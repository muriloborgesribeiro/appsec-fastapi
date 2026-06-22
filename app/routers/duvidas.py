from fastapi import APIRouter, Depends, HTTPException
from openai import APITimeoutError

from app.auth.dependencies import require_role
from app.config import GROQ_MODEL
from app.schemas import DuvidaRequest, DuvidaResponse, ErrorResponse
from app.services.llm_service import gerar_resposta
from app.services.rag_service import get_document_store

router = APIRouter(prefix="/api/v1", tags=["duvidas"])


@router.post(
    "/duvidas",
    response_model=DuvidaResponse,
    summary="Tirar duvida sobre o projeto",
    responses={
        200: {"description": "Pergunta respondida com sucesso"},
        400: {
            "description": "Pergunta invalida",
            "model": ErrorResponse,
        },
        503: {
            "description": "Servico de IA indisponivel",
            "model": ErrorResponse,
        },
    },
)
async def perguntar(
    payload: DuvidaRequest,
    _=Depends(require_role("admin", "professional", "viewer")),
):
    """Responde uma pergunta sobre o projeto com base na documentacao.

    Utiliza RAG (TF-IDF + Groq) para recuperar trechos relevantes da
    documentacao e gerar uma resposta precisa.

    Requer perfil **admin**, **professional** ou **viewer**.
    """
    try:
        store = get_document_store()
        chunks = store.buscar(payload.pergunta)
        contexto_info = []
        for c in chunks:
            texto_resumido = c["texto"][:80].replace("\n", " ").strip()
            contexto_info.append(f"{c['fonte']} ({texto_resumido}...)")

        resposta = gerar_resposta(payload.pergunta, chunks)

        return DuvidaResponse(
            pergunta=payload.pergunta,
            resposta=resposta,
            contexto_utilizado=contexto_info if contexto_info else [],
            modelo=GROQ_MODEL,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except APITimeoutError:
        raise HTTPException(
            status_code=503,
            detail="O servico de IA esta demorando mais que o esperado. Tente novamente.",
        ) from None
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Servico de IA temporariamente indisponivel",
        ) from None
