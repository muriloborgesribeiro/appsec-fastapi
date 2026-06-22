# ============================================================
#  ml/alvarado.py
#  APPSPEC -- Motor Alvarado Score (deterministico)
#  Contrato: SPEC-01 6.2 / SPEC-03
#
#  ZERO dependencia de ML ou IA generativa.
#  TODO texto clinico e hardcoded com referencia DOI.
#  Nenhuma string e gerada dinamicamente.
#
#  Referencia base: Alvarado A. (1986). A practical score for
#  the early diagnosis of acute appendicitis.
#  Ann Emerg Med, 15(5), 557-564.
#  DOI: 10.1016/S0196-0644(86)80468-2
# ============================================================

from app.config import ALVARADO_TEMP_THRESHOLD, ALVARADO_LEUCOCITOS_THRESHOLD
from ml.protocolo import ModeloMLProtocol


CHAVES_ALVARADO = [
    "dor_migratoria",
    "anorexia",
    "nauseas_vomitos",
    "dor_fid",
    "descompressao_dolorosa",
    "temperatura",
    "leucocitos",
    "neutrofilia",
]


class AlvaradoMotor:
    def executar(self, dados: dict) -> dict:
        params = {k: dados.get(k, False) for k in CHAVES_ALVARADO}
        return calcular_alvarado(params)


# -----------------------------------------------------------
#  CRITERIOS DO ALVARADO SCORE (8 criterios, max 10 pontos)
#  Cada criterio tem referencia DOI como comentario
#  Convenção SPEC-00 §7.1: Todo criterio clinico com DOI
# -----------------------------------------------------------

CRITERIOS = [
    # --- Sintomas (S) - 3 pontos ---
    {
        "id": "dor_migratoria",
        # DOI: 10.1016/S0196-0644(86)80468-2 — Alvarado, 1986
        "descricao": "Dor migratoria para FID",
        "descricao_completa": (
            "Dor que iniciou em regiao periumbilical ou epigastrica "
            "e migrou para a fossa iliaca direita (FID). "
            "Criterio M do MANTRELS."
        ),
        "pontos": 1,
        "tipo": "bool",
        "categoria": "Sintomas",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2",
    },
    {
        "id": "anorexia",
        # DOI: 10.1016/S0196-0644(86)80468-2 — Alvarado, 1986
        "descricao": "Anorexia",
        "descricao_completa": (
            "Perda de apetite associada ao quadro clinico atual. "
            "Criterio A do MANTRELS."
        ),
        "pontos": 1,
        "tipo": "bool",
        "categoria": "Sintomas",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2",
    },
    {
        "id": "nauseas_vomitos",
        # DOI: 10.1016/S0196-0644(86)80468-2 — Alvarado, 1986
        "descricao": "Nauseas ou vomitos",
        "descricao_completa": (
            "Presenca de nauseas e/ou vomitos associados ao quadro. "
            "Criterio N do MANTRELS."
        ),
        "pontos": 1,
        "tipo": "bool",
        "categoria": "Sintomas",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2",
    },
    # --- Sinais (S) - 3 pontos ---
    {
        "id": "dor_fid",
        # DOI: 10.1016/S0196-0644(86)80468-2 — Alvarado, 1986
        "descricao": "Dor a palpacao em FID",
        "descricao_completa": (
            "Dor a palpacao direta na fossa iliaca direita (ponto de McBurney). "
            "Criterio T do MANTRELS. Peso 2 pontos por ser o sinal "
            "mais especifico para apendicite."
        ),
        "pontos": 2,
        "tipo": "bool",
        "categoria": "Sinais",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2",
    },
    {
        "id": "descompressao_dolorosa",
        # DOI: 10.1016/S0196-0644(86)80468-2 — Alvarado, 1986
        "descricao": "Descompressao dolorosa (Blumberg)",
        "descricao_completa": (
            "Dor a descompressao brusca da parede abdominal (sinal de Blumberg). "
            "Indica irritacao peritoneal. Criterio R do MANTRELS."
        ),
        "pontos": 1,
        "tipo": "bool",
        "categoria": "Sinais",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2",
    },
    {
        "id": "temperatura",
        # DOI: 10.1016/S0196-0644(86)80468-2 — Alvarado, 1986
        "descricao": "Temperatura > 37.3 C",
        "descricao_completa": (
            "Temperatura axilar acima de 37.3 graus Celsius. "
            "Criterio E do MANTRELS (Elevation of temperature). "
            "Nota: criterio e estritamente MAIOR que 37.3, nao igual."
        ),
        "pontos": 1,
        "tipo": "threshold",
        "threshold": ALVARADO_TEMP_THRESHOLD,
        "categoria": "Sinais",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2",
    },
    # --- Laboratorial (L) - 4 pontos ---
    {
        "id": "leucocitos",
        # DOI: 10.1016/S0196-0644(86)80468-2 — Alvarado, 1986
        "descricao": "Leucocitos > 10.000/mm3",
        "descricao_completa": (
            "Leucocitose: contagem de leucocitos acima de 10.000 celulas/mm3. "
            "Criterio L do MANTRELS. Peso 2 pontos por ser marcador "
            "laboratorial relevante. "
            "Nota: criterio e estritamente MAIOR que 10.000, nao igual."
        ),
        "pontos": 2,
        "tipo": "threshold",
        "threshold": ALVARADO_LEUCOCITOS_THRESHOLD,
        "categoria": "Laboratorial",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2",
    },
    {
        "id": "neutrofilia",
        # DOI: 10.1016/S0196-0644(86)80468-2 — Alvarado, 1986
        "descricao": "Neutrofilia (desvio a esquerda)",
        "descricao_completa": (
            "Desvio a esquerda na contagem diferencial de leucocitos, "
            "indicando neutrofilia (> 75% de neutrofilos). "
            "Criterio S do MANTRELS (Shift of WBC count)."
        ),
        "pontos": 1,
        "tipo": "bool",
        "categoria": "Laboratorial",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2",
    },
]


# -----------------------------------------------------------
#  CLASSIFICACOES POR FAIXA DE SCORE
#  Referencia: Ohle R et al. (2011). The Alvarado score for
#  predicting acute appendicitis: systematic review.
#  BMC Med, 9, 139. DOI: 10.1186/1741-7015-9-139
# -----------------------------------------------------------

CLASSIFICACOES = {
    "baixo": {
        "range": (0, 4),
        "label": "Baixo Risco",
        "cor": "success",  # Bootstrap: verde
        "interpretacao": (
            "Score <= 4 indica baixa probabilidade de apendicite aguda. "
            "Considerar alta hospitalar com orientacoes de retorno em caso de piora. "
            "Sensibilidade para este ponto de corte: 99% (excluir apendicite). "
            "[Ohle et al., 2011. DOI:10.1186/1741-7015-9-139]"
        ),
        "conduta": "Alta com orientacoes. Retornar se piora dos sintomas.",
        "disclaimer": "AVISO: Esta estimativa NAO substitui avaliacao medica presencial.",
    },
    "moderado": {
        "range": (5, 6),
        "label": "Risco Moderado",
        "cor": "warning",  # Bootstrap: amarelo
        "interpretacao": (
            "Score 5-6 indica risco intermediario de apendicite. "
            "Recomenda-se observacao clinica, exames complementares "
            "(hemograma, PCR, ultrassom) e reavaliacao em 6-12h. "
            "[Ohle et al., 2011. DOI:10.1186/1741-7015-9-139]"
        ),
        "conduta": "Observacao hospitalar. Exames complementares. Reavaliacao em 6-12h.",
        "disclaimer": "AVISO: Esta estimativa NAO substitui avaliacao medica presencial.",
    },
    "alto": {
        "range": (7, 10),
        "label": "Alto Risco",
        "cor": "danger",  # Bootstrap: vermelho
        "interpretacao": (
            "Score >= 7 indica alta probabilidade de apendicite aguda. "
            "Recomenda-se avaliacao cirurgica imediata e preparo para cirurgia. "
            "Especificidade para este ponto de corte: 81-97%. "
            "[Ohle et al., 2011. DOI:10.1186/1741-7015-9-139] "
            "[Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2]"
        ),
        "conduta": "Avaliacao cirurgica imediata. Considerar apendicectomia.",
        "disclaimer": "AVISO: Esta estimativa NAO substitui avaliacao medica presencial.",
    },
}


# -----------------------------------------------------------
#  FUNCAO PUBLICA: calcular_alvarado(dados: dict) -> dict
#  Interface conforme SPEC-01 6.2
# -----------------------------------------------------------


def calcular_alvarado(dados: dict) -> dict:
    """
    Calcula o Escore de Alvarado para estimativa de risco de apendicite.

    Interface publica conforme SPEC-01 6.2:
      INPUT:  dados (dict) com 8 campos clinicos
      OUTPUT: {
          "score": int,              # 0-10
          "classificacao": str,      # "baixo" | "moderado" | "alto"
          "label": str,              # "Baixo Risco" | "Risco Moderado" | "Alto Risco"
          "cor": str,                # "success" | "warning" | "danger"
          "interpretacao": str,      # texto hardcoded com DOI
          "conduta": str,            # recomendacao de conduta
          "disclaimer": str,         # aviso clinico obrigatorio
          "detalhamento": list       # [{criterio, presente, pontos, referencia}]
      }

    Referencia: Alvarado A. (1986). DOI:10.1016/S0196-0644(86)80468-2
    Classificacao: Ohle R et al. (2011). DOI:10.1186/1741-7015-9-139

    Tecnologia: Python puro (sem ML, sem IA generativa)
    """
    score = 0
    detalhamento = []

    for criterio in CRITERIOS:
        criterio_id = criterio["id"]
        valor = dados[criterio_id]  # KeyError propaga se chave ausente (SPEC-03 11)
        presente = False
        pontos_atribuidos = 0

        if criterio["tipo"] == "bool":
            # Criterios booleanos: True/False
            presente = bool(valor)
        elif criterio["tipo"] == "threshold":
            # Criterios de limiar: estritamente MAIOR que o threshold
            # SPEC-03 11: temperatura == 37.3 NAO pontua
            # SPEC-03 11: leucocitos == 10000 NAO pontua
            presente = float(valor) > float(criterio["threshold"])  # type: ignore[arg-type]

        if presente:
            pontos_atribuidos = criterio["pontos"]  # type: ignore[assignment]
            score += pontos_atribuidos

        detalhamento.append(
            {
                "criterio": criterio["descricao"],
                "criterio_completo": criterio["descricao_completa"],
                "presente": presente,
                "pontos": pontos_atribuidos,
                "pontos_max": criterio["pontos"],
                "categoria": criterio["categoria"],
                "referencia": criterio["referencia"],
            }
        )

    # Validacao de bounds (SPEC-00 7.3 / SPEC-03 RF-02)
    # Score Alvarado sempre entre 0 e 10
    if not (0 <= score <= 10):
        raise ValueError(
            f"Score invalido: {score}. Esperado: 0-10. Dados recebidos: {dados}"
        )

    # Determinar classificacao por faixa
    classificacao_info = _classificar_score(score)

    return {
        "score": score,
        "classificacao": classificacao_info["chave"],
        "label": classificacao_info["label"],
        "cor": classificacao_info["cor"],
        "interpretacao": classificacao_info["interpretacao"],
        "conduta": classificacao_info["conduta"],
        "disclaimer": classificacao_info["disclaimer"],
        "detalhamento": detalhamento,
    }


def _classificar_score(score: int) -> dict:
    """
    Determina a classificacao de risco baseada no score.
    Referencia: Ohle R et al. (2011). DOI:10.1186/1741-7015-9-139
    """
    for chave, info in CLASSIFICACOES.items():
        faixa_min, faixa_max = int(info["range"][0]), int(info["range"][1])
        if faixa_min <= int(score) <= faixa_max:
            return {
                "chave": chave,
                "label": info["label"],
                "cor": info["cor"],
                "interpretacao": info["interpretacao"],
                "conduta": info["conduta"],
                "disclaimer": info["disclaimer"],
            }

    # Nunca deveria chegar aqui se o score esta entre 0-10
    # e as faixas cobrem [0-4], [5-6], [7-10]
    raise AssertionError(
        f"Score {score} nao se encaixa em nenhuma faixa de classificacao"
    )


# -----------------------------------------------------------
#  FUNCAO DE TESTE (SPEC-03 RF-06)
# -----------------------------------------------------------


def testar_alvarado():
    """
    Testa o motor Alvarado com casos conhecidos.
    Deve ser chamado para validacao antes de prosseguir para SPEC-04.
    """
    print("=" * 50)
    print("  TESTE DO MOTOR ALVARADO SCORE")
    print("=" * 50)

    # Caso 1: Todos negativos -> score 0 (baixo)
    caso_0 = {
        "dor_migratoria": False,
        "anorexia": False,
        "nauseas_vomitos": False,
        "dor_fid": False,
        "descompressao_dolorosa": False,
        "temperatura": 36.5,
        "leucocitos": 8000,
        "neutrofilia": False,
    }
    r0 = calcular_alvarado(caso_0)
    assert r0["score"] == 0, f"Esperado 0, obteve {r0['score']}"
    assert r0["classificacao"] == "baixo"
    print(f"  [OK] Caso 0: score={r0['score']}, class={r0['classificacao']}")

    # Caso 2: Todos positivos -> score 10 (alto)
    caso_10 = {
        "dor_migratoria": True,
        "anorexia": True,
        "nauseas_vomitos": True,
        "dor_fid": True,
        "descompressao_dolorosa": True,
        "temperatura": 38.5,
        "leucocitos": 15000,
        "neutrofilia": True,
    }
    r10 = calcular_alvarado(caso_10)
    assert r10["score"] == 10, f"Esperado 10, obteve {r10['score']}"
    assert r10["classificacao"] == "alto"
    print(f"  [OK] Caso 10: score={r10['score']}, class={r10['classificacao']}")

    # Caso 3: Score 5 (moderado) - dor_migratoria + dor_fid(2) + leucocitos(2)
    caso_5 = {
        "dor_migratoria": True,
        "anorexia": False,
        "nauseas_vomitos": False,
        "dor_fid": True,
        "descompressao_dolorosa": False,
        "temperatura": 36.8,
        "leucocitos": 12000,
        "neutrofilia": False,
    }
    r5 = calcular_alvarado(caso_5)
    assert r5["score"] == 5, f"Esperado 5, obteve {r5['score']}"
    assert r5["classificacao"] == "moderado"
    print(f"  [OK] Caso 5: score={r5['score']}, class={r5['classificacao']}")

    # Caso 4: Temperatura exatamente 37.3 NAO pontua (SPEC-03 11)
    caso_limite_temp = {
        "dor_migratoria": False,
        "anorexia": False,
        "nauseas_vomitos": False,
        "dor_fid": False,
        "descompressao_dolorosa": False,
        "temperatura": 37.3,
        "leucocitos": 5000,
        "neutrofilia": False,
    }
    r_temp = calcular_alvarado(caso_limite_temp)
    assert r_temp["score"] == 0, f"Temp 37.3 nao deve pontuar. Score={r_temp['score']}"
    print(f"  [OK] Limite temp=37.3: score={r_temp['score']} (nao pontua)")

    # Caso 5: Leucocitos exatamente 10000 NAO pontua (SPEC-03 11)
    caso_limite_leuco = {
        "dor_migratoria": False,
        "anorexia": False,
        "nauseas_vomitos": False,
        "dor_fid": False,
        "descompressao_dolorosa": False,
        "temperatura": 36.5,
        "leucocitos": 10000,
        "neutrofilia": False,
    }
    r_leuco = calcular_alvarado(caso_limite_leuco)
    assert r_leuco["score"] == 0, (
        f"Leuco 10000 nao deve pontuar. Score={r_leuco['score']}"
    )
    print(f"  [OK] Limite leuco=10000: score={r_leuco['score']} (nao pontua)")

    # Caso 6: Score 7 (alto) - fronteira
    caso_7 = {
        "dor_migratoria": True,
        "anorexia": True,
        "nauseas_vomitos": True,
        "dor_fid": True,
        "descompressao_dolorosa": True,
        "temperatura": 36.5,
        "leucocitos": 5000,
        "neutrofilia": True,
    }
    r7 = calcular_alvarado(caso_7)
    assert r7["score"] == 7, f"Esperado 7, obteve {r7['score']}"
    assert r7["classificacao"] == "alto"
    print(f"  [OK] Caso 7: score={r7['score']}, class={r7['classificacao']}")

    # Caso 7: Score 4 (baixo) - fronteira
    caso_4 = {
        "dor_migratoria": True,
        "anorexia": True,
        "nauseas_vomitos": True,
        "dor_fid": False,
        "descompressao_dolorosa": False,
        "temperatura": 37.5,
        "leucocitos": 5000,
        "neutrofilia": False,
    }
    r4 = calcular_alvarado(caso_4)
    assert r4["score"] == 4, f"Esperado 4, obteve {r4['score']}"
    assert r4["classificacao"] == "baixo"
    print(f"  [OK] Caso 4: score={r4['score']}, class={r4['classificacao']}")

    # Verificar detalhamento
    assert len(r10["detalhamento"]) == 8, "Deve ter 8 criterios no detalhamento"
    for item in r10["detalhamento"]:
        assert "referencia" in item, f"Criterio sem referencia: {item['criterio']}"
        assert "DOI" in item["referencia"], f"Referencia sem DOI: {item['referencia']}"
    print(f"  [OK] Detalhamento: 8 criterios, todos com DOI")

    # Verificar disclaimer
    assert r0["disclaimer"], "Disclaimer ausente no score baixo"
    assert r5["disclaimer"], "Disclaimer ausente no score moderado"
    assert r10["disclaimer"], "Disclaimer ausente no score alto"
    print(f"  [OK] Disclaimer presente em todas as classificacoes")

    print()
    print("  TODOS OS TESTES PASSARAM!")
    print("=" * 50)


if __name__ == "__main__":
    testar_alvarado()
