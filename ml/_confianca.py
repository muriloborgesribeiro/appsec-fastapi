from app.config import LIMIAR_CONFIANCA_ALTA, LIMIAR_CONFIANCA_MEDIA

CONFIANCA_ALTA = "Alta"
CONFIANCA_MEDIA = "Media"
CONFIANCA_BAIXA = "Baixa -- resultado inconclusivo"


def calcular_confianca(probabilidade: float) -> str:
    prob_max = max(probabilidade, 1.0 - probabilidade)
    if prob_max >= LIMIAR_CONFIANCA_ALTA:
        return CONFIANCA_ALTA
    elif prob_max >= LIMIAR_CONFIANCA_MEDIA:
        return CONFIANCA_MEDIA
    else:
        return CONFIANCA_BAIXA
