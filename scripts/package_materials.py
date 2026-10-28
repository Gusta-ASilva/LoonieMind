"""Reconstrói e confere o pacote dos materiais entregues, sem incluir dados locais."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "looniemind-v11-20261027"
PRESENTATION = ROOT / "outputs" / "looniemind-apresentacao-8-slides"
DATASET = ROOT / "datasets" / "sintetica-v2"
PACKAGE = OUTPUT / "LoonieMind_Materiais_Completos.zip"
RECEIPT = OUTPUT / "Manifesto_Materiais_Atuais.json"
DECK = "LoonieMind_Empresa_e_Sistema_8_Slides.pptx"
MANIFEST_NAME = "MANIFESTO-PACOTE.json"


def digest(content):
    return sha256(content).hexdigest()


def inventory():
    files = {
        DECK: PRESENTATION / DECK,
        "Roteiro_8_Slides.md": PRESENTATION / "Roteiro_8_Slides.md",
        "Roteiro_8_Slides.pdf": PRESENTATION / "Roteiro_8_Slides.pdf",
        "LEIA-ME.md": OUTPUT / "LEIA-ME.md",
        "Base_Sintetica_LoonieMind.zip": DATASET / "Base_Sintetica_LoonieMind.zip",
    }
    for name in (
        "Manual_Sistema_e_IA_LoonieMind.pdf", "Modelo_Importacao_LoonieMind.xlsx",
        "Relatorio_Demonstracao_LoonieMind.xlsx", "Projecao_Demonstracao_LoonieMind.xlsx",
    ):
        files[name] = OUTPUT / name
    for name in (
        "MANUAL-SISTEMA-E-IA.md", "ROTEIRO-APRESENTACAO.md", "GUIA-DE-USO.md",
        "ARQUITETURA.md", "DECISOES-E-ESCOPO.md", "VALIDACAO.md",
        "ATUALIZACAO-APRESENTACAO-EMPRESA.md", "relatorios/avaliacao-v1.1.json",
        "relatorios/apresentacao-8-slides.json",
    ):
        files[f"docs/{name}"] = ROOT / "docs" / name
    dataset_manifest = json.loads((DATASET / "manifesto.json").read_text(encoding="utf-8"))
    for name, metadata in dataset_manifest["arquivos"].items():
        path = (DATASET / name).resolve()
        if not path.is_relative_to(DATASET.resolve()):
            raise ValueError(f"Caminho fora da base sintética: {name}")
        content = path.read_bytes()
        if digest(content) != metadata["sha256"] or len(content) != metadata["bytes"]:
            raise ValueError(f"Base sintética alterada: {name}")
        files[f"datasets/sintetica-v2/{name}"] = path
    files["datasets/sintetica-v2/manifesto.json"] = DATASET / "manifesto.json"
    with ZipFile(PRESENTATION / DECK) as deck:
        slides = [name for name in deck.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        if len(slides) != 8 or deck.testzip() is not None:
            raise ValueError("A apresentação atual deve conter oito slides íntegros.")
    if PRESENTATION.joinpath("Roteiro_8_Slides.md").read_bytes() != (
        ROOT / "docs" / "ROTEIRO-APRESENTACAO.md"
    ).read_bytes():
        raise ValueError("O roteiro da documentação deve acompanhar os oito slides.")
    for name, path in files.items():
        if not path.is_file():
            raise FileNotFoundError(f"Material ausente: {name}")
    return dict(sorted(files.items()))


def manifest_for(files):
    return {
        "versao_aplicacao": "1.1.0",
        "apresentacao": {"arquivo": DECK, "slides": 8, "duracao_planejada_segundos": 275},
        "dados_sinteticos": True,
        "conteudo": "Materiais; o programa está no repositório GabrielIzi/LoonieMind.",
        "arquivos": {
            name: {"bytes": path.stat().st_size, "sha256": digest(path.read_bytes())}
            for name, path in files.items()
        },
    }


def verify(files, manifest):
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if receipt["manifesto"] != manifest:
        raise ValueError("O manifesto externo não corresponde aos materiais atuais.")
    if receipt["pacote"]["sha256"] != digest(PACKAGE.read_bytes()):
        raise ValueError("O hash do pacote não corresponde ao comprovante.")
    with ZipFile(PACKAGE) as archive:
        if archive.testzip() is not None:
            raise ValueError("Arquivo ZIP corrompido.")
        if set(archive.namelist()) != set(files) | {MANIFEST_NAME}:
            raise ValueError("O conteúdo do pacote difere da lista autorizada.")
        if json.loads(archive.read(MANIFEST_NAME)) != manifest:
            raise ValueError("Manifesto interno divergente.")
        for name, path in files.items():
            if digest(archive.read(name)) != digest(path.read_bytes()):
                raise ValueError(f"Conteúdo desatualizado no pacote: {name}")
    return {"arquivos": len(files) + 1, "bytes": PACKAGE.stat().st_size,
            "sha256": receipt["pacote"]["sha256"], "slides": 8}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Confere o pacote existente sem alterá-lo.")
    args = parser.parse_args()
    files = inventory()
    manifest = manifest_for(files)
    if not args.check:
        temporary = PACKAGE.with_suffix(".zip.tmp")
        try:
            with ZipFile(temporary, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
                contents = {name: path.read_bytes() for name, path in files.items()}
                contents[MANIFEST_NAME] = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
                for name, content in sorted(contents.items()):
                    info = ZipInfo(name, date_time=(2026, 10, 27, 0, 0, 0))
                    info.compress_type = ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, content, compresslevel=9)
            temporary.replace(PACKAGE)
        finally:
            temporary.unlink(missing_ok=True)
        receipt = {"manifesto": manifest, "pacote": {
            "arquivo": PACKAGE.name, "bytes": PACKAGE.stat().st_size,
            "sha256": digest(PACKAGE.read_bytes()),
        }}
        RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verify(files, manifest), ensure_ascii=False))


if __name__ == "__main__":
    main()
