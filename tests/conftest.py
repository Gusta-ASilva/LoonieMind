from datetime import date, timedelta

from fastapi.testclient import TestClient
import pytest

from looniemind.api import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path)) as session:
        yield session


@pytest.fixture
def company(client):
    response = client.post("/api/companies", json={"nome": "Empresa de teste", "saldo_inicial_centavos": 100_000,
        "data_saldo": (date.today() - timedelta(days=365)).isoformat()})
    assert response.status_code == 201
    return response.json()["id_empresa"]


@pytest.fixture
def movement():
    return {"descricao": "Pagamento fornecedor", "categoria": "Fornecedores", "valor_centavos": 12345,
            "tipo": 2, "data": date.today().isoformat()}
