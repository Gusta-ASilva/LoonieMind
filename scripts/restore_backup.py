import argparse
from datetime import datetime
from pathlib import Path

from looniemind.backup import restore_backup
from looniemind.domain import DomainError


def main():
    parser = argparse.ArgumentParser(description="Restaura um backup em uma pasta nova; nunca sobrescreve os dados atuais.")
    parser.add_argument("arquivo", type=Path)
    parser.add_argument("--destination", type=Path, default=Path("restored-" + datetime.now().strftime("%Y%m%d-%H%M%S")))
    args = parser.parse_args()
    try:
        result = restore_backup(args.arquivo, args.destination)
    except (DomainError, OSError) as exc:
        parser.exit(1, f"Não foi possível restaurar: {exc}\n")
    print(f"Backup restaurado: {result['empresas']} empresa(s), {result['lancamentos']} lançamento(s).")
    print(f"Pasta nova: {result['destino']}")
    print("Feche a aplicação e defina LOONIEMIND_DATA_DIR para essa pasta antes de iniciar.")
    print("Os modelos devem ser treinados novamente; os lançamentos revisados foram preservados.")


if __name__ == "__main__":
    main()
