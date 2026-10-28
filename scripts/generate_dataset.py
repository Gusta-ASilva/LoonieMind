import argparse
from datetime import date
import json
from pathlib import Path

from looniemind.models import TRAINING_TOPICS
from looniemind.synthetic import write_dataset

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera base fictícia documentada de classificação e fluxo de caixa.")
    parser.add_argument("--output", type=Path, default=Path("datasets/sintetica-v2"))
    parser.add_argument("--end", type=date.fromisoformat, help="Último dia do cenário, AAAA-MM-DD; padrão: hoje")
    args = parser.parse_args()
    manifest = write_dataset(args.output, TRAINING_TOPICS, end=args.end)
    print(json.dumps({"classificacao": manifest["classificacao"], "cenarios": manifest["cenarios"]}, ensure_ascii=False, indent=2))
