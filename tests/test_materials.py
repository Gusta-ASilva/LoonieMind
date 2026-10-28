from hashlib import sha256
from io import BytesIO
import json
import re
from zipfile import ZipFile


def test_current_materials_downloads_and_package(client):
    response = client.get("/api/materials")
    assert response.status_code == 200
    materials = {item["id"]: item for item in response.json()}
    assert "8 slides" in materials["apresentacao"]["nome"]
    assert "4min35s" in materials["roteiro"]["nome"]
    presentation = client.get(materials["apresentacao"]["url"])
    assert presentation.status_code == 200
    assert "8_Slides.pptx" in presentation.headers["content-disposition"]
    with ZipFile(BytesIO(presentation.content)) as deck:
        slides = [name for name in deck.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        assert len(slides) == 8
    guide = client.get(materials["roteiro"]["url"])
    assert guide.status_code == 200
    assert guide.content.startswith(b"%PDF-")
    package = client.get(materials["pacote"]["url"])
    assert package.status_code == 200
    with ZipFile(BytesIO(package.content)) as archive:
        assert archive.testzip() is None
        manifest = json.loads(archive.read("MANIFESTO-PACOTE.json"))
        name = manifest["apresentacao"]["arquivo"]
        assert manifest["apresentacao"]["slides"] == 8
        assert archive.read(name) == presentation.content
        assert archive.read("Roteiro_8_Slides.pdf") == guide.content
        assert len([path for path in archive.namelist() if path.endswith(".pptx")]) == 1
        for path, metadata in manifest["arquivos"].items():
            content = archive.read(path)
            assert len(content) == metadata["bytes"]
            assert sha256(content).hexdigest() == metadata["sha256"]
    assert client.get("/api/materials/arquivo-desconhecido").status_code == 404
