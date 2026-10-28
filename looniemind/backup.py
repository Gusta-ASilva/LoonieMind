"""Restaura dados em uma pasta nova, sem executar o esquema SQL do arquivo recebido."""
from pathlib import Path
import re
import sqlite3
import zipfile

from .db import SCHEMA, now
from .domain import DomainError

TABLES = ["Empresas", "Categorias", "Planilhas", "Lancamentos", "Auditoria"]
UPLOAD_NAME = re.compile(r"uploads/[a-f0-9]{32}\.(csv|xls|xlsx)")


def restore_backup(backup_path, destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise DomainError("A pasta de destino já existe. Escolha uma pasta nova para preservar seus dados.")
    if not destination.parent.is_dir():
        raise DomainError("A pasta superior do destino precisa existir.")
    source, target = sqlite3.connect(":memory:"), sqlite3.connect(":memory:")
    try:
        with zipfile.ZipFile(backup_path) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if len(entries) > 10_000 or sum(entry.file_size for entry in entries) > 200 * 1024 * 1024:
                raise DomainError("Backup excede o limite de 200 MB ou 10.000 arquivos.")
            if len(set(names)) != len(names) or "looniemind.sqlite3" not in names:
                raise DomainError("Estrutura do backup inválida.")
            if any(name not in {"looniemind.sqlite3", "manifest.json"} and not UPLOAD_NAME.fullmatch(name) for name in names):
                raise DomainError("O backup contém caminhos ou arquivos não permitidos.")
            source.deserialize(archive.read("looniemind.sqlite3"))
            source.execute("PRAGMA query_only=ON")
            source.execute("PRAGMA trusted_schema=OFF")
            if source.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise DomainError("O banco do backup não passou na verificação de integridade.")
            if source.execute("PRAGMA user_version").fetchone()[0] not in {1, 2}:
                raise DomainError("Versão do backup incompatível com esta aplicação.")
            target.executescript(SCHEMA)
            target.execute("PRAGMA foreign_keys=ON")
            target.execute("BEGIN")
            for table in TABLES:
                source_columns = {r[1] for r in source.execute(f"PRAGMA table_info({table})")}
                columns = [r[1] for r in target.execute(f"PRAGMA table_info({table})") if r[1] in source_columns]
                source_object = source.execute("SELECT type FROM sqlite_master WHERE name=?", (table,)).fetchone()
                if not source_object or source_object[0] != "table":
                    raise DomainError("Uma tabela obrigatória está ausente no backup.")
                fields = ",".join(f'"{column}"' for column in columns)
                records = source.execute(f"SELECT {fields} FROM {table}").fetchall()
                target.executemany(f"INSERT INTO {table}({fields}) VALUES({','.join('?' for _ in columns)})", records)
            for (file_url,) in target.execute("SELECT file_url FROM Planilhas"):
                if not UPLOAD_NAME.fullmatch(file_url):
                    raise DomainError("Referência de arquivo original inválida no backup.")
            target.execute("INSERT INTO schema_migrations VALUES(1,?)", (now(),))
            target.execute("INSERT INTO schema_migrations VALUES(2,?)", (now(),))
            target.execute("PRAGMA user_version=2")
            target.commit()
            content = target.serialize()
            destination.mkdir()
            (destination / "uploads").mkdir()
            (destination / "models").mkdir()
            (destination / "looniemind.sqlite3").write_bytes(content)
            for name in names:
                if UPLOAD_NAME.fullmatch(name):
                    (destination / name).write_bytes(archive.read(name))
            return {"destino": str(destination), "empresas": target.execute("SELECT count(*) FROM Empresas").fetchone()[0],
                    "lancamentos": target.execute("SELECT count(*) FROM Lancamentos").fetchone()[0]}
    except (sqlite3.Error, zipfile.BadZipFile, KeyError) as exc:
        raise DomainError("Backup inválido ou incompatível. A pasta de dados atual foi preservada.") from exc
    finally:
        source.close()
        target.close()
