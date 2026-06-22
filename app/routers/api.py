import os
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.repositories.historico_repo import HistoryRepository
from app.config import METRICAS_PATH
from app.schemas import (
    DiagnosticoRequest, DiagnosticoResponse, DiagnosticoSummary,
    DiagnosticosListResponse, Link, ErrorResponse,
    AlvaradoResult, AlvaradoDetalhe, KnnResult, SvmResult,
)
from app.services.ml_service import executar_modelos, criar_historico
from app.auth.dependencies import require_role

router = APIRouter(prefix="/api/v1", tags=["api"])


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
        return KnnResult()
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
        return SvmResult()
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
    responses={
        201: {"description": "Diagnóstico criado com sucesso"},
        422: {"model": ErrorResponse, "description": "Dados inválidos"},
        503: {"model": ErrorResponse, "description": "Modelo ML indisponível"},
    },
)
async def criar_diagnostico(
    payload: DiagnosticoRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "professional")),
):
    dados = payload.model_dump()
    resultados = executar_modelos(dados)
    historico = criar_historico(db, dados, resultados)

    return DiagnosticoResponse(
        id=historico.id,
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
    responses={200: {"description": "Lista de diagnósticos"}},
)
async def listar_diagnosticos(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "professional", "viewer")),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    data_inicio: Optional[str] = Query(None, description="Filtrar por data início (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Filtrar por data fim (YYYY-MM-DD)"),
    classificacao: Optional[str] = Query(None, description="Filtrar por classificação Alvarado"),
    resultado_knn: Optional[str] = Query(None, description="Filtrar por resultado KNN (0/1)"),
    resultado_svm: Optional[str] = Query(None, description="Filtrar por resultado SVM (0/1)"),
):
    repo = HistoryRepository(db)
    registros, total = repo.list(
        page=page, page_size=page_size,
        data_inicio=data_inicio, data_fim=data_fim,
        classificacao=classificacao,
        resultado_knn=resultado_knn, resultado_svm=resultado_svm,
    )

    items = [
        DiagnosticoSummary(
            id=r.id,
            created_at=r.created_at.isoformat() if r.created_at else None,
            alvarado_score=r.alvarado_score,
            alvarado_classificacao=r.alvarado_classificacao,
            predicao_knn=r.predicao_knn,
            probabilidade_knn=r.probabilidade_knn,
            predicao_svm=r.predicao_svm,
            probabilidade_svm=r.probabilidade_svm,
            _links=[Link(href=f"/api/v1/diagnosticos/{r.id}", rel="self", method="GET")],
        )
        for r in registros
    ]

    offset = (page - 1) * page_size
    links = [Link(href="/api/v1/diagnosticos", rel="self", method="GET")]
    if page > 1:
        links.append(Link(href=f"/api/v1/diagnosticos?page={page - 1}&page_size={page_size}", rel="prev", method="GET"))
    if offset + page_size < total:
        links.append(Link(href=f"/api/v1/diagnosticos?page={page + 1}&page_size={page_size}", rel="next", method="GET"))

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
    responses={
        200: {"description": "Diagnóstico encontrado"},
        404: {"model": ErrorResponse, "description": "Diagnóstico não encontrado"},
    },
)
async def obter_diagnostico(
    diagnostico_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin", "professional", "viewer")),
):
    repo = HistoryRepository(db)
    historico = repo.find_by_id_or_404(diagnostico_id)

    return DiagnosticoResponse(
        id=historico.id,
        alvarado=AlvaradoResult(
            score=historico.alvarado_score or 0,
            classificacao=historico.alvarado_classificacao or "",
            label="",
            cor="",
        ),
        knn=KnnResult(
            classe_predita=historico.predicao_knn,
            probabilidade_apendicite=historico.probabilidade_knn,
            confianca=historico.confianca_knn,
        ),
        svm=SvmResult(
            classe_predita=historico.predicao_svm,
            probabilidade_apendicite=historico.probabilidade_svm,
            confianca=historico.confianca_svm,
        ),
        _links=[
            Link(href=f"/api/v1/diagnosticos/{historico.id}", rel="self", method="GET"),
            Link(href="/api/v1/diagnosticos", rel="collection", method="GET"),
        ],
    )


@router.delete(
    "/diagnosticos/{diagnostico_id}",
    status_code=204,
    responses={
        204: {"description": "Diagnóstico removido"},
        404: {"model": ErrorResponse, "description": "Diagnóstico não encontrado"},
    },
)
async def deletar_diagnostico(
    diagnostico_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    repo = HistoryRepository(db)
    repo.delete(diagnostico_id)


@router.get(
    "/metricas",
    responses={
        200: {"description": "Métricas dos modelos"},
        404: {"model": ErrorResponse, "description": "Métricas não encontradas"},
    },
)
async def metricas_json(
    _=Depends(require_role("admin", "professional", "viewer")),
):
    if not os.path.exists(METRICAS_PATH):
        raise HTTPException(
            status_code=404,
            detail="Métricas não encontradas. Execute setup.py primeiro.",
        )
    with open(METRICAS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
