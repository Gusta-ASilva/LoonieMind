"""API e interface local, servidas pela mesma origem. Contrato em /api/docs."""
from contextlib import asynccontextmanager
from datetime import date
import io
import json
import logging
from typing import Literal
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, File, Form, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import __version__
from .db import Database, ROOT
from .domain import DomainError
from .imports import ImportService, MAX_BYTES
from .models import ForecastService, ModelService
from .services import FinanceService

logger = logging.getLogger("looniemind")
MATERIALS_DIR = ROOT / "outputs" / "looniemind-v11-20261027"
PRESENTATION_DIR = ROOT / "outputs" / "looniemind-apresentacao-8-slides"
MATERIALS = {
    "manual": ("Manual do sistema e IA", MATERIALS_DIR / "Manual_Sistema_e_IA_LoonieMind.pdf"),
    "roteiro": ("Roteiro de apresentação · 4min35s", PRESENTATION_DIR / "Roteiro_8_Slides.pdf"),
    "apresentacao": ("PowerPoint · 8 slides", PRESENTATION_DIR / "LoonieMind_Empresa_e_Sistema_8_Slides.pptx"),
    "pacote": ("Pacote completo de materiais atualizados", MATERIALS_DIR / "LoonieMind_Materiais_Completos.zip"),
    "base": ("Base sintética · 25.365 registros", ROOT / "datasets" / "sintetica-v2" / "Base_Sintetica_LoonieMind.zip"),
    "modelo": ("Modelo completo de importação", MATERIALS_DIR / "Modelo_Importacao_LoonieMind.xlsx"),
    "relatorio": ("Relatório de demonstração", MATERIALS_DIR / "Relatorio_Demonstracao_LoonieMind.xlsx"),
    "projecao": ("Projeção de demonstração", MATERIALS_DIR / "Projecao_Demonstracao_LoonieMind.xlsx"),
}


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CompanyPayload(Payload):
    nome: str = Field(min_length=2, max_length=100)
    descricao: str = Field(default="", max_length=300)
    saldo_inicial_centavos: int = Field(default=0, strict=True, ge=-100_000_000_000_000, le=100_000_000_000_000)
    data_saldo: date = Field(default_factory=lambda: date.today().replace(month=1, day=1))

    @field_validator("data_saldo")
    @classmethod
    def past_date(cls, value):
        if value > date.today() or value.year < 1900:
            raise ValueError("A referência do saldo deve ser uma data passada ou hoje, a partir de 1900.")
        return value


class TransactionPayload(Payload):
    descricao: str = Field(min_length=1, max_length=250)
    categoria: str = Field(min_length=1, max_length=80)
    valor_centavos: int = Field(strict=True, gt=0, le=100_000_000_000_000)
    data: date
    tipo: Literal[1, 2]
    documento: str = Field(default="", max_length=80)
    contraparte: str = Field(default="", max_length=120)
    centro_custo: str = Field(default="", max_length=80)
    conta: str = Field(default="", max_length=80)
    forma_pagamento: str = Field(default="", max_length=60)
    competencia: str = Field(default="", max_length=10)
    observacoes: str = Field(default="", max_length=500)
    id_externo: str = Field(default="", max_length=100)

    @field_validator("data")
    @classmethod
    def actual_date(cls, value):
        return CompanyPayload.past_date(value)


class CategoryPayload(Payload):
    nome: str = Field(min_length=2, max_length=80)
    tipo: Literal[1, 2]


class ImportOptions(Payload):
    mapping: dict[str, str] | None = None
    sheet: str | None = Field(default=None, max_length=100)
    header_row: int = Field(default=0, ge=0, le=20)
    decimal_format: Literal["auto", "br", "us"] = "auto"
    day_first: bool = True
    signed_values: bool = False
    encoding: Literal["auto", "utf-8-sig", "cp1252"] = "auto"
    separator: Literal[",", ";", "\t", "|"] | None = None


class ConfirmPayload(Payload):
    permitir_parcial: bool = False
    manter_semelhantes: bool = False


class AcceptPayload(Payload):
    ids: list[int] = Field(min_length=1, max_length=500)


class TrainingPayload(Payload):
    fonte: Literal["reviewed", "synthetic"] = "reviewed"


def query_filters(inicio: date | None = None, fim: date | None = None, tipo: int | None = Query(default=None, ge=1, le=2),
                  categoria: str | None = Query(default=None, max_length=80),
                  busca: str | None = Query(default=None, max_length=100), pendentes: bool = False):
    if inicio and fim and inicio > fim:
        raise DomainError("A data inicial deve ser anterior à data final.")
    return {"inicio": inicio.isoformat() if inicio else None, "fim": fim.isoformat() if fim else None,
            "tipo": tipo, "categoria": categoria, "busca": busca, "pendentes": pendentes}


def create_app(data_dir=None):
    db = Database(data_dir)
    models, forecasts = ModelService(db), ForecastService(db)
    imports = ImportService(db)
    finance = FinanceService(db, models, forecasts)

    @asynccontextmanager
    async def lifespan(application):
        db.initialize()
        yield

    application = FastAPI(title="LoonieMind API", version=__version__, lifespan=lifespan,
                          docs_url=None, redoc_url=None, openapi_url="/api/openapi.json")
    application.state.db = db
    application.state.finance = finance
    application.state.models = models
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])

    @application.middleware("http")
    async def local_boundary(request: Request, call_next):
        origin = request.headers.get("origin")
        if request.method not in {"GET", "HEAD", "OPTIONS"} and origin:
            origin_url = urlsplit(origin)
            if origin_url.scheme != request.url.scheme or origin_url.netloc != request.headers.get("host"):
                return JSONResponse({"mensagem": "A operação deve ser feita pela interface local do LoonieMind."}, 403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse({"mensagem": exc.message, "detalhes": exc.details}, status_code=exc.status)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        errors = [{"campo": ".".join(map(str, item["loc"])), "mensagem": item["msg"]} for item in exc.errors()]
        return JSONResponse({"mensagem": "Confira os campos informados.", "detalhes": errors}, status_code=422)

    @application.exception_handler(Exception)
    async def unexpected_error(request, exc):
        logger.error("Falha interna em %s: %s", request.url.path, type(exc).__name__)
        return JSONResponse({"mensagem": "Não foi possível concluir a operação. Tente novamente e consulte o terminal se o problema persistir."}, 500)

    @application.get("/api/health", tags=["Sistema"])
    def health():
        with db.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "aplicacao": "LoonieMind", "versao": __version__, "modo": "local", "moeda": "BRL"}

    @application.get("/api/companies", tags=["Empresas"])
    def companies():
        with db.connect() as conn:
            return [dict(r) for r in conn.execute("""SELECT e.*, (SELECT count(*) FROM Lancamentos l WHERE l.id_empresa=e.id_empresa)
                AS total_lancamentos FROM Empresas e ORDER BY demo,nome""")]

    @application.post("/api/companies", status_code=201, tags=["Empresas"])
    def create_company(payload: CompanyPayload):
        return finance.create_company(payload.nome, payload.descricao, payload.saldo_inicial_centavos, payload.data_saldo.isoformat())

    @application.put("/api/companies/{company_id}", tags=["Empresas"])
    def update_company(company_id: int, payload: CompanyPayload):
        return finance.update_company(company_id, payload.model_dump(mode="json"))

    @application.post("/api/demo", tags=["Demonstração"])
    def demo():
        """Cria uma empresa fictícia isolada, com histórico sintético e classificador demonstrativo."""
        return finance.seed_demo()

    @application.post("/api/demo/expanded", tags=["Demonstração"])
    def expanded_demo():
        return finance.seed_expanded_demo()

    @application.get("/api/companies/{company_id}/categories", tags=["Empresas"])
    def categories(company_id: int):
        with db.connect() as conn:
            return db.categories(conn, company_id)

    @application.post("/api/companies/{company_id}/categories", status_code=201, tags=["Empresas"])
    def category(company_id: int, payload: CategoryPayload):
        if payload.nome == "Sem categoria":
            raise DomainError("Este nome é reservado para lançamentos pendentes.")
        with db.connect(write=True) as conn:
            db.company(conn, company_id)
            conn.execute("INSERT OR IGNORE INTO Categorias(id_empresa,nome,tipo) VALUES(?,?,?)", (company_id, payload.nome, payload.tipo))
            db.audit(conn, company_id, "criar_categoria", "categoria", payload.nome, {"tipo": payload.tipo})
            return db.categories(conn, company_id)

    @application.get("/api/companies/{company_id}/summary", tags=["Indicadores"])
    def summary(company_id: int, periodo: Literal["month", "30d", "90d", "year", "all"] = "month"):
        return finance.summary(company_id, periodo)

    @application.get("/api/companies/{company_id}/transactions", tags=["Lançamentos"])
    def transactions(company_id: int, filtros: dict = Depends(query_filters), pagina: int = Query(1, ge=1),
                     por_pagina: int = Query(20, ge=1, le=100)):
        return finance.transactions(company_id, filtros, pagina, por_pagina)

    @application.post("/api/companies/{company_id}/transactions", status_code=201, tags=["Lançamentos"])
    def create_transaction(company_id: int, payload: TransactionPayload):
        return finance.save_transaction(company_id, payload.model_dump(mode="json"))

    @application.put("/api/companies/{company_id}/transactions/{transaction_id}", tags=["Lançamentos"])
    def update_transaction(company_id: int, transaction_id: int, payload: TransactionPayload):
        return finance.save_transaction(company_id, payload.model_dump(mode="json", exclude_unset=True), transaction_id)

    @application.delete("/api/companies/{company_id}/transactions/{transaction_id}", tags=["Lançamentos"])
    def delete_transaction(company_id: int, transaction_id: int):
        return finance.delete_transaction(company_id, transaction_id)

    @application.get("/api/companies/{company_id}/imports", tags=["Importação"])
    def list_imports(company_id: int):
        with db.connect() as conn:
            db.company(conn, company_id)
            return [dict(r) for r in conn.execute("""SELECT id_planilha,nome,aba,status,total_linhas,importados,rejeitados,created_at
                FROM Planilhas WHERE id_empresa=? ORDER BY created_at DESC LIMIT 50""", (company_id,))]

    @application.post("/api/companies/{company_id}/imports", status_code=201, tags=["Importação"])
    async def upload(company_id: int, arquivo: UploadFile = File(...), opcoes: str = Form("{}")):
        try:
            parsed = ImportOptions.model_validate_json(opcoes).model_dump(exclude_none=True)
        except ValueError as exc:
            raise DomainError("Opções de importação inválidas.") from exc
        content = await arquivo.read(MAX_BYTES + 1)
        await arquivo.close()
        return await run_in_threadpool(imports.create, company_id, arquivo.filename or "", content, parsed)

    @application.post("/api/companies/{company_id}/imports/{import_id}/preview", tags=["Importação"])
    def preview(company_id: int, import_id: str, payload: ImportOptions):
        return imports.preview(company_id, import_id, payload.model_dump(exclude_unset=True))

    @application.post("/api/companies/{company_id}/imports/{import_id}/confirm", tags=["Importação"])
    def confirm(company_id: int, import_id: str, payload: ConfirmPayload):
        return imports.confirm(company_id, import_id, payload.permitir_parcial, payload.manter_semelhantes)

    @application.post("/api/companies/{company_id}/imports/{import_id}/undo", tags=["Importação"])
    def undo(company_id: int, import_id: str):
        return imports.undo(company_id, import_id)

    @application.get("/api/companies/{company_id}/model", tags=["Aprendizado de máquina"])
    def model_status(company_id: int):
        with db.connect() as conn:
            db.company(conn, company_id)
            reviewed = conn.execute("SELECT count(*) FROM Lancamentos WHERE id_empresa=? AND revisado=1", (company_id,)).fetchone()[0]
        return {**models.status(company_id), "revisados_disponiveis": reviewed}

    @application.post("/api/companies/{company_id}/model/train", tags=["Aprendizado de máquina"])
    def train(company_id: int, payload: TrainingPayload):
        return models.train(company_id, payload.fonte)

    @application.post("/api/companies/{company_id}/classify", tags=["Aprendizado de máquina"])
    def classify(company_id: int):
        return finance.classify(company_id)

    @application.post("/api/companies/{company_id}/classify/accept", tags=["Aprendizado de máquina"])
    def accept(company_id: int, payload: AcceptPayload):
        return finance.accept_suggestions(company_id, payload.ids)

    @application.get("/api/companies/{company_id}/forecast", tags=["Previsão"])
    def forecast(company_id: int, dias: int = Query(30, ge=7, le=90)):
        if dias not in {7, 30, 60, 90}:
            raise DomainError("Escolha um horizonte de 7, 30, 60 ou 90 dias.", 422)
        return forecasts.calculate(company_id, dias)

    @application.get("/api/companies/{company_id}/export", tags=["Exportação"])
    def export(company_id: int, formato: Literal["csv", "xlsx"] = "csv", filtros: dict = Depends(query_filters)):
        content = finance.export(company_id, filtros, formato)
        media = "text/csv; charset=utf-8" if formato == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return Response(content, media_type=media, headers={"Content-Disposition": f'attachment; filename="looniemind-lancamentos-{date.today()}.{formato}"'})

    @application.get("/api/companies/{company_id}/forecast/export", tags=["Exportação"])
    def export_forecast(company_id: int, dias: int = Query(30, ge=7, le=90), formato: Literal["csv", "xlsx"] = "csv"):
        if dias not in {7, 30, 60, 90}:
            raise DomainError("Escolha um horizonte de 7, 30, 60 ou 90 dias.", 422)
        result = forecasts.calculate(company_id, dias)
        if not result["disponivel"]:
            raise DomainError(result["motivo"], 409)
        import csv
        from decimal import Decimal
        headers = ["Data", "Receitas previstas (R$)", "Despesas previstas (R$)", "Saldo previsto (R$)", "Método", "Dados sintéticos"]
        rows = [[r["data"], Decimal(r["receitas_centavos"]) / 100, Decimal(r["despesas_centavos"]) / 100,
                 Decimal(r["saldo_centavos"]) / 100, result["metodo"], "Sim" if result["sintetico"] else "Não"] for r in result["serie"]]
        if formato == "csv":
            buffer = io.StringIO(newline="")
            writer = csv.writer(buffer, delimiter=";")
            writer.writerow(headers)
            for row in rows:
                writer.writerow([str(v).replace(".", ",") if isinstance(v, Decimal) else v for v in row])
            content = buffer.getvalue().encode("utf-8-sig")
        else:
            from .workbooks import forecast_report
            content = forecast_report(result, finance.get_company(company_id))
        media = "text/csv; charset=utf-8" if formato == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return Response(content, media_type=media, headers={"Content-Disposition": f'attachment; filename="looniemind-previsao-{dias}dias.{formato}"'})

    @application.get("/api/template", tags=["Importação"])
    def template(formato: Literal["csv", "xlsx"] = "csv"):
        from .workbooks import import_template
        content = import_template(formato)
        return Response(content, media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="modelo-looniemind.{formato}"'})

    @application.get("/api/companies/{company_id}/audit", tags=["Auditoria"])
    def audit(company_id: int):
        with db.connect() as conn:
            db.company(conn, company_id)
            rows = [dict(r) for r in conn.execute("SELECT * FROM Auditoria WHERE id_empresa=? ORDER BY id DESC LIMIT 100", (company_id,))]
        for row in rows:
            row["detalhes"] = json.loads(row["detalhes"])
        return rows

    @application.get("/api/backup", tags=["Sistema"])
    def backup():
        return Response(finance.backup(), media_type="application/zip",
                        headers={"Content-Disposition": f'attachment; filename="looniemind-backup-{date.today()}.zip"'})

    @application.get("/api/materials", tags=["Sistema"])
    def materials():
        return [{"id": key, "nome": name, "formato": path.suffix.lstrip("."), "url": f"/api/materials/{key}"}
                for key, (name, path) in MATERIALS.items() if path.is_file()]

    @application.get("/api/materials/{key}", tags=["Sistema"])
    def material(key: str):
        selected = MATERIALS.get(key)
        if not selected or not selected[1].is_file():
            raise DomainError("Material não encontrado nesta instalação.", 404)
        return FileResponse(selected[1], filename=selected[1].name)

    @application.get("/", include_in_schema=False)
    def index():
        return FileResponse(ROOT / "web" / "index.html", headers={"Cache-Control": "no-cache"})

    @application.get("/api/docs", include_in_schema=False)
    def api_reference():
        return FileResponse(ROOT / "web" / "api.html")

    application.mount("/assets", StaticFiles(directory=ROOT / "web"), name="assets")
    return application


app = create_app()
