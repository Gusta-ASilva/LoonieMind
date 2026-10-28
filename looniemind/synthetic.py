"""Dados fictícios reproduzíveis. Famílias de descrição permanecem juntas na avaliação."""
from collections import Counter
from datetime import date, timedelta
import csv
import hashlib
import io
import json
from pathlib import Path
import random
import zipfile

EXTRA_PHRASES = {
 "Vendas": ["liquidação das vendas na maquininha", "repasse de pedidos do comércio", "receita da loja virtual", "faturamento de mercadorias", "pagamento de pedido no varejo", "recebimento de compra no balcão", "venda em feira comercial", "comercialização de produto acabado", "venda de catálogo", "pedido de venda por encomenda", "venda de kit de produtos", "recebimento de mercadoria vendida"],
 "Serviços": ["receita de assistência técnica", "pagamento por assessoria", "recebimento de projeto contratado", "consultoria empresarial prestada", "receita de serviço recorrente", "atendimento de manutenção realizado", "serviço de configuração concluído", "receita de instalação técnica", "projeto de identidade visual entregue", "serviço de revisão contratado", "recebimento de suporte técnico", "mensalidade de assessoria recebida"],
 "Outras receitas": ["remuneração do saldo aplicado", "resgate do rendimento financeiro", "devolução de taxa cobrada", "estorno de cobrança bancária", "receita de incentivo comercial", "rendimento do fundo de reserva", "receita de bonificação anual", "restituição de tarifa", "retorno de aplicação financeira", "crédito de benefício recebido", "reembolso de despesa antecipada", "juros creditados na conta"],
 "Fornecedores": ["abastecimento de matéria prima", "aquisição de materiais produtivos", "reposição de mercadorias para revenda", "pagamento da distribuidora de insumos", "compra de materiais de produção", "compra de peças para fabricação", "reposição de embalagens", "fornecimento de componentes", "compra de estoque da loja", "compra de material para encomendas", "fornecimento de matéria prima industrial", "aquisição de itens para revenda"],
 "Aluguel": ["locação mensal do ponto comercial", "mensalidade do espaço locado", "pagamento do imóvel comercial", "aluguel da unidade de atendimento", "locação de sala de trabalho", "aluguel da sede administrativa", "pagamento de locação imobiliária", "aluguel de espaço de produção", "locação da loja do centro", "pagamento mensal ao locador", "aluguel do imóvel da empresa", "contraprestação de locação comercial"],
 "Pessoal": ["remuneração da equipe contratada", "pagamento de pró labore", "adiantamento da folha salarial", "vale alimentação dos colaboradores", "rescisão de funcionário", "bônus da equipe", "encargos da folha de salários", "benefícios dos empregados", "pagamento de horas extras", "remuneração de colaboradores", "férias e adicional de funcionário", "complemento de salário da equipe"],
 "Impostos": ["recolhimento de tributos estaduais", "quitação de guia fiscal", "arrecadação municipal de imposto", "pagamento de contribuição tributária", "guia do simples nacional", "recolhimento de imposto sobre serviços", "taxa de fiscalização municipal", "pagamento de obrigação fiscal", "recolhimento de tributos federais", "guia de contribuição previdenciária", "pagamento do imposto da empresa", "tributos sobre faturamento"],
 "Marketing": ["investimento em mídia patrocinada", "contratação de divulgação comercial", "campanha de anúncios digitais", "gestão de redes sociais", "criação de material de divulgação", "compra de espaço publicitário", "produção de campanha publicitária", "anúncio em plataforma de busca", "divulgação da marca em rede social", "serviço de agência de marketing", "publicação patrocinada da loja", "campanha de mídia online"],
 "Logística": ["transporte para entrega de pedidos", "envio de mercadorias pela transportadora", "abastecimento do veículo de entregas", "coleta de encomendas", "postagem de produtos vendidos", "remessa por serviço postal", "contratação de entrega expressa", "custo de distribuição dos pedidos", "pagamento ao entregador", "frete de mercadoria ao cliente", "deslocamento de carga", "logística de transporte comercial"],
 "Alimentação": ["refeição dos colaboradores", "compra de lanche para reunião", "almoço no horário de trabalho", "café da equipe na empresa", "alimentação da equipe em evento", "refeições para funcionários", "compra de café e lanches", "alimentação durante atendimento externo", "refeição de reunião comercial", "despesa de restaurante da equipe", "café para a reunião", "lanche durante o expediente"],
 "Utilidades": ["fornecimento de energia elétrica", "serviço de abastecimento de água", "plano de telefonia da empresa", "assinatura de conexão de internet", "consumo mensal de eletricidade", "fatura de água do imóvel", "conta de comunicação móvel", "serviço de banda larga", "fornecimento de água e esgoto", "conta de consumo de energia", "plano de internet comercial", "cobrança mensal de telefonia"],
 "Outras despesas": ["aquisição de material administrativo", "assinatura de sistema de gestão", "despesa de manutenção da conta", "compra de suprimentos de escritório", "licença de ferramenta digital", "compra de material de limpeza", "pagamento de tarifa de serviços bancários", "assinatura de aplicativo empresarial", "manutenção de equipamento de escritório", "compra de equipamento administrativo", "despesa com certificado digital", "compra de papel para impressão"],
}

SCENARIOS = [
 {"id": "aurora", "nome": "Aurora Comércio", "ramo": "Comércio de produtos e serviços", "saldo": 3_000_000, "escala": 1.0},
 {"id": "horizonte", "nome": "Horizonte Varejo", "ramo": "Varejo com pressão recente no caixa", "saldo": 2_000_000, "escala": .88},
 {"id": "studio", "nome": "Studio Soluções", "ramo": "Prestação de serviços com sazonalidade", "saldo": 2_500_000, "escala": 1.15},
]


def classification_data(topics, variants=50, seed=2702026):
    rng = random.Random(seed)
    rows = []
    for kind, category, phrases in topics:
        families = [*phrases, *EXTRA_PHRASES[category]]
        for family_index, phrase in enumerate(families):
            for variant in range(variants):
                vendor = f"{'Cliente' if kind == 1 else 'Fornecedor'} Modelo {rng.randint(1, 180):03d}"
                channel = rng.choice(["PIX", "transferência", "cartão", "boleto", "débito em conta"])
                text = rng.choice([f"{phrase} / {vendor}", f"{channel} {phrase} ref. {rng.randint(1000,99999)}",
                                   f"{phrase} - {channel} - unidade {rng.choice(['Centro','Norte','Sul'])}",
                                   f"{phrase} documento {rng.randint(10000,99999)} {vendor}"])
                if variant % 7 == 0:
                    text = text.upper()
                rows.append({"descricao": text, "tipo": kind, "categoria": category,
                             "grupo": f"{kind}-{category}-{family_index:02d}", "fonte": "sintetica",
                             "id_exemplo": f"CLS-{kind}-{family_index:02d}-{category}-{variant:03d}"})
    rng.shuffle(rows)
    return rows


def financial_history(scenario, end=None, days=1095, seed=2702026):
    end = end or date.today()
    start = end - timedelta(days=days - 1)
    rng = random.Random(seed + sum(map(ord, scenario["id"])))
    rows = []
    def add(day, kind, category, cents, description, center, counterpart):
        index = len(rows) + 1
        rows.append({"data": day.isoformat(), "descricao": description, "tipo": kind, "categoria": category,
            "valor_centavos": max(1, int(round(cents))), "documento": f"DOC-{scenario['id'].upper()}-{index:06d}",
            "contraparte": counterpart, "centro_custo": center,
            "conta": "Conta principal" if index % 4 else "Caixa da loja",
            "forma_pagamento": rng.choice(["PIX", "Transferência", "Cartão", "Boleto"]),
            "competencia": day.strftime("%Y-%m"), "observacoes": "Registro fictício para treinamento e demonstração",
            "id_externo": f"SYN-{scenario['id'].upper()}-{index:06d}", "cenario": scenario["id"], "fonte": "sintetica"})
    for offset in range(days):
        day = start + timedelta(days=offset)
        growth = .88 + .22 * offset / max(days - 1, 1)
        seasonal = 1.28 if day.month in (11, 12) else .9 if day.month in (1, 2) else 1.0
        pressure = .72 if scenario["id"] == "horizonte" and (end - day).days < 120 else 1.0
        multiplier = growth * seasonal * pressure * scenario["escala"]
        number = 2 if day.weekday() >= 5 else 3
        if scenario["id"] == "studio":
            number = 0 if day.weekday() >= 5 else 2
        for sale in range(number):
            service = scenario["id"] == "studio" or sale == 2
            amount = rng.randint(24_000, 48_000) * multiplier * (1.5 if service else 1)
            category = "Serviços" if service else "Vendas"
            add(day, 1, category, amount,
                ("Serviço de manutenção" if service else "Venda de produtos") + f" pedido {offset*4+sale+1000}",
                "Atendimento" if service else "Loja", f"Cliente Modelo {rng.randint(1,180):03d}")
        if day.weekday() in (0, 2, 4):
            add(day, 2, "Fornecedores", rng.randint(33_000, 58_000) * scenario["escala"],
                "Pagamento fornecedor de insumos", "Operação", f"Distribuidora Fictícia {rng.randint(1,30):02d}")
        if day.day == 5:
            add(day, 2, "Aluguel", 320_000 * scenario["escala"], "Aluguel do ponto comercial", "Administrativo", "Locadora Modelo")
            add(day, 2, "Pessoal", 900_000 * scenario["escala"] * (1.12 if offset > days*.7 else 1),
                "Folha de pagamento da equipe", "Administrativo", "Equipe fictícia")
        if day.day == 15:
            add(day, 2, "Utilidades", rng.randint(72_000, 100_000), "Conta de energia e internet", "Administrativo", "Concessionária Modelo")
        if day.day == 20:
            add(day, 2, "Impostos", 210_000 * multiplier, "Guia DAS simples nacional", "Administrativo", "Arrecadação fictícia")
        if day.weekday() == 1:
            add(day, 2, "Marketing", rng.randint(18_000, 31_000), "Campanha de marketing digital", "Comercial", "Agência Modelo")
        if day.weekday() == 3:
            add(day, 2, "Logística", rng.randint(10_000, 22_000), "Frete de entrega de produtos", "Operação", "Transportadora Modelo")
            add(day, 2, "Alimentação", rng.randint(9_000, 17_000), "Almoço da equipe", "Administrativo", "Restaurante Modelo")
        if day.day == 28:
            add(day, 1, "Outras receitas", rng.randint(1500, 6500), "Rendimento de aplicação financeira", "Financeiro", "Instituição fictícia")
            add(day, 2, "Outras despesas", rng.randint(5000, 12000), "Mensalidade de software de gestão", "Administrativo", "Software Modelo")
        if scenario["id"] == "horizonte" and day == end - timedelta(days=85):
            add(day, 2, "Outras despesas", 8_500_000, "Compra de equipamento administrativo", "Administrativo", "Equipamentos Modelo")
    return rows


IMPORT_HEADERS = ["Data", "Descrição", "Valor", "Tipo", "Categoria", "Documento", "Contraparte", "Centro de custo",
                  "Conta", "Forma de pagamento", "Competência", "Observações", "ID externo"]


def import_csv(rows):
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";", lineterminator="\r\n")
    writer.writerow(IMPORT_HEADERS)
    for r in rows:
        writer.writerow([r["data"], r["descricao"], f"{r['valor_centavos']/100:.2f}".replace(".", ","),
            "Receita" if r["tipo"] == 1 else "Despesa", r["categoria"], *(r.get(f, "") for f in ["documento", "contraparte",
            "centro_custo", "conta", "forma_pagamento", "competencia", "observacoes", "id_externo"])])
    return output.getvalue().encode("utf-8-sig")


def write_dataset(directory, topics, end=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    training = classification_data(topics)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(training[0]), delimiter=";")
    writer.writeheader()
    writer.writerows(training)
    contents = {"classificacao_rotulada.csv": buffer.getvalue().encode("utf-8-sig")}
    scenarios = []
    for scenario in SCENARIOS:
        rows = financial_history(scenario, end)
        years = sorted({r["data"][:4] for r in rows})
        for year in years:
            subset = [r for r in rows if r["data"].startswith(year)]
            contents[f"financeiro/{scenario['id']}_{year}.csv"] = import_csv(subset)
        scenarios.append({"id": scenario["id"], "nome": scenario["nome"], "registros": len(rows),
                          "inicio": rows[0]["data"], "fim": rows[-1]["data"], "saldo_inicial_centavos": scenario["saldo"]})
    manifest = {"versao": "sintetica-v2", "sintetico": True, "seed": 2702026,
        "classificacao": {"registros": len(training), "classes": dict(Counter(f"{r['tipo']}|{r['categoria']}" for r in training)),
                          "familias": len({r["grupo"] for r in training})},
        "cenarios": scenarios, "arquivos": {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                                               for name, data in contents.items()},
        "uso": "Dados artificiais. Não demonstram desempenho em empresas reais. O grupo de descrição deve permanecer na mesma partição."}
    for name, content in contents.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    (directory / "manifesto.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with zipfile.ZipFile(directory / "Base_Sintetica_LoonieMind.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in contents.items():
            archive.writestr(name, content)
        archive.writestr("manifesto.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest
