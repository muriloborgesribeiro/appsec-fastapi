import json
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.config import METRICAS_PATH
from app.database import get_db
from app.repositories.historico_repo import HistoryRepository
from app.schemas import (
    AlvaradoDetalhe,
    AlvaradoResult,
    DiagnosticoRequest,
    DiagnosticoResponse,
    DiagnosticosListResponse,
    DiagnosticoSummary,
    ErrorResponse,
    KnnResult,
    Link,
    SvmResult,
)
from app.services.ml_service import criar_historico, executar_modelos

router = APIRouter(prefix="/api/v1", tags=["diagnosticos"])


def _build_alvarado(alv: dict) -> AlvaradoResult:
    return AlvaradoResult(
        score=alv.get("score", 0),
        classificacao=alv.get("classificacao", ""),
        label=alv.get("label", ""),
        cor=alv.get("cor", ""),
        interpretacao=alv.get("interpretacao"),
        conduta=alv.get("conduta"),
        disclaimer=alv.get("disclaimer"),
        detalhamento=[AlvaradoDetalhe(**d) for d in alv.get("detalhamento", [])],
    )


def _build_knn(knn: dict) -> KnnResult:
    if "erro" in knn:
        return KnnResult()  # type: ignore[call-arg]
    return KnnResult(
        classe_predita=knn.get("classe_predita"),
        label_predita=knn.get("label_predita"),
        probabilidade_apendicite=knn.get("probabilidade_apendicite"),
        probabilidade_percentual=knn.get("probabilidade_percentual"),
        k_vizinhos=knn.get("k_vizinhos"),
        acuracia_modelo=knn.get("acuracia_modelo"),
        distancia_media_vizinhos=knn.get("distancia_media_vizinhos"),
        confianca=knn.get("confianca"),
        limiar_decisao=knn.get("limiar_decisao"),
        algoritmo=knn.get("algoritmo"),
        referencia_algoritmo=knn.get("referencia_algoritmo"),
        disclaimer=knn.get("disclaimer"),
        features_imputadas=knn.get("features_imputadas", []),
    )


def _build_svm(svm: dict) -> SvmResult:
    if "erro" in svm:
        return SvmResult()  # type: ignore[call-arg]
    return SvmResult(
        classe_predita=svm.get("classe_predita"),
        label_predita=svm.get("label_predita"),
        probabilidade_apendicite=svm.get("probabilidade_apendicite"),
        probabilidade_percentual=svm.get("probabilidade_percentual"),
        kernel=svm.get("kernel"),
        C=svm.get("C"),
        acuracia_modelo=svm.get("acuracia_modelo"),
        confianca=svm.get("confianca"),
        limiar_decisao=svm.get("limiar_decisao"),
        algoritmo=svm.get("algoritmo"),
        referencia_algoritmo=svm.get("referencia_algoritmo"),
        disclaimer=svm.get("disclaimer"),
        features_imputadas=svm.get("features_imputadas", []),
    )


@router.post(
    "/diagnosticos",
    response_model=DiagnosticoResponse,
    status_code=201,
    summary="Criar novo diagnóstico",
    responses={
        201: {"description": "Diagnóstico criado com sucesso"},
        422: {
            "description": "Dados inválidos — campos fora dos limites permitidos",
            "model": ErrorResponse,
        },
        503: {
            "description": "Modelo de ML indisponível",
            "model": ErrorResponse,
        },
    },
)
async def criar_diagnostico(
    payload: DiagnosticoRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "professional")),
):
    """Cria um novo diagnóstico de apendicite.

    Executa os três modelos em cascata:
    1. **Escala de Alvarado** — escore clínico determinístico
    2. **KNN** — K-Nearest Neighbors
    3. **SVM** — Support Vector Machine

    Requer perfil **admin** ou **professional**.
    """
    dados = payload.model_dump()
    resultados = executar_modelos(dados)
    historico = criar_historico(db, dados, resultados)

    return DiagnosticoResponse(  # type: ignore[arg-type]
        id=historico.id,  # type: ignore[arg-type]
        **dados,
        alvarado=_build_alvarado(resultados["alvarado"]),
        knn=_build_knn(resultados["knn"]),
        svm=_build_svm(resultados["svm"]),
        _links=[
            Link(href=f"/api/v1/diagnosticos/{historico.id}", rel="self", method="GET"),
            Link(href="/api/v1/diagnosticos", rel="collection", method="GET"),
        ],
    )


@router.get(
    "/diagnosticos",
    response_model=DiagnosticosListResponse,
    summary="Listar diagnósticos",
    responses={
        200: {"description": "Lista paginada de diagnósticos"},
    },
)
async def listar_diagnosticos(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "professional", "viewer")),
    page: int = Query(1, ge=1, description="Número da página (começa em 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página (máx. 100)"),
    data_inicio: str | None = Query(
        None, description="Filtrar por data início (formato: YYYY-MM-DD)"
    ),
    data_fim: str | None = Query(
        None, description="Filtrar por data fim (formato: YYYY-MM-DD)"
    ),
    classificacao: str | None = Query(
        None, description="Filtrar por classificação Alvarado (ex: Alta Probabilidade)"
    ),
    resultado_knn: str | None = Query(
        None, description="Filtrar por resultado KNN (0 = negativo, 1 = positivo)"
    ),
    resultado_svm: str | None = Query(
        None, description="Filtrar por resultado SVM (0 = negativo, 1 = positivo)"
    ),
):
    """Lista diagnósticos com paginação e filtros.

    Retorna um resumo dos diagnósticos. Para detalhes completos, use o endpoint
    de consulta individual.

    Requer perfil **admin**, **professional** ou **viewer**.
    """
    repo = HistoryRepository(db)
    registros, total = repo.list(
        page=page,
        page_size=page_size,
        data_inicio=data_inicio,
        data_fim=data_fim,
        classificacao=classificacao,
        resultado_knn=resultado_knn,
        resultado_svm=resultado_svm,
    )

    items = [
        DiagnosticoSummary(
            id=r.id,
            created_at=r.created_at.isoformat() if r.created_at else None,
            dor_migratoria=r.dor_migratoria,
            anorexia=r.anorexia,
            nauseas_vomitos=r.nauseas_vomitos,
            dor_fid=r.dor_fid,
            descompressao_dolorosa=r.descompressao_dolorosa,
            temperatura=r.temperatura,
            leucocitos=r.leucocitos,
            neutrofilia=r.neutrofilia,
            alvarado_score=r.alvarado_score,
            alvarado_classificacao=r.alvarado_classificacao,
            predicao_knn=r.predicao_knn,
            probabilidade_knn=r.probabilidade_knn,
            predicao_svm=r.predicao_svm,
            probabilidade_svm=r.probabilidade_svm,
            _links=[
                Link(href=f"/api/v1/diagnosticos/{r.id}", rel="self", method="GET")
            ],
        )
        for r in registros
    ]

    offset = (page - 1) * page_size
    links = [Link(href="/api/v1/diagnosticos", rel="self", method="GET")]
    if page > 1:
        links.append(
            Link(
                href=f"/api/v1/diagnosticos?page={page - 1}&page_size={page_size}",
                rel="prev",
                method="GET",
            )
        )
    if offset + page_size < total:
        links.append(
            Link(
                href=f"/api/v1/diagnosticos?page={page + 1}&page_size={page_size}",
                rel="next",
                method="GET",
            )
        )

    return DiagnosticosListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        _links=links,
    )


@router.get(
    "/diagnosticos/{diagnostico_id}",
    response_model=DiagnosticoResponse,
    summary="Obter diagnóstico por ID",
    responses={
        200: {"description": "Diagnóstico encontrado"},
        404: {
            "description": "Diagnóstico não encontrado",
            "model": ErrorResponse,
        },
    },
)
async def obter_diagnostico(
    diagnostico_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "professional", "viewer")),
):
    """Retorna os detalhes completos de um diagnóstico específico.

    Requer perfil **admin**, **professional** ou **viewer**.
    """
    repo = HistoryRepository(db)
    historico = repo.find_by_id_or_404(diagnostico_id)

    return DiagnosticoResponse(  # type: ignore[arg-type]
        id=historico.id,  # type: ignore[arg-type]
        dor_migratoria=historico.dor_migratoria,  # type: ignore[arg-type]
        anorexia=historico.anorexia,  # type: ignore[arg-type]
        nauseas_vomitos=historico.nauseas_vomitos,  # type: ignore[arg-type]
        dor_fid=historico.dor_fid,  # type: ignore[arg-type]
        descompressao_dolorosa=historico.descompressao_dolorosa,  # type: ignore[arg-type]
        temperatura=historico.temperatura,  # type: ignore[arg-type]
        leucocitos=historico.leucocitos,  # type: ignore[arg-type]
        neutrofilia=historico.neutrofilia,  # type: ignore[arg-type]
        alvarado=AlvaradoResult(
            score=historico.alvarado_score or 0,  # type: ignore[arg-type]
            classificacao=historico.alvarado_classificacao or "",  # type: ignore[arg-type]
            label="",
            cor="",
        ),
        knn=KnnResult(  # type: ignore[call-arg]
            classe_predita=historico.predicao_knn,  # type: ignore[arg-type]
            probabilidade_apendicite=historico.probabilidade_knn,  # type: ignore[arg-type]
            confianca=historico.confianca_knn,  # type: ignore[arg-type]
        ),
        svm=SvmResult(  # type: ignore[call-arg]
            classe_predita=historico.predicao_svm,  # type: ignore[arg-type]
            probabilidade_apendicite=historico.probabilidade_svm,  # type: ignore[arg-type]
            confianca=historico.confianca_svm,  # type: ignore[arg-type]
        ),
        _links=[
            Link(href=f"/api/v1/diagnosticos/{historico.id}", rel="self", method="GET"),
            Link(href="/api/v1/diagnosticos", rel="collection", method="GET"),
        ],
    )


# ── Delete ────────────────────────────────────────────────────
@router.delete(
    "/diagnosticos/{diagnostico_id}",
    status_code=204,
    summary="Remover diagnóstico",
    responses={
        204: {"description": "Diagnóstico removido com sucesso (sem conteúdo)"},
        404: {
            "description": "Diagnóstico não encontrado",
            "model": ErrorResponse,
        },
    },
)
async def deletar_diagnostico(
    diagnostico_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    """Remove um diagnóstico do sistema.

    **Restrito a administradores.** Esta operação é irreversível.
    """
    repo = HistoryRepository(db)
    repo.delete(diagnostico_id)


metricas_router = APIRouter(prefix="/api/v1", tags=["metricas"])


@metricas_router.get(
    "/metricas",
    summary="Obter métricas dos modelos ML",
    responses={
        200: {"description": "Métricas de desempenho dos modelos"},
        404: {
            "description": "Arquivo de métricas não encontrado",
            "model": ErrorResponse,
        },
    },
)
async def metricas_json(
    _=Depends(require_role("admin", "professional", "viewer")),
):
    """Retorna as métricas de desempenho dos modelos KNN e SVM.

    As métricas incluem acurácia, precisão, recall, F1-score e matriz de confusão.
    Execute `python pipeline.py` para gerar/atualizar as métricas.

    Requer perfil **admin**, **professional** ou **viewer**.
    """
    if not os.path.exists(METRICAS_PATH):
        raise HTTPException(
            status_code=404,
            detail="Métricas não encontradas. Execute setup.py primeiro.",
        )
    with open(METRICAS_PATH, encoding="utf-8") as f:
        return json.load(f)
