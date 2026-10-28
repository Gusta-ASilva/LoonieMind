import argparse
import csv
import json
from pathlib import Path

from looniemind.db import Database
from looniemind.domain import DomainError, clean_text, parse_type
from looniemind.models import ModelService


def main():
    parser = argparse.ArgumentParser(description="Treina e avalia o classificador financeiro local.")
    parser.add_argument("--company", type=int, required=True)
    parser.add_argument("--source", choices=["reviewed", "synthetic"], default="reviewed")
    parser.add_argument("--csv", type=Path, help="CSV UTF-8, separado por ponto e vírgula: descricao;tipo;categoria")
    args = parser.parse_args()
    database = Database()
    database.initialize()
    try:
        records = None
        if args.csv:
            with args.csv.open(encoding="utf-8-sig", newline="") as file:
                records = []
                for row in csv.DictReader(file, delimiter=";"):
                    item = {"descricao": clean_text(row.get("descricao")), "tipo": parse_type(row.get("tipo")),
                            "categoria": clean_text(row.get("categoria"), 80),
                            "grupo": clean_text(row.get("grupo"), 200), "fonte": clean_text(row.get("fonte"), 40)}
                    if not item["descricao"] or not item["tipo"] or not item["categoria"]:
                        raise ValueError("Cada linha precisa de descricao, tipo e categoria válidos.")
                    records.append(item)
        result = ModelService(database).train(args.company, args.source, records)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (DomainError, OSError, ValueError) as exc:
        parser.exit(1, f"Treinamento não concluído: {exc}\n")


if __name__ == "__main__":
    main()
