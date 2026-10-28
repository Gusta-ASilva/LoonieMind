"""Importação em duas fases, com prévia repetível e confirmação transacional."""
import csv
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import uuid
import zipfile

import pandas as pd

from .db import now
from .domain import DETAIL_FIELDS, DomainError, clean_text, money_to_cents, movement_details, normalized, parse_date, parse_type

MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 10_000
ALIASES = {
    "data": {"data", "date", "dt", "data pagamento", "data da movimentacao", "data lancamento", "data realizada"},
    "descricao": {"descricao", "description", "historico", "lancamento", "detalhes", "desc"},
    "valor": {"valor", "amount", "value", "valor r$", "valor total", "valor (r$)"},
    "tipo": {"tipo", "type", "natureza", "entrada/saida", "operacao"},
    "categoria": {"categoria", "category", "classificacao", "grupo"},
    "entrada": {"entrada", "entradas", "receita", "receitas", "credito"},
    "saida": {"saida", "saidas", "despesa", "despesas", "debito"},
    "documento": {"documento", "nota fiscal", "nf", "numero documento"},
    "contraparte": {"contraparte", "cliente/fornecedor", "cliente ou fornecedor", "favorecido", "cliente", "fornecedor"},
    "centro_custo": {"centro de custo", "centro_custo", "departamento", "unidade"},
    "conta": {"conta", "conta financeira", "conta bancaria"},
    "forma_pagamento": {"forma de pagamento", "forma_pagamento", "meio de pagamento", "pagamento"},
    "competencia": {"competencia", "mes competencia"},
    "observacoes": {"observacoes", "observacao", "notas"},
    "id_externo": {"id externo", "id_externo", "identificador externo", "identificador"},
}


def read_table(content, extension, options):
    if len(content) > MAX_BYTES:
        raise DomainError("O arquivo excede o limite de 10 MB.", 413)
    if not content:
        raise DomainError("O arquivo está vazio.")
    header = options.get("header_row", 0)
    if not isinstance(header, int) or not 0 <= header <= 20:
        raise DomainError("A linha de cabeçalho deve estar entre 1 e 21.")
    sheets, encoding, separator = [], None, None
    try:
        if extension == ".csv":
            encoding = options.get("encoding", "auto")
            if encoding not in {"auto", "utf-8-sig", "cp1252"}:
                raise DomainError("Codificação não suportada.")
            if encoding == "auto":
                try:
                    text = content.decode("utf-8-sig")
                    encoding = "utf-8-sig"
                except UnicodeDecodeError:
                    text, encoding = content.decode("cp1252"), "cp1252"
            else:
                text = content.decode(encoding)
            separator = options.get("separator")
            if separator and separator not in {",", ";", "\t", "|"}:
                raise DomainError("Separador inválido.")
            if not separator:
                try:
                    separator = csv.Sniffer().sniff(text[:8000], delimiters=",;\t|").delimiter
                except csv.Error:
                    separator = ";" if ";" in text.splitlines()[header] else ","
            frame = pd.read_csv(io.StringIO(text), sep=separator, header=header,
                                dtype=str, keep_default_na=False, nrows=MAX_ROWS + 1)
            sheet = "CSV"
        elif extension in {".xlsx", ".xls"}:
            if extension == ".xlsx":
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    entries = archive.infolist()
                    if len(entries) > 2000 or sum(x.file_size for x in entries) > 100 * 1024 * 1024:
                        raise DomainError("A planilha excede o limite de conteúdo descompactado.", 413)
            with pd.ExcelFile(io.BytesIO(content), engine="openpyxl" if extension == ".xlsx" else "xlrd") as book:
                sheets = book.sheet_names
                if len(sheets) > 30:
                    raise DomainError("Limite de 30 abas por arquivo.")
                sheet = options.get("sheet") or sheets[0]
                if sheet not in sheets:
                    raise DomainError("A aba selecionada não existe no arquivo.")
                frame = pd.read_excel(book, sheet_name=sheet, header=header, dtype=str,
                                      keep_default_na=False, nrows=MAX_ROWS + 1)
        else:
            raise DomainError("Formato não suportado. Envie CSV, XLS ou XLSX.")
    except DomainError:
        raise
    except Exception as exc:
        raise DomainError("Não foi possível ler o arquivo. Confira o formato, o cabeçalho e se ele está protegido por senha.") from exc
    if len(frame) > MAX_ROWS or len(frame.columns) > 100:
        raise DomainError("Limite de 10.000 linhas e 100 colunas por arquivo.", 413)
    frame.columns = [clean_text(c, 100) for c in frame.columns]
    if len(set(frame.columns)) != len(frame.columns):
        raise DomainError("Existem cabeçalhos repetidos. Renomeie as colunas antes de importar.")
    if frame.empty and (extension == ".csv" or len(sheets) <= 1):
        raise DomainError("Nenhum lançamento foi encontrado após o cabeçalho.")
    return frame, {"sheet": sheet, "sheets": sheets, "encoding": encoding, "separator": separator}


def suggest_mapping(columns):
    return {field: next((column for column in columns if normalized(column) in aliases), "")
            for field, aliases in ALIASES.items()}


def normalize_rows(frame, options):
    mapping = options.get("mapping") or suggest_mapping(frame.columns)
    if not isinstance(mapping, dict) or set(mapping) - set(ALIASES):
        raise DomainError("Mapeamento de colunas inválido.")
    for column in mapping.values():
        if column and column not in frame.columns:
            raise DomainError(f"A coluna {column!r} não existe nesta aba.")
    selected = [c for c in mapping.values() if c]
    if len(set(selected)) != len(selected):
        raise DomainError("Uma coluna não pode representar dois campos diferentes.")
    missing = [field for field in ("data", "descricao") if not mapping.get(field)]
    if not mapping.get("valor") and not (mapping.get("entrada") and mapping.get("saida")):
        missing.append("valor ou as duas colunas entrada/saída")
    if missing:
        return [], [], mapping, missing
    records, errors = [], []
    for idx, source in frame.iterrows():
        number = int(idx) + options.get("header_row", 0) + 2
        raw = {str(k): clean_text(v, 500) for k, v in source.items()}
        if all(not value for value in raw.values()):
            continue
        def get(field):
            return raw.get(mapping.get(field), "")
        try:
            description = clean_text(get("descricao"))
            if not description:
                raise ValueError("Descrição obrigatória.")
            kind = parse_type(get("tipo"))
            if mapping.get("valor"):
                signed = money_to_cents(get("valor"), options.get("decimal_format", "auto"))
                if signed < 0 and kind == 1:
                    raise ValueError("Valor negativo conflita com o tipo Receita.")
                if kind is None:
                    kind = 2 if signed < 0 else (1 if options.get("signed_values") else None)
                amount = abs(signed)
            else:
                income = money_to_cents(get("entrada") or "0", options.get("decimal_format", "auto"), True)
                expense = money_to_cents(get("saida") or "0", options.get("decimal_format", "auto"), True)
                if income < 0 or expense < 0 or (income > 0) == (expense > 0):
                    raise ValueError("Informe apenas uma entrada ou saída positiva na linha.")
                inferred = 1 if income else 2
                if kind and kind != inferred:
                    raise ValueError("Tipo conflita com as colunas de entrada/saída.")
                amount, kind = income or expense, inferred
            category = clean_text(get("categoria"), 80) or "Sem categoria"
            movement_date = parse_date(get("data"), options.get("day_first", True))
            if movement_date > date.today().isoformat():
                raise ValueError("Use uma data realizada: movimentações futuras não fazem parte do histórico de caixa.")
            records.append({"linha": number, "data": movement_date,
                            "descricao": description, "valor_centavos": amount, "tipo": kind,
                            "categoria": category, "revisado": int(category != "Sem categoria" and kind is not None),
                            "original": raw, **movement_details({field: get(field) for field in DETAIL_FIELDS})})
        except ValueError as exc:
            errors.append({"linha": number, "mensagem": str(exc), "dados": raw})
    return records, errors, mapping, []


class ImportService:
    def __init__(self, db):
        self.db = db

    def create(self, company_id, name, content, options):
        extension = Path(name or "").suffix.lower()
        frame, meta = read_table(content, extension, options)
        options = {**options, "sheet": meta["sheet"]}
        import_id = uuid.uuid4().hex
        relative = f"uploads/{import_id}{extension}"
        with self.db.connect() as conn:
            self.db.company(conn, company_id)
        path = self.db.directory / relative
        path.write_bytes(content)
        try:
            with self.db.connect(write=True) as conn:
                conn.execute("""INSERT INTO Planilhas(id_planilha,id_empresa,nome,file_url,sha256,aba,opcoes,
                    status,total_linhas,created_at,updated_at) VALUES(?,?,?,?,?,?,?,'preview',?,?,?)""",
                    (import_id, company_id, clean_text(Path(name).name, 150), relative,
                     hashlib.sha256(content).hexdigest(), meta["sheet"], json.dumps(options), len(frame), now(), now()))
            return self.preview(company_id, import_id, options)
        except BaseException:
            path.unlink(missing_ok=True)
            with self.db.connect(write=True) as conn:
                conn.execute("DELETE FROM Planilhas WHERE id_planilha=? AND status='preview'", (import_id,))
            raise

    def get(self, conn, company_id, import_id):
        self.db.company(conn, company_id)
        row = conn.execute("SELECT * FROM Planilhas WHERE id_empresa=? AND id_planilha=?", (company_id, import_id)).fetchone()
        if not row:
            raise DomainError("Importação não encontrada nesta empresa.", 404)
        return dict(row)

    def _read(self, record, options):
        path = self.db.directory / record["file_url"]
        if not path.is_file():
            raise DomainError("O arquivo original não está disponível. Envie a planilha novamente.", 409)
        frame, meta = read_table(path.read_bytes(), path.suffix, options)
        records, errors, mapping, missing = normalize_rows(frame, options)
        return frame, meta, records, errors, mapping, missing

    def preview(self, company_id, import_id, changes=None):
        with self.db.connect(write=True) as conn:
            record = self.get(conn, company_id, import_id)
            if record["status"] != "preview":
                raise DomainError("Esta importação já foi finalizada.", 409)
            options = {**json.loads(record["opcoes"]), **(changes or {})}
            frame, meta, records, errors, mapping, missing = self._read(record, options)
            options.update({"sheet": meta["sheet"], "mapping": mapping})
            duplicate = conn.execute("SELECT id_planilha FROM Planilhas WHERE id_empresa=? AND sha256=? AND aba=? AND status='confirmed'",
                                     (company_id, record["sha256"], meta["sheet"])).fetchone()
            existing = {tuple(row) for row in conn.execute(
                "SELECT data,descricao,valor_centavos,tipo FROM Lancamentos WHERE id_empresa=?", (company_id,))}
            suspected = sum((r["data"], r["descricao"], r["valor_centavos"], r["tipo"]) in existing for r in records)
            conn.execute("UPDATE Planilhas SET opcoes=?,aba=?,total_linhas=?,updated_at=? WHERE id_planilha=?",
                         (json.dumps(options), meta["sheet"], len(frame), now(), import_id))
            return {"id_planilha": import_id, "nome": record["nome"], "colunas": list(frame.columns),
                    "opcoes": options, "metadados": meta, "total": len(records) + len(errors),
                    "validos": len(records), "invalidos": len(errors), "sem_tipo": sum(r["tipo"] is None for r in records),
                    "duplicado": bool(duplicate), "possiveis_duplicados": suspected,
                    "campos_ausentes": missing, "amostra_original": frame.head(5).to_dict(orient="records"),
                    "linhas": [{k: v for k, v in r.items() if k != "original"} for r in records[:30]],
                    "erros": errors[:200], "erros_truncados": len(errors) > 200}

    def confirm(self, company_id, import_id, allow_partial=False, acknowledge_duplicates=False):
        try:
            with self.db.connect(write=True) as conn:
                record = self.get(conn, company_id, import_id)
                if record["status"] == "confirmed":
                    return {"id_planilha": import_id, "importados": record["importados"], "ja_confirmado": True}
                if record["status"] != "preview":
                    raise DomainError("A importação foi desfeita. Envie o arquivo novamente.", 409)
                options = json.loads(record["opcoes"])
                _, _, records, errors, _, missing = self._read(record, options)
                if missing or not records:
                    raise DomainError("Mapeie os campos e corrija as linhas antes de confirmar.")
                if errors and not allow_partial:
                    raise DomainError("Existem linhas inválidas. Corrija o arquivo ou autorize a importação parcial.", 422)
                existing = {tuple(row) for row in conn.execute(
                    "SELECT data,descricao,valor_centavos,tipo FROM Lancamentos WHERE id_empresa=?", (company_id,))}
                if not acknowledge_duplicates and any((r["data"], r["descricao"], r["valor_centavos"], r["tipo"]) in existing for r in records):
                    raise DomainError("Há lançamentos semelhantes no histórico. Confirme que deseja mantê-los.", 409)
                timestamp = now()
                for row in records:
                    fields = ["id_empresa", "id_planilha", "linha_origem", "descricao", "categoria", "valor_centavos",
                              "data", "tipo", "revisado", "origem", "original", "created_at", "updated_at", *DETAIL_FIELDS]
                    values = [company_id, import_id, row["linha"], row["descricao"], row["categoria"], row["valor_centavos"],
                              row["data"], row["tipo"], row["revisado"], "importacao", json.dumps(row["original"], ensure_ascii=False),
                              timestamp, timestamp, *(row[field] for field in DETAIL_FIELDS)]
                    conn.execute(f"INSERT INTO Lancamentos({','.join(fields)}) VALUES({','.join('?' for _ in fields)})", values)
                    if row["revisado"]:
                        conn.execute("INSERT OR IGNORE INTO Categorias(id_empresa,nome,tipo) VALUES(?,?,?)",
                                     (company_id, row["categoria"], row["tipo"]))
                conn.execute("UPDATE Planilhas SET status='confirmed',importados=?,rejeitados=?,updated_at=? WHERE id_planilha=?",
                             (len(records), len(errors), timestamp, import_id))
                self.db.touch(conn, company_id)
                self.db.audit(conn, company_id, "importar", "planilha", import_id,
                              {"arquivo": record["nome"], "linhas": len(records), "rejeitadas": len(errors)})
                return {"id_planilha": import_id, "importados": len(records), "rejeitados": len(errors), "ja_confirmado": False}
        except sqlite3.IntegrityError as exc:
            raise DomainError("Esta aba deste arquivo já foi importada para a empresa.", 409) from exc

    def undo(self, company_id, import_id):
        with self.db.connect(write=True) as conn:
            record = self.get(conn, company_id, import_id)
            if record["status"] != "confirmed":
                raise DomainError("Somente importações confirmadas podem ser desfeitas.", 409)
            count = conn.execute("SELECT count(*) FROM Lancamentos WHERE id_planilha=?", (import_id,)).fetchone()[0]
            conn.execute("DELETE FROM Lancamentos WHERE id_planilha=? AND id_empresa=?", (import_id, company_id))
            conn.execute("UPDATE Planilhas SET status='undone',updated_at=? WHERE id_planilha=?", (now(), import_id))
            self.db.touch(conn, company_id)
            self.db.audit(conn, company_id, "desfazer_importacao", "planilha", import_id, {"removidos": count})
            return {"removidos": count}
