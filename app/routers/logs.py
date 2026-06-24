"""Endpoint de consulta de logs da aplicacao.

Tecnico: expoe as ultimas linhas do buffer de log via HTTP, restrito a admin.
         Torna o registro de execucoes/erros demonstravel pelo Swagger, sem
         precisar de acesso ao console do servidor.
Clinico: o administrador abre o livro de ocorrencias e le as ultimas anotacoes.
"""

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_role
from app.logging_config import get_recent_logs

router = APIRouter(prefix="/api/v1", tags=["logs"])


@router.get(
    "/logs",
    summary="Consultar logs recentes da aplicacao (admin)",
    description=(
        "Retorna as ultimas linhas de log de execucao e erro da aplicacao. "
        "Restrito ao perfil **admin**. Use para auditar e monitorar a API."
    ),
    responses={
        200: {"description": "Lista das linhas de log mais recentes"},
        401: {"description": "Sem token de autenticacao"},
        403: {"description": "Perfil sem permissao (somente admin)"},
    },
)
async def consultar_logs(
    limite: int = Query(100, ge=1, le=200, description="Quantas linhas retornar"),
    nivel: str | None = Query(
        None, description="Filtrar por nivel: INFO, WARNING, ERROR"
    ),
    _=Depends(require_role("admin")),
):
    """Retorna as linhas de log mais recentes (admin).

    Tecnico: le do buffer em memoria alimentado pelo logging.
    Clinico: consulta as ultimas anotacoes do livro de ocorrencias.
    """
    linhas = get_recent_logs(limite=limite, nivel=nivel)
    return {"total": len(linhas), "logs": linhas}
