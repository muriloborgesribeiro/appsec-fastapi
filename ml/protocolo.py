from typing import Protocol, Dict, Any


class ModeloMLProtocol(Protocol):
    def executar(self, dados: Dict[str, Any]) -> Dict[str, Any]: ...
