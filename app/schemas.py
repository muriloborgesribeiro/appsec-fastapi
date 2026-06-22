from pydantic import BaseModel, Field

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
    interpretacao: str | None = None
    conduta: str | None = None
    disclaimer: str | None = None
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

    classe_predita: int | None = Field(
        None, description="Classe predita (0 = negativo, 1 = positivo)"
    )
    label_predita: str | None = Field(None, description="Rótulo da classe predita")
    probabilidade_apendicite: float | None = Field(
        None, description="Probabilidade de apendicite (0 a 1)"
    )
    probabilidade_percentual: str | None = Field(
        None, description="Probabilidade formatada em percentual"
    )
    k_vizinhos: int | None = Field(
        None, description="Número de vizinhos considerados (k)"
    )
    acuracia_modelo: float | None = Field(
        None, description="Acurácia do modelo nos dados de validação"
    )
    distancia_media_vizinhos: float | None = Field(
        None, description="Distância média aos k vizinhos mais próximos"
    )
    confianca: str | None = Field(None, description="Nível de confiança da predição")
    limiar_decisao: float | None = Field(
        None, description="Limiar de decisão utilizado"
    )
    algoritmo: str | None = Field(None, description="Nome do algoritmo")
    referencia_algoritmo: str | None = Field(
        None, description="Referência bibliográfica do algoritmo"
    )
    disclaimer: str | None = None
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

    classe_predita: int | None = Field(
        None, description="Classe predita (0 = negativo, 1 = positivo)"
    )
    label_predita: str | None = Field(None, description="Rótulo da classe predita")
    probabilidade_apendicite: float | None = Field(
        None, description="Probabilidade de apendicite (0 a 1)"
    )
    probabilidade_percentual: str | None = Field(
        None, description="Probabilidade formatada em percentual"
    )
    kernel: str | None = Field(
        None, description="Função kernel utilizada (rbf, linear, polynomial)"
    )
    C: float | None = Field(None, description="Parâmetro de regularização do SVM")
    acuracia_modelo: float | None = Field(
        None, description="Acurácia do modelo nos dados de validação"
    )
    confianca: str | None = Field(None, description="Nível de confiança da predição")
    limiar_decisao: float | None = Field(
        None, description="Limiar de decisão utilizado"
    )
    algoritmo: str | None = Field(None, description="Nome do algoritmo")
    referencia_algoritmo: str | None = Field(
        None, description="Referência bibliográfica do algoritmo"
    )
    disclaimer: str | None = None
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
    created_at: str | None = None
    dor_migratoria: bool | None = None
    anorexia: bool | None = None
    nauseas_vomitos: bool | None = None
    dor_fid: bool | None = None
    descompressao_dolorosa: bool | None = None
    temperatura: float | None = None
    leucocitos: float | None = None
    neutrofilia: bool | None = None
    alvarado_score: int | None = None
    alvarado_classificacao: str | None = None
    predicao_knn: int | None = None
    probabilidade_knn: float | None = None
    predicao_svm: int | None = None
    probabilidade_svm: float | None = None
    _links: list[Link] = []


class DiagnosticosListResponse(BaseModel):
    """Lista paginada de diagnósticos."""

    items: list[DiagnosticoSummary]
    total: int
    page: int
    page_size: int
    _links: list[Link] = []


# ── Duvidas (RAG) ────────────────────────────────────────────


class DuvidaRequest(BaseModel):
    """Pergunta do usuario sobre o projeto."""

    pergunta: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Pergunta sobre o projeto em portugues",
    )

    model_config = {
        "json_schema_extra": {
            "example": {"pergunta": "Como o escore de Alvarado classifica o risco?"}
        }
    }


class DuvidaResponse(BaseModel):
    """Resposta gerada pela LLM com base na documentacao do projeto."""

    pergunta: str
    resposta: str
    contexto_utilizado: list[str] = []
    modelo: str


# ── Errors ──────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Resposta de erro padronizada."""

    detail: str
