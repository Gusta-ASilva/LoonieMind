from datetime import date, timedelta

from looniemind.models import ForecastService


def test_cold_start_and_invalid_horizon(client, company):
    response = client.get(f"/api/companies/{company}/forecast").json()
    assert response["disponivel"] is False and response["serie"] == []
    assert client.get(f"/api/companies/{company}/forecast?dias=10000").status_code == 422
    assert client.post(f"/api/companies/{company}/model/train", json={}).status_code == 400


def test_demonstration_models_review_and_forecast(client):
    seeded = client.post("/api/demo")
    assert seeded.status_code == 200
    company = seeded.json()["empresa"]["id_empresa"]
    assert seeded.json()["modelo"]["sintetico"] is True
    assert seeded.json()["modelo"]["metricas"]["teste"] > 0
    assert seeded.json()["modelo"]["metricas"]["treino"] > seeded.json()["modelo"]["metricas"]["teste"]
    assert client.post("/api/demo").json()["existente"] is True
    pending = client.get(f"/api/companies/{company}/transactions?pendentes=true").json()
    assert pending["total"] > 0
    row = next(r for r in pending["itens"] if r["sugestao"])
    client.post(f"/api/companies/{company}/classify/accept", json={"ids": [row["id_lancamento"]]})
    with client.app.state.db.connect() as conn:
        confirmed = dict(conn.execute("SELECT * FROM Lancamentos WHERE id_lancamento=?", (row["id_lancamento"],)).fetchone())
    client.post(f"/api/companies/{company}/classify")
    with client.app.state.db.connect() as conn:
        after = dict(conn.execute("SELECT * FROM Lancamentos WHERE id_lancamento=?", (row["id_lancamento"],)).fetchone())
    assert after == confirmed and after["revisado"] == 1
    forecast = client.get(f"/api/companies/{company}/forecast?dias=30").json()
    assert forecast["disponivel"] is True and len(forecast["serie"]) == 30
    assert forecast["serie"][0]["data"] == (date.today() + timedelta(days=1)).isoformat()
    assert all(isinstance(r["receitas_centavos"], int) and r["receitas_centavos"] >= 0 for r in forecast["serie"])
    summary = client.get(f"/api/companies/{company}/summary").json()
    balance = summary["saldo_centavos"]
    for day in forecast["serie"]:
        balance += day["receitas_centavos"] - day["despesas_centavos"]
        assert balance == day["saldo_centavos"]
    for model in forecast["modelos"].values():
        assert model["avaliacao"]["fim_teste"] <= date.today().isoformat()
    assert client.get(f"/api/companies/{company}/forecast/export?formato=csv").status_code == 200
    assert client.get(f"/api/companies/{company}/forecast/export?formato=xlsx").status_code == 200
    changed = client.put(f"/api/companies/{company}", json={"nome": "Estúdio Aurora", "saldo_inicial_centavos": 3450000,
        "data_saldo": summary["empresa"]["data_saldo"]})
    assert changed.status_code == 200
    updated = client.get(f"/api/companies/{company}/forecast").json()
    assert updated["saldo_final_centavos"] == forecast["saldo_final_centavos"] + 1_000_000


def test_stale_history_is_not_forecast(client, company, movement):
    client.post(f"/api/companies/{company}/transactions", json={**movement,"data": (date.today()-timedelta(days=45)).isoformat()})
    forecast = ForecastService(client.app.state.db).calculate(company)
    assert forecast["disponivel"] is False and "desatualizado" in forecast["motivo"]


def test_company_classifier_never_uses_another_company_artifact(client, company):
    model = client.app.state.models
    assert not model.paths(company)[0].exists()
    suggestion = model.predict(company, [{"descricao": "Pagamento de aluguel", "tipo": 2}])[0]
    assert suggestion["metodo"] == "regra" and suggestion["score"] is None
