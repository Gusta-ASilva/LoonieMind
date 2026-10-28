import io
from datetime import date
from pathlib import Path
import sqlite3
import zipfile

import pytest

from looniemind.backup import restore_backup
from looniemind.domain import DomainError
from looniemind.api import create_app
from fastapi.testclient import TestClient


def test_restore_preserves_data_and_never_overwrites(client, company, movement, tmp_path):
    client.post(f"/api/companies/{company}/transactions", json=movement)
    content = client.get("/api/backup").content
    destination = tmp_path / "restored"
    result = restore_backup(io.BytesIO(content), destination)
    assert result["lancamentos"] == 1
    with sqlite3.connect(destination / "looniemind.sqlite3") as conn:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("SELECT valor_centavos FROM Lancamentos").fetchone()[0] == movement["valor_centavos"]
    with pytest.raises(DomainError, match="já existe"):
        restore_backup(io.BytesIO(content), destination)
    assert Path(client.app.state.db.path).is_file()


def test_restore_rejects_zip_path_traversal_and_sqlite_schema(client, tmp_path):
    source = io.BytesIO(client.get("/api/backup").content)
    with zipfile.ZipFile(source, "a") as archive:
        archive.writestr("../outside.txt", "unsafe")
    with pytest.raises(DomainError, match="não permitidos"):
        restore_backup(source, tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


def test_restore_preserves_original_files_and_can_finish_preview(client, company, tmp_path):
    content = f"Data;Descricao;Valor;Tipo\n{date.today()};Venda;10,00;Receita".encode()
    response = client.post(f"/api/companies/{company}/imports", files={"arquivo": ("original.csv", content)})
    identifier = response.json()["id_planilha"]
    destination = tmp_path / "recovered"
    restore_backup(io.BytesIO(client.get("/api/backup").content), destination)
    with TestClient(create_app(destination)) as recovered:
        preview = recovered.post(f"/api/companies/{company}/imports/{identifier}/preview", json={})
        assert preview.status_code == 200 and preview.json()["validos"] == 1
        assert recovered.post(f"/api/companies/{company}/imports/{identifier}/confirm", json={}).status_code == 200
        assert recovered.get(f"/api/companies/{company}/transactions").json()["total"] == 1
