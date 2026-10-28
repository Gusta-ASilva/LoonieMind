"""Acrescenta a demonstração ampliada, preserva empresas existentes e registra a avaliação."""
import json
from pathlib import Path

from looniemind.db import Database, now
from looniemind.models import ForecastService, ModelService
from looniemind.services import FinanceService


def main():
    database = Database()
    database.initialize()
    models, forecasts = ModelService(database), ForecastService(database)
    finance = FinanceService(database, models, forecasts)
    with database.connect() as connection:
        before = {r[0]: r[1] for r in connection.execute("SELECT id_empresa,count(*) FROM Lancamentos GROUP BY id_empresa")}
    result = finance.seed_expanded_demo()
    output = {"gerado_em": now(), "sintetico": True, "empresas": []}
    for index, entry in enumerate(result["empresas"]):
        identifier = entry["empresa"]["id_empresa"]
        status = models.status(identifier)
        if index == 0 and (not status["disponivel"] or status.get("exemplos", 0) < 14400):
            print("Treinando classificador com 14.400 exemplos...", flush=True)
            status = models.train(identifier, "synthetic")
            finance.classify(identifier)
        forecast = forecasts.calculate(identifier)
        summary = finance.summary(identifier)
        summary.pop("fluxo_diario", None)
        output["empresas"].append({"empresa": entry["empresa"], "modelo": status, "previsao": forecast,
                                    "resumo": summary})
        print(json.dumps({"empresa": entry["empresa"]["nome"], "registros": summary["total_lancamentos"],
            "f1": status.get("metricas", {}).get("f1_macro"), "previsao": forecast.get("metodo")}, ensure_ascii=False), flush=True)
    with database.connect() as connection:
        after = {r[0]: r[1] for r in connection.execute("SELECT id_empresa,count(*) FROM Lancamentos GROUP BY id_empresa")}
    assert all(after[key] == value for key, value in before.items()), "Os totais existentes devem ser preservados."
    output["preservacao"] = {"contagens_anteriores": before, "verificado": True}
    destination = Path("docs/relatorios/avaliacao-v1.1.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
