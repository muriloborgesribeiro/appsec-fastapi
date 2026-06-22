from pydantic import BaseModel, Field
from typing import Optional


# ── Request ─────────────────────────────────────────────────


class DiagnosticoRequest(BaseModel):
    """Parâmetros clínicos para realização do diagnóstico de apendicite."""

    dor_migratoria: bool = Field(
        ..., description="Dor migratória para fossa ilíaca direita (FID)"
    )
    anorexia: bool = Field(..., description="Perda de apetite / anorexia")
    nauseas_vomitos: bool = Field(..., description="Náuseas ou vômitos")
    dor_fid: bool = Field(
        ..., description="Dor à palpação em fossa ilíaca direita (FID)"
    )
    descompressao_dolorosa: bool = Field(
        ..., description="Sinal de Blumberg (descompressão dolorosa)"
    )
    temperatura: float = Field(
        ..., ge=35.0, le=42.0, description="Temperatura axilar em °C"
    )
    leucocitos: float = Field(
        ..., ge=1000, le=50000, description="Leucócitos totais (/mm³)"
    )
    neutrofilia: bool = Field(
        ..., description="Neutrofilia (>75%) — desvio para esquerda"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "dor_migratoria": True,
                "anorexia": True,
                "nauseas_vomitos": False,
                "dor_fid": True,
                "descompressao_dolorosa": True,
                "temperatura": 38.5,
                "leucocitos": 14500,
                "neutrofilia": True,
            }
        }
    }


# ── HATEOAS ─────────────────────────────────────────────────


class Link(BaseModel):
    """Link HATEOAS para navegação entre recursos."""

    href: str
    rel: str
    method: str = "GET"


# ── Alvarado ────────────────────────────────────────────────


class AlvaradoDetalhe(BaseModel):
    """Detalhamento de um critério da Escala de Alvarado."""

    criterio: str
    criterio_completo: str
    presente: bool
    pontos: int
    pontos_max: int
    categoria: str
    referencia: str


class AlvaradoResult(BaseModel):
    """Resultado do Escore de Alvarado (determinístico)."""

    score: int
    classificacao: str
    label: str
    cor: str
    interpretacao: Optional[str] = None
    conduta: Optional[str] = None
    disclaimer: Optional[str] = None
    detalhamento: list[AlvaradoDetalhe] = []

    model_config = {
        "json_schema_extra": {
            "example": {
                "score": 8,
                "classificacao": "Alta Probabilidade",
                "label": "Alta",
                "cor": "#dc3545",
                "interpretacao": "Probabilidade elevada de apendicite aguda",
                "conduta": "Encaminhamento cirúrgico",
                "disclaimer": "Este escore não substitui avaliação clínica",
                "detalhamento": [
                    {
                        "criterio": "Dor migratória",
                        "criterio_completo": "Dor migratória para FID",
                        "presente": True,
                        "pontos": 1,
                        "pontos_max": 1,
                        "categoria": "Sintomas",
                        "referencia": "Alvarado 1986",
                    }
                ],
            }
        }
    }


# ── KNN ─────────────────────────────────────────────────────


class KnnResult(BaseModel):
    """Resultado da predição do modelo KNN (K-Nearest Neighbors)."""

    classe_predita: Optional[int] = Field(
        None, description="Classe predita (0 = negativo, 1 = positivo)"
    )
    label_predita: Optional[str] = Field(None, description="Rótulo da classe predita")
    probabilidade_apendicite: Optional[float] = Field(
        None, description="Probabilidade de apendicite (0 a 1)"
    )
    probabilidade_percentual: Optional[str] = Field(
        None, description="Probabilidade formatada em percentual"
    )
    k_vizinhos: Optional[int] = Field(
        None, description="Número de vizinhos considerados (k)"
    )
    acuracia_modelo: Optional[float] = Field(
        None, description="Acurácia do modelo nos dados de validação"
    )
    distancia_media_vizinhos: Optional[float] = Field(
        None, description="Distância média aos k vizinhos mais próximos"
    )
    confianca: Optional[str] = Field(None, description="Nível de confiança da predição")
    limiar_decisao: Optional[float] = Field(
        None, description="Limiar de decisão utilizado"
    )
    algoritmo: Optional[str] = Field(None, description="Nome do algoritmo")
    referencia_algoritmo: Optional[str] = Field(
        None, description="Referência bibliográfica do algoritmo"
    )
    disclaimer: Optional[str] = None
    features_imputadas: list[str] = []

    model_config = {
        "json_schema_extra": {
            "example": {
                "classe_predita": 1,
                "label_predita": "Positivo",
                "probabilidade_apendicite": 0.92,
                "probabilidade_percentual": "92.0%",
                "k_vizinhos": 5,
                "acuracia_modelo": 0.89,
                "distancia_media_vizinhos": 0.35,
                "confianca": "Alta",
                "limiar_decisao": 0.5,
                "algoritmo": "K-Nearest Neighbors",
                "referencia_algoritmo": "Cover & Hart (1967)",
                "features_imputadas": [],
            }
        }
    }


# ── SVM ─────────────────────────────────────────────────────


class SvmResult(BaseModel):
    """Resultado da predição do modelo SVM (Support Vector Machine)."""

    classe_predita: Optional[int] = Field(
        None, description="Classe predita (0 = negativo, 1 = positivo)"
    )
    label_predita: Optional[str] = Field(None, description="Rótulo da classe predita")
    probabilidade_apendicite: Optional[float] = Field(
        None, description="Probabilidade de apendicite (0 a 1)"
    )
    probabilidade_percentual: Optional[str] = Field(
        None, description="Probabilidade formatada em percentual"
    )
    kernel: Optional[str] = Field(
        None, description="Função kernel utilizada (rbf, linear, polynomial)"
    )
    C: Optional[float] = Field(None, description="Parâmetro de regularização do SVM")
    acuracia_modelo: Optional[float] = Field(
        None, description="Acurácia do modelo nos dados de validação"
    )
    confianca: Optional[str] = Field(None, description="Nível de confiança da predição")
    limiar_decisao: Optional[float] = Field(
        None, description="Limiar de decisão utilizado"
    )
    algoritmo: Optional[str] = Field(None, description="Nome do algoritmo")
    referencia_algoritmo: Optional[str] = Field(
        None, description="Referência bibliográfica do algoritmo"
    )
    disclaimer: Optional[str] = None
    features_imputadas: list[str] = []

    model_config = {
        "json_schema_extra": {
            "example": {
                "classe_predita": 1,
                "label_predita": "Positivo",
                "probabilidade_apendicite": 0.87,
                "probabilidade_percentual": "87.0%",
                "kernel": "rbf",
                "C": 1.0,
                "acuracia_modelo": 0.91,
                "confianca": "Alta",
                "limiar_decisao": 0.5,
                "algoritmo": "Support Vector Machine",
                "referencia_algoritmo": "Vapnik (1995)",
                "features_imputadas": [],
            }
        }
    }


# ── Responses ───────────────────────────────────────────────


class DiagnosticoResponse(BaseModel):
    """Resposta completa de um diagnóstico, incluindo resultados dos três modelos."""

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
    """Resumo de um diagnóstico para exibição em listas."""

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
    """Lista paginada de diagnósticos."""

    items: list[DiagnosticoSummary]
    total: int
    page: int
    page_size: int
    _links: list[Link] = []


# ── Errors ──────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Resposta de erro padronizada."""

    detail: str
