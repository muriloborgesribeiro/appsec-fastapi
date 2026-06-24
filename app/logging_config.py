"""Configuração central de logging da aplicação.

Tecnico: configura o logging da stdlib com saida para stdout (capturado pelo
         Render) e um buffer em memoria (deque) que guarda as ultimas linhas,
         permitindo expor os logs por um endpoint HTTP autenticado.
Clinico: e o "livro de ocorrencias" do plantao. Tudo que acontece fica
         registrado, e o administrador pode consultar as ultimas anotacoes.
"""

import logging
import os
import sys
from collections import deque
from datetime import datetime, timezone

# ── Buffer em memoria das ultimas linhas de log ───────────────
# Tecnico: deque com tamanho fixo; quando enche, descarta as mais antigas.
#          Funciona no Render (sistema de arquivos efemero) sem depender de disco.
_LOG_BUFFER: deque = deque(maxlen=int(os.getenv("LOG_BUFFER_SIZE", "200")))

_FORMATO = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


class BufferLogHandler(logging.Handler):
    """Handler que guarda cada linha formatada no buffer em memoria.

    Tecnico: alimentado pelo logging padrao; o endpoint /api/v1/logs le daqui.
    Clinico: a copia carbono de cada anotacao do livro de ocorrencias.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            _LOG_BUFFER.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "nivel": record.levelname,
                    "origem": record.name,
                    "mensagem": record.getMessage(),
                }
            )
        except Exception:  # nunca deixar o logging quebrar a aplicacao
            pass


def configurar_logging() -> None:
    """Configura o logging global. Chamado uma vez no startup.

    Tecnico: nivel via LOG_LEVEL (default INFO); saida para stdout + buffer.
    Clinico: abre o livro de ocorrencias no inicio do plantao.
    """
    nivel = os.getenv("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(nivel)

    # Evita handlers duplicados em reload/testes
    for h in list(root.handlers):
        if getattr(h, "_appsec", False):
            root.removeHandler(h)

    formatter = logging.Formatter(_FORMATO)

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    stream._appsec = True  # type: ignore[attr-defined]
    root.addHandler(stream)

    buffer_handler = BufferLogHandler()
    buffer_handler.setFormatter(formatter)
    buffer_handler._appsec = True  # type: ignore[attr-defined]
    root.addHandler(buffer_handler)

    get_logger("appspec").info(f"Logging configurado (nivel={nivel})")


def get_logger(nome: str) -> logging.Logger:
    """Retorna um logger nomeado.

    Tecnico: atalho para logging.getLogger, padroniza o uso no projeto.
    """
    return logging.getLogger(nome)


def get_recent_logs(limite: int = 100, nivel: str | None = None) -> list[dict]:
    """Retorna as linhas mais recentes do buffer, opcionalmente filtradas por nivel.

    Tecnico: lido pelo endpoint GET /api/v1/logs (admin).
    Clinico: as ultimas anotacoes do livro de ocorrencias, sob demanda.
    """
    linhas = list(_LOG_BUFFER)
    if nivel:
        nivel = nivel.upper()
        linhas = [linha for linha in linhas if linha["nivel"] == nivel]
    return linhas[-limite:]
