"""Conversões estritas na fronteira; todo cálculo financeiro usa centavos."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math
import re
import unicodedata

DETAIL_FIELDS = {"documento": 80, "contraparte": 120, "centro_custo": 80, "conta": 80,
                 "forma_pagamento": 60, "competencia": 10, "observacoes": 500, "id_externo": 100}


def movement_details(values):
    result = {}
    for field, limit in DETAIL_FIELDS.items():
        text = clean_text(values.get(field), 501)
        if len(text) > limit:
            raise ValueError(f"O campo {field} deve ter até {limit} caracteres.")
        if field == "competencia" and text:
            if re.fullmatch(r"\d{2}/\d{4}", text):
                text = text[3:] + "-" + text[:2]
            elif len(text) >= 10:
                text = parse_date(text)[:7]
            if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", text):
                raise ValueError("Competência inválida. Use AAAA-MM ou MM/AAAA.")
        result[field] = text
    return result


class DomainError(Exception):
    def __init__(self, message: str, status: int = 400, details=None):
        super().__init__(message)
        self.message, self.status, self.details = message, status, details


def normalized(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return re.sub(r"\s+", " ", "".join(c for c in text if not unicodedata.combining(c))).lower().strip()


def clean_text(value, limit=250) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return re.sub(r"[\x00-\x1f]", " ", str(value)).strip()[:limit]


def money_to_cents(value, decimal_format="auto", allow_zero=False) -> int:
    if isinstance(value, bool) or value is None:
        raise ValueError("Informe um valor monetário.")
    raw = clean_text(value, 80).replace("R$", "").replace("\u00a0", "").replace(" ", "")
    if not raw or raw.lower() in {"nan", "inf", "none", "-"}:
        raise ValueError("Valor monetário inválido.")
    if raw.startswith("(") and raw.endswith(")"):
        raw = "-" + raw[1:-1]
    if decimal_format == "us":
        if not re.fullmatch(r"[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?", raw):
            raise ValueError("Valor incompatível com o formato decimal selecionado.")
        raw = raw.replace(",", "")
    elif decimal_format == "br" or "," in raw:
        if not re.fullmatch(r"[+-]?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?", raw):
            raise ValueError("Valor incompatível com o formato brasileiro selecionado.")
        raw = raw.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}\.\d{3}", raw):
        raise ValueError("Valor ambíguo: escolha o formato brasileiro ou decimal na importação.")
    if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", raw):
        raise ValueError("Valor monetário inválido.")
    try:
        amount = Decimal(raw)
        if not amount.is_finite():
            raise ValueError("Valor monetário inválido.")
        cents = int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, OverflowError):
        raise ValueError("Valor monetário inválido.") from None
    if abs(cents) > 100_000_000_000_000 or (cents == 0 and not allow_zero):
        raise ValueError("O valor deve ser diferente de zero e estar dentro do limite permitido.")
    return cents


def parse_date(value, day_first=True) -> str:
    if isinstance(value, (datetime, date)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    text = clean_text(value, 50)
    formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]
    formats += ["%d/%m/%Y", "%d-%m-%Y"] if day_first else ["%m/%d/%Y", "%m-%d-%Y"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(text, fmt).date()
            if parsed.year < 1900 or parsed.year > 2200:
                break
            return parsed.isoformat()
        except ValueError:
            continue
    raise ValueError("Data inválida. Use DD/MM/AAAA ou AAAA-MM-DD e confira o formato selecionado.")


def parse_type(value):
    text = normalized(value)
    if text in {"1", "1.0", "receita", "entrada", "credito", "credit", "c", "+"}:
        return 1
    if text in {"2", "2.0", "despesa", "saida", "debito", "debit", "d", "-"}:
        return 2
    if not text or text in {"pendente", "a definir", "nao informado"}:
        return None
    raise ValueError("Tipo inválido: use Receita/Entrada/1 ou Despesa/Saída/2.")
