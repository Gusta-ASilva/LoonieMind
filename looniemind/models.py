"""Treino supervisionado e previsão com validação temporal, executados localmente."""
from collections import defaultdict
from datetime import date, timedelta
import hashlib
import importlib.metadata
import json
import math
import random
import re
import threading

import joblib
from lightgbm import LGBMClassifier, LGBMRegressor
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, f1_score
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import LabelEncoder

from .db import now
from .domain import DomainError, normalized

TRAINING_TOPICS = [
    (1, "Vendas", ["venda de produtos", "recebimento de venda", "pedido na loja", "vendas no balcão", "venda pelo site", "venda mercadorias", "recebimento cartão de vendas", "pix cliente compra", "venda varejo", "receita de produtos", "pedido de mercadoria", "pagamento compra cliente"]),
    (1, "Serviços", ["serviço prestado", "honorários de consultoria", "serviço de manutenção", "consultoria recebida", "atendimento técnico", "projeto entregue", "contrato de serviço", "recebimento assessoria", "serviço de instalação", "mensalidade de serviço", "prestação de serviços", "suporte contratado"]),
    (1, "Outras receitas", ["rendimento aplicação", "juros recebidos", "receita financeira", "rendimento bancário", "rendimento investimento", "bonificação recebida", "receita extraordinária", "juros de aplicação", "rendimentos de poupança", "bonificação financeira", "reembolso recebido", "receita eventual"]),
    (2, "Fornecedores", ["compra de matéria prima", "pagamento fornecedor", "compra de mercadorias", "embalagens para produtos", "aquisição de insumos", "reposição de estoque", "pedido ao fornecedor", "compra de ingredientes", "insumos de produção", "fornecedor de embalagens", "matéria prima fábrica", "compra para estoque"]),
    (2, "Aluguel", ["aluguel do imóvel", "locação comercial", "aluguel da loja", "locação do escritório", "aluguel mensal", "locação do galpão", "aluguel da sala", "aluguel do ponto", "contrato de locação", "pagamento imobiliária", "locação de espaço", "aluguel comercial"]),
    (2, "Pessoal", ["folha de pagamento", "salário funcionário", "pagamento salários", "férias de funcionário", "vale transporte equipe", "benefício funcionário", "adiantamento salarial", "salários da equipe", "décimo terceiro", "folha mensal", "remuneração funcionário", "pró labore sócio"]),
    (2, "Impostos", ["pagamento de imposto", "guia DAS simples nacional", "tributos municipais", "pagamento de ISS", "guia de ICMS", "imposto federal", "taxa municipal", "guia tributária", "recolhimento INSS", "pagamento de DARF", "imposto simples nacional", "tributação mensal"]),
    (2, "Marketing", ["anúncio publicitário", "campanha de marketing", "publicidade digital", "anúncios google ads", "impulsionamento instagram", "campanha de divulgação", "agência de publicidade", "anúncio redes sociais", "marketing da loja", "material publicitário", "campanha patrocinada", "publicidade no facebook"]),
    (2, "Logística", ["frete de entrega", "transporte de mercadoria", "serviço de motoboy", "combustível entregas", "envio pelos correios", "frete transportadora", "logística de entrega", "combustível veículo", "entrega ao cliente", "custo de transporte", "serviço de frete", "postagem de encomenda"]),
    (2, "Alimentação", ["almoço da equipe", "refeição de trabalho", "café para funcionários", "lanche da equipe", "vale refeição", "almoço comercial", "alimentação funcionários", "refeição no restaurante", "café da manhã equipe", "compra de alimentos", "lanche de trabalho", "despesa de alimentação"]),
    (2, "Utilidades", ["conta de energia", "fatura de internet", "conta de água", "telefonia comercial", "energia elétrica", "serviço de internet", "conta de telefone", "água e esgoto", "consumo de luz", "fatura telefonia", "serviço de água", "internet do escritório"]),
    (2, "Outras despesas", ["tarifa bancária", "mensalidade de software", "material de escritório", "taxa da conta", "licença de sistema", "papelaria do escritório", "assinatura de software", "tarifa de manutenção", "compra de papel", "licenciamento de programa", "despesa administrativa", "material de limpeza"]),
]


def synthetic_training():
    from .synthetic import classification_data
    return classification_data(TRAINING_TOPICS)


class ModelService:
    def __init__(self, db):
        self.db = db
        self.lock = threading.RLock()
        self.cache = {}

    def paths(self, company_id):
        base = self.db.directory / "models" / f"classifier-{int(company_id)}"
        return base.with_suffix(".joblib"), base.with_suffix(".json")

    def status(self, company_id):
        path, metadata_path = self.paths(company_id)
        if not path.is_file() or not metadata_path.is_file():
            return {"disponivel": False, "metodo": "regras", "mensagem": "Modelo ainda não treinado. Sugestões por palavras-chave disponíveis."}
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"disponivel": False, "metodo": "regras", "mensagem": "Metadados indisponíveis. Treine o modelo novamente."}
        metrics = metadata.get("metricas", {})
        if metrics.get("validacao") and metadata.get("exemplos"):
            metrics["separacao"] = "famílias de descrição disjuntas por classe; consulte as contagens efetivas de cada partição"
            metrics["proporcoes"] = {key: round(metrics[key]/metadata["exemplos"], 4) for key in ("treino", "validacao", "teste")}
        return {"disponivel": True, **metadata}

    def train(self, company_id, source="reviewed", external_records=None):
        with self.db.connect() as conn:
            company = self.db.company(conn, company_id)
            if external_records is not None:
                records = external_records
                source = "arquivo_rotulado"
            elif source == "synthetic":
                records = synthetic_training()
            else:
                records = [dict(r) for r in conn.execute("""SELECT descricao,tipo,categoria FROM Lancamentos
                    WHERE id_empresa=? AND revisado=1 AND tipo IS NOT NULL AND categoria!='Sem categoria'""", (company_id,))]
        if len(records) < 24:
            raise DomainError("São necessários pelo menos 24 exemplos revisados, com 4 descrições distintas por categoria.")
        by_label = defaultdict(lambda: defaultdict(list))
        for row in records:
            label = f"{int(row['tipo'])}|{row['categoria']}"
            group = row.get("grupo") or re.sub(r"\d+", "#", normalized(row["descricao"]))
            by_label[label][group].append(row)
        if len(by_label) < 2 or any(len(groups) < 4 for groups in by_label.values()):
            raise DomainError("Use pelo menos duas classes e quatro descrições distintas por combinação de tipo/categoria.")
        train, validation, test = [], [], []
        split_groups = {"treino": set(), "validacao": set(), "teste": set()}
        rng = random.Random(42)
        for groups in by_label.values():
            keys = sorted(groups)
            rng.shuffle(keys)
            count = max(1, math.floor(len(keys) * .2))
            held_out, validation_groups = set(keys[:count]), set(keys[count:count*2])
            for group, rows in groups.items():
                split = "teste" if group in held_out else "validacao" if group in validation_groups else "treino"
                split_groups[split].add(f"{rows[0]['tipo']}|{rows[0]['categoria']}|{group}")
                {"treino": train, "validacao": validation, "teste": test}[split].extend(rows)
        def labels(rows):
            return [f"{int(r['tipo'])}|{r['categoria']}" for r in rows]
        encoder = LabelEncoder().fit(labels(records))
        vectorizer = FeatureUnion([
            ("palavras", TfidfVectorizer(strip_accents="unicode", ngram_range=(1, 2), max_features=12_000, sublinear_tf=True)),
            ("caracteres", TfidfVectorizer(strip_accents="unicode", analyzer="char_wb", ngram_range=(3, 5),
                                          max_features=16_000, min_df=2, sublinear_tf=True))])
        x_train = vectorizer.fit_transform([r["descricao"] for r in train])
        x_test = vectorizer.transform([r["descricao"] for r in test])
        model = LGBMClassifier(n_estimators=90, num_leaves=15, max_depth=5, min_child_samples=5,
                               learning_rate=.1, n_jobs=2, random_state=42, verbosity=-1,
                               force_col_wise=True, deterministic=True, class_weight="balanced")
        model.fit(x_train, encoder.transform(labels(train)))
        validation_score = f1_score(encoder.transform(labels(validation)),
            model.predict(vectorizer.transform([r["descricao"] for r in validation])), average="macro", zero_division=0)
        y_test, predicted = encoder.transform(labels(test)), model.predict(x_test)
        metrics = {"f1_macro": round(float(f1_score(y_test, predicted, average="macro", zero_division=0)), 4),
                   "por_classe": classification_report(y_test, predicted, labels=list(range(len(encoder.classes_))),
                       target_names=list(encoder.classes_), output_dict=True, zero_division=0),
                   "f1_macro_validacao": round(float(validation_score), 4),
                   "treino": len(train), "validacao": len(validation), "teste": len(test),
                   "grupos": {name: len(groups) for name, groups in split_groups.items()},
                   "separacao": "famílias de descrição disjuntas por classe; consulte as contagens efetivas de cada partição",
                   "proporcoes": {"treino": round(len(train)/len(records),4), "validacao": round(len(validation)/len(records),4), "teste": round(len(test)/len(records),4)},
                   "seed": 42}
        # Após avaliar o holdout, o artefato de uso é reajustado sobre a base disponível.
        full_x = vectorizer.fit_transform([r["descricao"] for r in records])
        model.fit(full_x, encoder.transform(labels(records)))
        dataset_hash = hashlib.sha256(json.dumps(records, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        libraries = {name: importlib.metadata.version(name) for name in ["scikit-learn", "lightgbm", "numpy", "joblib"]}
        signature = {"dados": dataset_hash, "parametros": model.get_params(), "pipeline": "word-char-tfidf-v2", "bibliotecas": libraries}
        model_hash = hashlib.sha256(json.dumps(signature, sort_keys=True, default=str).encode()).hexdigest()
        is_synthetic = bool(company["demo"]) or source == "synthetic" or bool(records) and all(r.get("fonte") == "sintetica" for r in records)
        metadata = {"metodo": "TF-IDF (palavras e caracteres) + LightGBM", "fonte": source, "sintetico": is_synthetic,
                    "versao": model_hash[:12], "dados_sha256": dataset_hash, "treinado_em": now(), "exemplos": len(records),
                    "bibliotecas": libraries,
                    "classes": len(encoder.classes_), "metricas": metrics,
                    "aviso": "Avaliação em dados sintéticos; não demonstra qualidade em dados reais." if is_synthetic else "Avaliação interna da base revisada; valide antes de ampliar o uso."}
        artifact = {"vectorizer": vectorizer, "model": model, "labels": list(encoder.classes_), "metadata": metadata}
        path, meta_path = self.paths(company_id)
        with self.lock:
            temporary = path.with_suffix(".tmp")
            joblib.dump(artifact, temporary)
            temporary.replace(path)
            meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            self.cache.pop(company_id, None)
        with self.db.connect(write=True) as conn:
            conn.execute("UPDATE Lancamentos SET sugestao=NULL WHERE id_empresa=? AND revisado=0", (company_id,))
            self.db.audit(conn, company_id, "treinar_modelo", "modelo", metadata["versao"], {"fonte": source, "exemplos": len(records)})
        return {"disponivel": True, **metadata}

    def predict(self, company_id, records):
        if not records:
            return []
        path, _ = self.paths(company_id)
        artifact = None
        if path.is_file():
            with self.lock:
                stamp = path.stat().st_mtime_ns
                cached = self.cache.get(company_id)
                if not cached or cached[0] != stamp:
                    try:
                        cached = (stamp, joblib.load(path))
                        self.cache[company_id] = cached
                    except Exception:
                        cached = None
                artifact = cached[1] if cached else None
        if artifact:
            matrix = artifact["vectorizer"].transform([row["descricao"] for row in records])
            probabilities = artifact["model"].predict_proba(matrix)
            output = []
            for row, scores in zip(records, probabilities):
                candidates = [(float(score), label) for score, label in zip(scores, artifact["labels"])
                              if not row.get("tipo") or int(label.split("|", 1)[0]) == row["tipo"]]
                if not candidates:
                    output.append(None)
                    continue
                score, label = max(candidates)
                kind, category = label.split("|", 1)
                # Texto completamente fora do vocabulário não recebe uma falsa sugestão de IA.
                if matrix[len(output)].nnz == 0:
                    output.append(None)
                    continue
                output.append({"tipo": int(kind), "categoria": category, "score": round(score, 4),
                               "metodo": "modelo", "versao": artifact["metadata"]["versao"],
                               "sintetico": artifact["metadata"]["sintetico"]})
            return output
        rules = {"venda": (1, "Vendas"), "servico": (1, "Serviços"), "rendimento": (1, "Outras receitas"),
                 "fornecedor": (2, "Fornecedores"), "aluguel": (2, "Aluguel"), "salario": (2, "Pessoal"),
                 "imposto": (2, "Impostos"), "marketing": (2, "Marketing"), "frete": (2, "Logística"),
                 "almoco": (2, "Alimentação"), "energia": (2, "Utilidades"), "tarifa": (2, "Outras despesas")}
        output = []
        for row in records:
            candidate = next(((kind, category) for word, (kind, category) in rules.items()
                              if word in normalized(row["descricao"]) and (not row.get("tipo") or row["tipo"] == kind)), None)
            output.append({"tipo": candidate[0], "categoria": candidate[1], "score": None,
                           "metodo": "regra", "versao": "aliases-v1", "sintetico": False} if candidate else None)
        return output


def temporal_features(values, day):
    previous = list(values)
    return [day.weekday(), day.day, day.month, math.sin(2 * math.pi * day.weekday() / 7),
            previous[-1], previous[-7], previous[-14], previous[-28],
            float(np.mean(previous[-7:])), float(np.mean(previous[-28:]))]


def recursive_predictions(model, history, start, horizon):
    values, results = list(history), []
    for step in range(horizon):
        day = start + timedelta(days=step)
        if model is None:
            value = values[-7]
        else:
            value = float(model.booster_.predict(np.array([temporal_features(values, day)]), num_threads=2)[0])
        value = max(0, int(round(value)))
        results.append(value)
        values.append(value)
    return results


class ForecastService:
    def __init__(self, db):
        self.db = db
        self.cache = {}
        self.lock = threading.RLock()

    def calculate(self, company_id, horizon=30):
        with self.db.connect() as conn:
            company = self.db.company(conn, company_id)
            rows = [dict(r) for r in conn.execute("""SELECT data,tipo,SUM(valor_centavos) AS total FROM Lancamentos
                WHERE id_empresa=? AND tipo IS NOT NULL AND data<=? AND data>=? GROUP BY data,tipo ORDER BY data""",
                (company_id, date.today().isoformat(), company["data_saldo"]))]
            unknown = conn.execute("SELECT count(*) FROM Lancamentos WHERE id_empresa=? AND tipo IS NULL", (company_id,)).fetchone()[0]
        key = (company_id, company["revisao"], horizon, date.today().isoformat())
        with self.lock:
            if key in self.cache:
                return self.cache[key]
        empty = {"disponivel": False, "dias": horizon, "serie": [], "metodo": "indisponível", "pendentes_sem_tipo": unknown}
        if not rows:
            return {**empty, "motivo": "Importe movimentações realizadas para construir o histórico financeiro."}
        first, last = date.fromisoformat(rows[0]["data"]), date.fromisoformat(rows[-1]["data"])
        if (date.today() - last).days > 7:
            return {**empty, "motivo": "Histórico desatualizado: a última movimentação tem mais de 7 dias. Importe dados recentes.", "ultima_data": last.isoformat()}
        start = max(first, date.today() - timedelta(days=1094))
        dates = pd.date_range(start, date.today(), freq="D")
        if len(dates) < 28:
            return {**empty, "motivo": "São necessários pelo menos 28 dias de histórico. Com 90 dias, o modelo LightGBM também é avaliado.", "dias_historico": len(dates)}
        lookup = {(r["data"], r["tipo"]): r["total"] for r in rows}
        predicted, evaluations, methods = {}, {}, []
        for kind, name in [(1, "receitas"), (2, "despesas")]:
            values = [lookup.get((day.date().isoformat(), kind), 0) for day in dates]
            chosen_model, evaluation = None, None
            method = "Referência sazonal (7 dias)"
            if len(values) >= 90 and sum(v > 0 for v in values) >= 20:
                holdout = min(21, max(14, len(values) // 5))
                cutoff = len(values) - holdout
                def train(end):
                    x = np.array([temporal_features(values[:i], dates[i].date()) for i in range(28, end)])
                    y = np.array(values[28:end])
                    regressor = LGBMRegressor(n_estimators=65, num_leaves=10, max_depth=4,
                        min_child_samples=7, learning_rate=.07, n_jobs=2, random_state=42, verbosity=-1,
                        deterministic=True, force_col_wise=True)
                    regressor.fit(x, y)
                    return regressor
                candidate = train(cutoff)
                model_values = recursive_predictions(candidate, values[:cutoff], dates[cutoff].date(), holdout)
                baseline_values = recursive_predictions(None, values[:cutoff], dates[cutoff].date(), holdout)
                actual = np.array(values[cutoff:])
                model_mae = float(np.mean(np.abs(actual - np.array(model_values))))
                baseline_mae = float(np.mean(np.abs(actual - np.array(baseline_values))))
                evaluation = {"mae_modelo_centavos": round(model_mae), "mae_referencia_centavos": round(baseline_mae),
                              "dias_teste": holdout, "inicio_teste": dates[cutoff].date().isoformat(),
                              "fim_teste": dates[-1].date().isoformat(), "validacao": "holdout cronológico com previsão recursiva"}
                if model_mae < baseline_mae:
                    chosen_model, method = train(len(values)), "LightGBM Regressor"
                denominator = int(actual.sum())
                best_mae = min(model_mae, baseline_mae)
                evaluation["wape"] = round(best_mae * holdout / denominator, 4) if denominator else None
            predicted[name] = recursive_predictions(chosen_model, values, date.today() + timedelta(days=1), horizon)
            evaluations[name] = {"metodo": method, "avaliacao": evaluation}
            methods.append(method)
        balance = company["saldo_inicial_centavos"] + sum(r["total"] * (1 if r["tipo"] == 1 else -1) for r in rows)
        current_balance = balance
        series = []
        for offset, (income, expense) in enumerate(zip(predicted["receitas"], predicted["despesas"]), start=1):
            balance += income - expense
            series.append({"data": (date.today() + timedelta(days=offset)).isoformat(), "receitas_centavos": income,
                           "despesas_centavos": expense, "saldo_centavos": balance})
        result = {"disponivel": True, "dias": horizon, "serie": series, "metodo": " + ".join(sorted(set(methods))),
                  "modelos": evaluations, "dias_historico": len(dates), "ultima_data": last.isoformat(),
                  "origem_previsao": date.today().isoformat(), "menor_saldo_centavos": min(r["saldo_centavos"] for r in series),
                  "saldo_final_centavos": balance, "pendentes_sem_tipo": unknown,
                  "saldo_atual_centavos": current_balance,
                  "aviso": "Estimativa, não garantia. Dias sem lançamentos no histórico são considerados sem movimentação. Confira se os arquivos cobrem todo o período.",
                  "sintetico": bool(company["demo"])}
        with self.lock:
            if len(self.cache) > 40:
                self.cache.clear()
            self.cache[key] = result
        return result
