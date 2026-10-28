"""SQLite operacional versionado; o arquivo Database original permanece como referência."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3

from .domain import DETAIL_FIELDS, DomainError

ROOT = Path(__file__).resolve().parent.parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS Empresas (
 id_empresa INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL CHECK(length(trim(nome))>0),
 descricao TEXT NOT NULL DEFAULT '', saldo_inicial_centavos INTEGER NOT NULL DEFAULT 0,
 data_saldo TEXT NOT NULL, demo INTEGER NOT NULL DEFAULT 0 CHECK(demo IN (0,1)),
 revisao INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS Categorias (
 id_categoria INTEGER PRIMARY KEY AUTOINCREMENT, id_empresa INTEGER NOT NULL REFERENCES Empresas(id_empresa),
 nome TEXT NOT NULL, tipo INTEGER NOT NULL CHECK(tipo IN (1,2)), UNIQUE(id_empresa,nome,tipo)
);
CREATE TABLE IF NOT EXISTS Planilhas (
 id_planilha TEXT PRIMARY KEY, id_empresa INTEGER NOT NULL REFERENCES Empresas(id_empresa),
 nome TEXT NOT NULL, file_url TEXT NOT NULL, sha256 TEXT NOT NULL, aba TEXT NOT NULL DEFAULT '',
 opcoes TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL CHECK(status IN ('preview','confirmed','undone')),
 total_linhas INTEGER NOT NULL DEFAULT 0, importados INTEGER NOT NULL DEFAULT 0,
 rejeitados INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_import ON Planilhas(id_empresa,sha256,aba) WHERE status='confirmed';
CREATE TABLE IF NOT EXISTS Lancamentos (
 id_lancamento INTEGER PRIMARY KEY AUTOINCREMENT,
 id_empresa INTEGER NOT NULL REFERENCES Empresas(id_empresa),
 id_planilha TEXT REFERENCES Planilhas(id_planilha), linha_origem INTEGER,
 descricao TEXT NOT NULL CHECK(length(trim(descricao))>0), categoria TEXT NOT NULL DEFAULT 'Sem categoria',
 valor_centavos INTEGER NOT NULL CHECK(typeof(valor_centavos)='integer' AND valor_centavos>0),
 data TEXT NOT NULL, tipo INTEGER CHECK(tipo IN (1,2)),
 revisado INTEGER NOT NULL DEFAULT 0 CHECK(revisado IN (0,1)),
 origem TEXT NOT NULL, sugestao TEXT, original TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 documento TEXT NOT NULL DEFAULT '', contraparte TEXT NOT NULL DEFAULT '',
 centro_custo TEXT NOT NULL DEFAULT '', conta TEXT NOT NULL DEFAULT '',
 forma_pagamento TEXT NOT NULL DEFAULT '', competencia TEXT NOT NULL DEFAULT '',
 observacoes TEXT NOT NULL DEFAULT '', id_externo TEXT NOT NULL DEFAULT '',
 UNIQUE(id_planilha,linha_origem)
);
CREATE INDEX IF NOT EXISTS ix_lancamentos_empresa_data ON Lancamentos(id_empresa,data,id_lancamento);
CREATE INDEX IF NOT EXISTS ix_lancamentos_planilha ON Lancamentos(id_planilha);
CREATE INDEX IF NOT EXISTS ix_planilhas_empresa ON Planilhas(id_empresa,created_at);
CREATE TABLE IF NOT EXISTS Auditoria (
 id INTEGER PRIMARY KEY AUTOINCREMENT, id_empresa INTEGER NOT NULL REFERENCES Empresas(id_empresa),
 acao TEXT NOT NULL, entidade TEXT NOT NULL, referencia TEXT, detalhes TEXT NOT NULL, created_at TEXT NOT NULL
);
"""

CATEGORIES = {
    1: ["Vendas", "Serviços", "Outras receitas"],
    2: ["Fornecedores", "Aluguel", "Pessoal", "Impostos", "Marketing", "Logística", "Alimentação", "Utilidades", "Outras despesas"],
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


class Database:
    def __init__(self, directory=None):
        self.directory = Path(directory or os.environ.get("LOONIEMIND_DATA_DIR", ROOT / "data")).resolve()
        self.path = self.directory / "looniemind.sqlite3"

    def initialize(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / "uploads").mkdir(exist_ok=True)
        (self.directory / "models").mkdir(exist_ok=True)
        with self.connect() as conn:
            current_version = conn.execute("PRAGMA user_version").fetchone()[0]
            if current_version > 2:
                raise DomainError("Este banco usa uma versão mais recente. Atualize a aplicação.")
            if current_version == 1:
                backup_dir = self.directory / "backups"
                backup_dir.mkdir(exist_ok=True)
                backup_path = backup_dir / "antes-da-versao-2.sqlite3"
                if not backup_path.exists():
                    with sqlite3.connect(backup_path) as snapshot:
                        conn.backup(snapshot)
            conn.executescript(SCHEMA)
            conn.execute("BEGIN IMMEDIATE")
            columns = {row[1] for row in conn.execute("PRAGMA table_info(Lancamentos)")}
            for field in DETAIL_FIELDS:
                if field not in columns:
                    conn.execute(f"ALTER TABLE Lancamentos ADD COLUMN {field} TEXT NOT NULL DEFAULT ''")
            conn.execute("INSERT OR IGNORE INTO schema_migrations VALUES (1,?)", (now(),))
            conn.execute("INSERT OR IGNORE INTO schema_migrations VALUES (2,?)", (now(),))
            conn.execute("PRAGMA user_version=2")

    @contextmanager
    def connect(self, write=False):
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=15000")
        try:
            if write:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def company(self, conn, company_id):
        row = conn.execute("SELECT * FROM Empresas WHERE id_empresa=?", (company_id,)).fetchone()
        if not row:
            raise DomainError("Empresa não encontrada.", 404)
        return dict(row)

    def categories(self, conn, company_id):
        self.company(conn, company_id)
        return [dict(row) for row in conn.execute(
            "SELECT * FROM Categorias WHERE id_empresa=? ORDER BY tipo,nome", (company_id,)
        )]

    def add_defaults(self, conn, company_id):
        for kind, names in CATEGORIES.items():
            conn.executemany("INSERT OR IGNORE INTO Categorias(id_empresa,nome,tipo) VALUES(?,?,?)",
                             [(company_id, name, kind) for name in names])

    def touch(self, conn, company_id):
        conn.execute("UPDATE Empresas SET revisao=revisao+1,updated_at=? WHERE id_empresa=?", (now(), company_id))

    def audit(self, conn, company_id, action, entity, reference, details):
        conn.execute("INSERT INTO Auditoria(id_empresa,acao,entidade,referencia,detalhes,created_at) VALUES(?,?,?,?,?,?)",
                     (company_id, action, entity, str(reference), json.dumps(details, ensure_ascii=False), now()))
