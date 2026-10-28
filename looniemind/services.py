"""Casos de uso financeiros e de manutenção, independentes da interface HTTP."""
from collections import defaultdict
from datetime import date, timedelta
import io
import json
import random
import sqlite3
import zipfile


from .db import now
from .domain import DETAIL_FIELDS, DomainError, movement_details


def transaction_dict(row):
    item = dict(row)
    item.pop("original", None)
    if item.get("sugestao"):
        item["sugestao"] = json.loads(item["sugestao"])
    return item


class FinanceService:
    def __init__(self, db, models, forecasts):
        self.db, self.models, self.forecasts = db, models, forecasts

    def create_company(self, name, description, balance, balance_date, demo=False):
        with self.db.connect(write=True) as conn:
            cursor = conn.execute("""INSERT INTO Empresas(nome,descricao,saldo_inicial_centavos,data_saldo,demo,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?)""", (name, description, balance, balance_date, int(demo), now(), now()))
            company_id = cursor.lastrowid
            self.db.add_defaults(conn, company_id)
            self.db.audit(conn, company_id, "criar_empresa", "empresa", company_id, {"demo": demo})
            return self.db.company(conn, company_id)

    def update_company(self, company_id, fields):
        with self.db.connect(write=True) as conn:
            self.db.company(conn, company_id)
            allowed = {k: v for k, v in fields.items() if k in {"nome", "descricao", "saldo_inicial_centavos", "data_saldo"}}
            if allowed:
                conn.execute("UPDATE Empresas SET " + ",".join(f"{key}=?" for key in allowed) + " WHERE id_empresa=?",
                             (*allowed.values(), company_id))
                self.db.touch(conn, company_id)
                self.db.audit(conn, company_id, "alterar_empresa", "empresa", company_id, allowed)
            return self.db.company(conn, company_id)

    def _where(self, company_id, filters=None):
        filters = filters or {}
        where, args = ["id_empresa=?"], [company_id]
        for key, operation in [("inicio", "data>=?"), ("fim", "data<=?"), ("tipo", "tipo=?"), ("categoria", "categoria=?")]:
            if filters.get(key) is not None and filters.get(key) != "":
                where.append(operation)
                args.append(filters[key])
        if filters.get("busca"):
            where.append("(descricao LIKE ? ESCAPE '\\' OR categoria LIKE ? ESCAPE '\\' OR contraparte LIKE ? ESCAPE '\\' OR documento LIKE ? ESCAPE '\\' OR centro_custo LIKE ? ESCAPE '\\')")
            term = str(filters["busca"]).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            args.extend([f"%{term}%"] * 5)
        if filters.get("pendentes"):
            where.append("revisado=0")
        return " AND ".join(where), args

    def transactions(self, company_id, filters=None, page=1, page_size=20, all_rows=False):
        where, args = self._where(company_id, filters)
        with self.db.connect() as conn:
            self.db.company(conn, company_id)
            count = conn.execute(f"SELECT count(*) FROM Lancamentos WHERE {where}", args).fetchone()[0]
            totals = conn.execute(f"""SELECT COALESCE(SUM(CASE WHEN tipo=1 THEN valor_centavos ELSE 0 END),0),
                COALESCE(SUM(CASE WHEN tipo=2 THEN valor_centavos ELSE 0 END),0),
                SUM(CASE WHEN tipo IS NULL THEN 1 ELSE 0 END) FROM Lancamentos WHERE {where}""", args).fetchone()
            query = f"SELECT * FROM Lancamentos WHERE {where} ORDER BY data DESC,id_lancamento DESC"
            rows = conn.execute(query if all_rows else query + " LIMIT ? OFFSET ?",
                                args if all_rows else [*args, page_size, (page - 1) * page_size]).fetchall()
            return {"itens": [transaction_dict(r) for r in rows], "total": count, "pagina": page,
                    "por_pagina": page_size, "receitas_centavos": totals[0], "despesas_centavos": totals[1],
                    "sem_tipo": totals[2] or 0}

    def save_transaction(self, company_id, fields, transaction_id=None):
        with self.db.connect(write=True) as conn:
            self.db.company(conn, company_id)
            if fields["categoria"] == "Sem categoria":
                raise DomainError("Escolha uma categoria antes de confirmar o lançamento.")
            timestamp = now()
            values = (fields["descricao"], fields["categoria"], fields["valor_centavos"], fields["data"], fields["tipo"])
            if transaction_id:
                previous = conn.execute("SELECT * FROM Lancamentos WHERE id_empresa=? AND id_lancamento=?",
                                        (company_id, transaction_id)).fetchone()
                if not previous:
                    raise DomainError("Lançamento não encontrado nesta empresa.", 404)
                conn.execute("""UPDATE Lancamentos SET descricao=?,categoria=?,valor_centavos=?,data=?,tipo=?,
                    revisado=1,origem='revisao_manual',sugestao=NULL,updated_at=? WHERE id_empresa=? AND id_lancamento=?""",
                    (*values, timestamp, company_id, transaction_id))
                action = "corrigir_lancamento"
            else:
                cursor = conn.execute("""INSERT INTO Lancamentos(descricao,categoria,valor_centavos,data,tipo,
                    id_empresa,revisado,origem,created_at,updated_at) VALUES(?,?,?,?,?,?,1,'manual',?,?)""",
                    (*values, company_id, timestamp, timestamp))
                transaction_id, action = cursor.lastrowid, "criar_lancamento"
                previous = None
            try:
                details = movement_details({field: fields.get(field, previous[field] if previous else "") for field in DETAIL_FIELDS})
            except ValueError as exc:
                raise DomainError(str(exc)) from exc
            conn.execute("UPDATE Lancamentos SET " + ",".join(f"{field}=?" for field in DETAIL_FIELDS) + " WHERE id_lancamento=?",
                         (*details.values(), transaction_id))
            conn.execute("INSERT OR IGNORE INTO Categorias(id_empresa,nome,tipo) VALUES(?,?,?)",
                         (company_id, fields["categoria"], fields["tipo"]))
            self.db.touch(conn, company_id)
            self.db.audit(conn, company_id, action, "lancamento", transaction_id,
                          {"antes": transaction_dict(previous) if previous else None, "depois": fields})
            return transaction_dict(conn.execute("SELECT * FROM Lancamentos WHERE id_lancamento=?", (transaction_id,)).fetchone())

    def delete_transaction(self, company_id, transaction_id):
        with self.db.connect(write=True) as conn:
            row = conn.execute("SELECT * FROM Lancamentos WHERE id_empresa=? AND id_lancamento=?",
                               (company_id, transaction_id)).fetchone()
            if not row:
                raise DomainError("Lançamento não encontrado nesta empresa.", 404)
            conn.execute("DELETE FROM Lancamentos WHERE id_lancamento=?", (transaction_id,))
            self.db.touch(conn, company_id)
            self.db.audit(conn, company_id, "excluir_lancamento", "lancamento", transaction_id, transaction_dict(row))
            return {"excluido": True}

    def classify(self, company_id):
        with self.db.connect() as conn:
            self.db.company(conn, company_id)
            records = [dict(r) for r in conn.execute("SELECT * FROM Lancamentos WHERE id_empresa=? AND revisado=0", (company_id,))]
        predictions = self.models.predict(company_id, records)
        count = 0
        with self.db.connect(write=True) as conn:
            for row, suggestion in zip(records, predictions):
                if suggestion:
                    # A cláusula de revisão e o timestamp preservam alterações concorrentes.
                    count += conn.execute("UPDATE Lancamentos SET sugestao=? WHERE id_lancamento=? AND id_empresa=? AND revisado=0 AND updated_at=?",
                        (json.dumps(suggestion, ensure_ascii=False), row["id_lancamento"], company_id, row["updated_at"])).rowcount
            self.db.audit(conn, company_id, "sugerir_classificacao", "modelo", company_id, {"sugestoes": count})
        return {"sugestoes": count, "pendentes": len(records), "modelo": self.models.status(company_id)}

    def accept_suggestions(self, company_id, identifiers):
        accepted = 0
        with self.db.connect(write=True) as conn:
            self.db.company(conn, company_id)
            for identifier in set(identifiers):
                row = conn.execute("SELECT * FROM Lancamentos WHERE id_empresa=? AND id_lancamento=?",
                                   (company_id, identifier)).fetchone()
                if not row or row["revisado"] or not row["sugestao"]:
                    continue
                suggestion = json.loads(row["sugestao"])
                kind = row["tipo"] or suggestion["tipo"]
                conn.execute("UPDATE Lancamentos SET categoria=?,tipo=?,revisado=1,origem='sugestao_confirmada',updated_at=? WHERE id_lancamento=?",
                             (suggestion["categoria"], kind, now(), identifier))
                conn.execute("INSERT OR IGNORE INTO Categorias(id_empresa,nome,tipo) VALUES(?,?,?)",
                             (company_id, suggestion["categoria"], kind))
                self.db.audit(conn, company_id, "aceitar_sugestao", "lancamento", identifier, suggestion)
                accepted += 1
            if accepted:
                self.db.touch(conn, company_id)
        return {"confirmados": accepted}

    def summary(self, company_id, period="month"):
        today = date.today()
        start = {"month": today.replace(day=1), "30d": today - timedelta(days=29),
                 "90d": today - timedelta(days=89), "year": today.replace(month=1, day=1),
                 "all": date(1900, 1, 1)}[period]
        span = (today - start).days + 1
        previous_start, previous_end = start - timedelta(days=span), start - timedelta(days=1)
        with self.db.connect() as conn:
            company = self.db.company(conn, company_id)
            rows = [dict(r) for r in conn.execute("SELECT * FROM Lancamentos WHERE id_empresa=? AND data<=?", (company_id, today.isoformat()))]
        current = [r for r in rows if r["data"] >= start.isoformat()]
        previous = [r for r in rows if previous_start.isoformat() <= r["data"] <= previous_end.isoformat()]
        def total(data, kind):
            return sum(r["valor_centavos"] for r in data if r["tipo"] == kind)
        income, expense = total(current, 1), total(current, 2)
        balance_rows = [r for r in rows if r["data"] >= company["data_saldo"]]
        balance = company["saldo_inicial_centavos"] + total(balance_rows, 1) - total(balance_rows, 2)
        chart_start = max(start, date.fromisoformat(company["data_saldo"]), today - timedelta(days=365))
        daily = defaultdict(lambda: {1: 0, 2: 0})
        running = company["saldo_inicial_centavos"]
        for row in balance_rows:
            if row["tipo"]:
                if row["data"] < chart_start.isoformat():
                    running += row["valor_centavos"] * (1 if row["tipo"] == 1 else -1)
                else:
                    daily[row["data"]][row["tipo"]] += row["valor_centavos"]
        opening = running
        daily_series = []
        for offset in range(max(0, (today-chart_start).days+1)):
            day = (chart_start+timedelta(days=offset)).isoformat()
            running += daily[day][1] - daily[day][2]
            daily_series.append({"data": day, "receitas_centavos": daily[day][1],
                                 "despesas_centavos": daily[day][2], "saldo_centavos": running})
        pending = sum(not r["revisado"] for r in rows)
        unknown = sum(r["tipo"] is None for r in rows)
        categories = defaultdict(int)
        for row in current:
            if row["tipo"] == 2:
                categories[row["categoria"]] += row["valor_centavos"]
        category_series = [{"categoria": name, "valor_centavos": value,
                            "percentual": round(value / expense * 100, 1) if expense else 0}
                           for name, value in sorted(categories.items(), key=lambda x: -x[1])]
        month_end = today.year * 12 + today.month - 1
        months = []
        for index in range(month_end - 5, month_end + 1):
            year, month = divmod(index, 12)
            prefix = f"{year:04d}-{month+1:02d}"
            monthly = [r for r in rows if r["data"].startswith(prefix)]
            months.append({"mes": prefix, "receitas_centavos": total(monthly, 1), "despesas_centavos": total(monthly, 2)})
        forecast = self.forecasts.calculate(company_id, 30)
        alerts = []
        if balance < 0:
            alerts.append({"nivel": "danger", "titulo": "Saldo atual negativo", "descricao": "As saídas realizadas superam o saldo disponível. Confira os lançamentos e o saldo de referência.",
                           "data": today.isoformat(), "valor_centavos": balance, "destino": "transactions"})
        if balance >= 0 and forecast["disponivel"] and forecast["menor_saldo_centavos"] < 0:
            first_negative = next(r for r in forecast["serie"] if r["saldo_centavos"] < 0)
            alerts.append({"nivel": "danger", "titulo": "Possível saldo negativo", "descricao": "As saídas estimadas superam o caixa disponível. Revise o planejamento.",
                           "data": first_negative["data"], "valor_centavos": first_negative["saldo_centavos"], "destino": "forecast"})
        if pending:
            alerts.append({"nivel": "warning", "titulo": "Lançamentos para revisar", "descricao": f"{pending} movimentações aguardam confirmação da categoria ou do tipo.",
                           "quantidade": pending, "destino": "classification"})
        if category_series and category_series[0]["percentual"] >= 40:
            top = category_series[0]
            alerts.append({"nivel": "info", "titulo": "Despesas concentradas", "descricao": f"{top['categoria']} representa {top['percentual']:.0f}% das saídas no período.",
                           "valor_centavos": top["valor_centavos"], "destino": "transactions"})
        if not forecast["disponivel"]:
            alerts.append({"nivel": "info", "titulo": "Complete seu histórico", "descricao": forecast["motivo"], "destino": "import"})
        if not alerts:
            alerts.append({"nivel": "success", "titulo": "Revisões em dia", "descricao": "Não há pendências de classificação. Acompanhe a projeção regularmente.", "destino": "forecast"})
        last_30_expense = total([r for r in rows if r["data"] >= (today - timedelta(days=29)).isoformat()], 2)
        def variation(value, old):
            return round((value - old) / old * 100, 1) if old else None
        return {"empresa": company, "periodo": {"codigo": period, "inicio": start.isoformat(), "fim": today.isoformat()},
                "saldo_centavos": balance, "receitas_centavos": income, "despesas_centavos": expense,
                "resultado_centavos": income - expense, "variacao_receitas": variation(income, total(previous, 1)),
                "variacao_despesas": variation(expense, total(previous, 2)), "pendentes": pending, "sem_tipo": unknown,
                "total_lancamentos": len(rows), "lancamentos_periodo": len(current), "categorias": category_series,
                "fluxo_diario": daily_series, "saldo_abertura_grafico_centavos": opening,
                "qualidade": {"revisados": len(rows)-pending, "pendentes": pending,
                    "sem_tipo_centavos": sum(r["valor_centavos"] for r in rows if r["tipo"] is None),
                    "ultima_movimentacao": max((r["data"] for r in rows), default=None)},
                "fluxo_mensal": months, "ultimos": [transaction_dict(r) for r in sorted(current, key=lambda r: (r["data"], r["id_lancamento"]), reverse=True)[:5]],
                "previsao": forecast, "alertas": alerts,
                "dias_cobertura": max(0, round(balance / (last_30_expense / 30))) if last_30_expense else None}

    def export(self, company_id, filters=None, file_format="csv"):
        from .workbooks import finance_report, report_csv
        records = self.transactions(company_id, filters, all_rows=True)["itens"]
        if file_format == "csv":
            return report_csv(records)
        summary = self.summary(company_id, "all")
        return finance_report(records, summary["empresa"], filters, summary["saldo_centavos"])

    def backup(self):
        buffer = io.BytesIO()
        with self.db.connect(write=True) as conn:
            snapshot = sqlite3.connect(":memory:")
            # A conexão de leitura separada evita fazer backup da própria transação de escrita.
            source = sqlite3.connect(self.db.path)
            try:
                source.backup(snapshot)
                content = snapshot.serialize()
                files = [dict(r) for r in conn.execute("SELECT file_url FROM Planilhas")]
            finally:
                source.close()
                snapshot.close()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("looniemind.sqlite3", content)
            archive.writestr("manifest.json", json.dumps({"versao": 2, "criado_em": now(),
                "nota": "Inclui banco e arquivos originais. Modelos devem ser treinados novamente após restaurar."}, ensure_ascii=False))
            for record in files:
                path = (self.db.directory / record["file_url"]).resolve()
                if path.is_relative_to(self.db.directory / "uploads") and path.is_file():
                    archive.write(path, record["file_url"])
        return buffer.getvalue()

    def seed_demo(self):
        with self.db.connect() as conn:
            existing = conn.execute("SELECT id_empresa FROM Empresas WHERE demo=1 ORDER BY id_empresa LIMIT 1").fetchone()
        if existing:
            return {"empresa": self.get_company(existing[0]), "existente": True}
        today, rng = date.today(), random.Random(2026)
        start = today - timedelta(days=209)
        company = self.create_company("Estúdio Aurora", "Empresa fictícia · comércio e serviços criativos", 2_450_000, start.isoformat(), True)
        company_id, timestamp = company["id_empresa"], now()
        records = []
        for offset in range(210):
            day = start + timedelta(days=offset)
            weekend = day.weekday() >= 5
            for j in range(2 if weekend else 3):
                income = rng.randint(24_000, 62_000) * (1.1 if day.weekday() == 4 else 1)
                category = "Serviços" if j == 2 else "Vendas"
                description = ("Serviço de criação · Cliente " if j == 2 else "Venda de produtos · Pedido ") + str(1000 + offset * 3 + j)
                records.append((day, 1, category, int(income), description))
            if day.weekday() in (0, 2, 4):
                records.append((day, 2, "Fornecedores", rng.randint(30_000, 65_000), "Compra de insumos · Papelaria Horizonte"))
            if day.day == 5:
                records.extend([(day, 2, "Aluguel", 380_000, "Aluguel do espaço · Unidade Centro"),
                                (day, 2, "Pessoal", 1_250_000, "Folha de pagamento · Equipe Aurora")])
            if day.day == 20:
                records.append((day, 2, "Impostos", 280_000 + rng.randint(0, 80_000), "Guia DAS · Simples Nacional"))
            if day.day == 15:
                records.append((day, 2, "Utilidades", 92_000, "Energia e internet · Escritório"))
            if day.weekday() == 1:
                records.append((day, 2, "Marketing", rng.randint(25_000, 42_000), "Campanha de marketing · Redes sociais"))
            if day.weekday() == 3:
                records.extend([(day, 2, "Logística", rng.randint(9_000, 20_000), "Frete de entrega · Pedidos da semana"),
                                (day, 2, "Alimentação", rng.randint(12_000, 24_000), "Almoço da equipe · Restaurante Jardim")])
        with self.db.connect(write=True) as conn:
            for idx, (day, kind, category, amount, description) in enumerate(records):
                pending = idx > len(records) - 35 and idx % 3 == 0
                conn.execute("""INSERT INTO Lancamentos(id_empresa,descricao,categoria,valor_centavos,data,tipo,revisado,
                    origem,created_at,updated_at) VALUES(?,?,?,?,?,?,?,'demonstracao',?,?)""",
                    (company_id, description, "Sem categoria" if pending else category, amount, day.isoformat(), kind,
                     int(not pending), timestamp, timestamp))
            self.db.touch(conn, company_id)
            self.db.audit(conn, company_id, "carregar_demonstracao", "empresa", company_id, {"sintetico": True, "registros": len(records)})
        model = self.models.train(company_id, "synthetic")
        self.classify(company_id)
        return {"empresa": self.get_company(company_id), "lancamentos": len(records), "modelo": model, "existente": False}

    def get_company(self, company_id):
        with self.db.connect() as conn:
            return self.db.company(conn, company_id)

    def seed_expanded_demo(self):
        from .synthetic import SCENARIOS, financial_history
        companies = []
        for scenario in SCENARIOS:
            marker = f"Base sintética v2 · {scenario['id']}"
            with self.db.connect() as conn:
                existing = conn.execute("SELECT id_empresa FROM Empresas WHERE demo=1 AND descricao=?", (marker,)).fetchone()
            if existing:
                companies.append({"empresa": self.get_company(existing[0]), "existente": True})
                continue
            rows = financial_history(scenario)
            company = self.create_company(scenario["nome"], marker, scenario["saldo"], rows[0]["data"], True)
            identifier, timestamp = company["id_empresa"], now()
            with self.db.connect(write=True) as conn:
                for index, row in enumerate(rows):
                    pending = index >= len(rows)-50 and index % 4 == 0
                    fields = ["id_empresa", "descricao", "categoria", "valor_centavos", "data", "tipo", "revisado",
                              "origem", "created_at", "updated_at", *DETAIL_FIELDS]
                    values = [identifier, row["descricao"], "Sem categoria" if pending else row["categoria"],
                              row["valor_centavos"], row["data"], row["tipo"], int(not pending), "demonstracao",
                              timestamp, timestamp, *(row[f] for f in DETAIL_FIELDS)]
                    conn.execute(f"INSERT INTO Lancamentos({','.join(fields)}) VALUES({','.join('?' for _ in fields)})", values)
                self.db.touch(conn, identifier)
                self.db.audit(conn, identifier, "carregar_base_ampliada", "empresa", identifier,
                              {"sintetico": True, "registros": len(rows), "dias": 1095})
            companies.append({"empresa": self.get_company(identifier), "lancamentos": len(rows), "existente": False})
        return {"empresas": companies, "sintetico": True}
