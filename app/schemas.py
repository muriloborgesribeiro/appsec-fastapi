from pydantic import BaseModel, Field
from typing import Optional


# ── Request ─────────────────────────────────────────────────


class DiagnosticoRequest(BaseModel):
    dor_migratoria: bool = Field(..., description="Dor migratória para FID")
    anorexia: bool = Field(..., description="Perda de apetite")
    nauseas_vomitos: bool = Field(..., description="Náuseas ou vômitos")
    dor_fid: bool = Field(..., description="Dor à palpação em FID")
    descompressao_dolorosa: bool = Field(..., description="Sinal de Blumberg")
    temperatura: float = Field(
        ..., ge=35.0, le=42.0, description="Temperatura axilar em °C"
    )
    leucocitos: float = Field(
        ..., ge=1000, le=50000, description="Leucócitos totais /mm³"
    )
    neutrofilia: bool = Field(..., description="Neutrofilia (>75%)")


# ── HATEOAS ─────────────────────────────────────────────────


class Link(BaseModel):
    href: str
    rel: str
    method: str = "GET"


# ── Alvarado ────────────────────────────────────────────────


class AlvaradoDetalhe(BaseModel):
    criterio: str
    criterio_completo: str
    presente: bool
    pontos: int
    pontos_max: int
    categoria: str
    referencia: str


class AlvaradoResult(BaseModel):
    score: int
    classificacao: str
    label: str
    cor: str
    interpretacao: Optional[str] = None
    conduta: Optional[str] = None
    disclaimer: Optional[str] = None
    detalhamento: list[AlvaradoDetalhe] = []


# ── KNN ─────────────────────────────────────────────────────


class KnnResult(BaseModel):
    classe_predita: Optional[int] = None
    label_predita: Optional[str] = None
    probabilidade_apendicite: Optional[float] = None
    probabilidade_percentual: Optional[str] = None
    k_vizinhos: Optional[int] = None
    acuracia_modelo: Optional[float] = None
    distancia_media_vizinhos: Optional[float] = None
    confianca: Optional[str] = None
    limiar_decisao: Optional[float] = None
    algoritmo: Optional[str] = None
    referencia_algoritmo: Optional[str] = None
    disclaimer: Optional[str] = None
    features_imputadas: list[str] = []


# ── SVM ─────────────────────────────────────────────────────


class SvmResult(BaseModel):
    classe_predita: Optional[int] = None
    label_predita: Optional[str] = None
    probabilidade_apendicite: Optional[float] = None
    probabilidade_percentual: Optional[str] = None
    kernel: Optional[str] = None
    C: Optional[float] = None
    acuracia_modelo: Optional[float] = None
    confianca: Optional[str] = None
    limiar_decisao: Optional[float] = None
    algoritmo: Optional[str] = None
    referencia_algoritmo: Optional[str] = None
    disclaimer: Optional[str] = None
    features_imputadas: list[str] = []


# ── Responses ───────────────────────────────────────────────


class DiagnosticoResponse(BaseModel):
    id: int
    dor_migratoria: bool
    anorexia: bool
    nauseas_vomitos: bool
    dor_fid: bool
    descompressao_dolorosa: bool
    temperatura: float
    leucocitos: float
    neutrofilia: bool
    alvarado: AlvaradoResult
    knn: KnnResult
    svm: SvmResult
    _links: list[Link] = []


class DiagnosticoSummary(BaseModel):
    id: int
    created_at: Optional[str] = None
    dor_migratoria: Optional[bool] = None
    anorexia: Optional[bool] = None
    nauseas_vomitos: Optional[bool] = None
    dor_fid: Optional[bool] = None
    descompressao_dolorosa: Optional[bool] = None
    temperatura: Optional[float] = None
    leucocitos: Optional[float] = None
    neutrofilia: Optional[bool] = None
    alvarado_score: Optional[int] = None
    alvarado_classificacao: Optional[str] = None
    predicao_knn: Optional[int] = None
    probabilidade_knn: Optional[float] = None
    predicao_svm: Optional[int] = None
    probabilidade_svm: Optional[float] = None
    _links: list[Link] = []


class DiagnosticosListResponse(BaseModel):
    items: list[DiagnosticoSummary]
    total: int
    page: int
    page_size: int
    _links: list[Link] = []


# ── Errors ──────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    detail: str
