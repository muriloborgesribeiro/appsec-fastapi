# Spec: APPSPEC-03 — Motor Alvarado Score

**Versão:** 1.0  
**Status:** Aprovada  
**Autor:** Neri  
**Data:** 2026-04-26  
**Depende de:** SPEC-00, SPEC-01

---

## 1. Resumo

Implementa `ml/alvarado.py` — motor determinístico do Escore de Alvarado para estimativa de risco de apendicite. Toda lógica é baseada em critérios clínicos publicados, hardcoded com referências DOI. Nenhuma geração dinâmica de texto clínico. Zero dependência de LLM ou qualquer IA generativa.

---

## 2. Contexto e Motivação

**Problema:** O Escore de Alvarado é a regra clínica mais utilizada globalmente para triagem de apendicite em pronto-socorro. Implementá-lo corretamente — com referências — demonstra rigor científico e serve como âncora de validação para o KNN.

**Evidências:** Alvarado (1986) descreveu o escore MANTRELS para diagnóstico de apendicite. Meta-análises posteriores confirmaram sensibilidade de 72-99% e especificidade de 57-90% dependendo do ponto de corte. DOI: 10.1097/00000658-198609000-00004

**Por que agora:** O Motor Alvarado é independente de dados e de ML — pode ser gerado antes do KNN e serve como baseline de comparação.

---

## 3. Goals

- [ ] G-01: Implementar os 8 critérios do Alvarado Score com pesos corretos
- [ ] G-02: Cada critério tem referência DOI no código como comentário
- [ ] G-03: Classificação em 3 faixas (baixo / moderado / alto) com interpretação hardcoded
- [ ] G-04: Output estruturado conforme interface pública definida em SPEC-01
- [ ] G-05: Validação de bounds: score sempre entre 0 e 10

| Métrica | Baseline | Target | Prazo |
|---|---|---|---|
| Critérios implementados | 0/8 | 8/8 | SPEC-03 |
| Referências DOI no código | 0 | 1 por critério | SPEC-03 |
| Cobertura de testes unitários | 0% | 100% (scores 0-10) | SPEC-03 |

---

## 4. Non-Goals

- NG-01: **NÃO** usa ML — é cálculo determinístico puro
- NG-02: **NÃO** gera texto clínico dinamicamente — todo texto é dicionário hardcoded
- NG-03: **NÃO** implementa variações do Alvarado (MANTRELS, PAS, RIPASA) — apenas o Alvarado clássico de 10 pontos
- NG-04: **NÃO** valida os dados de entrada — isso é responsabilidade de forms.py (SPEC-07)
- NG-05: **NÃO** faz diagnóstico — classifica risco com disclaimer obrigatório

---

## 5. Usuários e Personas

**Primário:** `diagnostico/views.py` — chama `calcular_alvarado(dados)` e usa o resultado  
**Secundário:** `setup.py` — pode usar para testes de sanidade

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| RF-01 | Implementar 8 critérios com pesos corretos | Must | Score 10/10 com todos os critérios positivos |
| RF-02 | Validar bounds do score [0, 10] | Must | AssertionError se score < 0 ou > 10 |
| RF-03 | Retornar detalhamento por critério | Must | Lista com nome, pontos e referência de cada critério |
| RF-04 | Classificar em baixo/moderado/alto | Must | Conforme tabela clínica publicada |
| RF-05 | Texto de interpretação hardcoded com DOI | Must | Nenhuma string gerada dinamicamente |
| RF-06 | Função de teste embutida | Should | `testar_alvarado()` retorna casos conhecidos corretos |

### 6.2 Os 8 Critérios do Alvarado Score

```python
# Referência base: Alvarado A. (1986). A practical score for the early diagnosis of
# acute appendicitis. Ann Emerg Med. DOI: 10.1016/S0196-0644(86)80468-2

CRITERIOS = [
    # Sintomas (4 pontos possíveis)
    {
        "id": "dor_migratoria",
        "descricao": "Dor migratória para FID",
        "pontos": 1,
        "tipo": "bool",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2"
    },
    {
        "id": "anorexia",
        "descricao": "Anorexia",
        "pontos": 1,
        "tipo": "bool",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2"
    },
    {
        "id": "nauseas_vomitos",
        "descricao": "Náuseas ou vômitos",
        "pontos": 1,
        "tipo": "bool",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2"
    },
    # Sinais (5 pontos possíveis)
    {
        "id": "dor_fid",
        "descricao": "Dor à palpação em FID",
        "pontos": 2,
        "tipo": "bool",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2"
    },
    {
        "id": "descompressao_dolorosa",
        "descricao": "Descompressão dolorosa (Blumberg)",
        "pontos": 1,
        "tipo": "bool",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2"
    },
    {
        "id": "temperatura",
        "descricao": "Temperatura > 37.3°C",
        "pontos": 1,
        "tipo": "threshold",
        "threshold": 37.3,
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2"
    },
    # Laboratorial (2 pontos possíveis)
    {
        "id": "leucocitos",
        "descricao": "Leucócitos > 10.000/mm³",
        "pontos": 2,
        "tipo": "threshold",
        "threshold": 10000,
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2"
    },
    {
        "id": "neutrofilia",
        "descricao": "Neutrofilia (desvio à esquerda)",
        "pontos": 1,
        "tipo": "bool",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2"
    },
]
```

### 6.3 Classificação por Faixas

```python
# Referência: Ohle R et al. (2011). The Alvarado score for predicting acute appendicitis.
# Systematic review and meta-analysis. BMC Med. DOI:10.1186/1741-7015-9-139

CLASSIFICACOES = {
    "baixo": {
        "range": (0, 4),          # score <= 4
        "label": "Baixo Risco",
        "cor": "success",         # Bootstrap: verde
        "interpretacao": (
            "Score ≤ 4 indica baixa probabilidade de apendicite aguda. "
            "Considerar alta hospitalar com orientações de retorno em caso de piora. "
            "Sensibilidade para este ponto de corte: 99% (excluir apendicite). "
            "[Ohle et al., 2011. DOI:10.1186/1741-7015-9-139]"
        ),
        "conduta": "Alta com orientações. Retornar se piora dos sintomas.",
        "disclaimer": "AVISO: Esta estimativa não substitui avaliação médica presencial."
    },
    "moderado": {
        "range": (5, 6),          # score 5 ou 6
        "label": "Risco Moderado",
        "cor": "warning",         # Bootstrap: amarelo
        "interpretacao": (
            "Score 5-6 indica risco intermediário de apendicite. "
            "Recomenda-se observação clínica, exames complementares "
            "(hemograma, PCR, ultrassom) e reavaliação em 6-12h. "
            "[Ohle et al., 2011. DOI:10.1186/1741-7015-9-139]"
        ),
        "conduta": "Observação hospitalar. Exames complementares. Reavaliação em 6-12h.",
        "disclaimer": "AVISO: Esta estimativa não substitui avaliação médica presencial."
    },
    "alto": {
        "range": (7, 10),         # score >= 7
        "label": "Alto Risco",
        "cor": "danger",          # Bootstrap: vermelho
        "interpretacao": (
            "Score ≥ 7 indica alta probabilidade de apendicite aguda. "
            "Recomenda-se avaliação cirúrgica imediata e preparo para cirurgia. "
            "Especificidade para este ponto de corte: 81-97%. "
            "[Ohle et al., 2011. DOI:10.1186/1741-7015-9-139] "
            "[Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2]"
        ),
        "conduta": "Avaliação cirúrgica imediata. Considerar apendicectomia.",
        "disclaimer": "AVISO: Esta estimativa não substitui avaliação médica presencial."
    }
}
```

### 6.4 Fluxo Principal (Happy Path)

```
1. views.py chama calcular_alvarado(dados: dict)
2. alvarado.py itera sobre CRITERIOS
3. Para cada critério: verifica valor em dados, adiciona pontos se positivo
4. Soma total dos pontos → score (int, 0-10)
5. assert 0 <= score <= 10
6. Determina classificacao por faixas
7. Retorna dict conforme interface pública SPEC-01
```

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|---|---|---|---|
| RNF-01 | Tempo de cálculo | < 1ms | Operação trivial |
| RNF-02 | Determinismo | 100% | Mesma entrada → mesma saída sempre |
| RNF-03 | Zero dependências externas | 0 imports de ML | Apenas Python puro |

---

## 8. Design e Interface

O output de `calcular_alvarado()` alimenta diretamente o template `resultado.html`. Cada item do `detalhamento` é exibido como linha de tabela com: critério, pontos atribuídos, referência DOI clicável. A classificação determina a cor do card de resultado (Bootstrap: verde / amarelo / vermelho).

---

## 9. Modelo de Dados

```python
# Entrada
dados = {
    "dor_migratoria": bool,
    "anorexia": bool,
    "nauseas_vomitos": bool,
    "dor_fid": bool,
    "descompressao_dolorosa": bool,
    "temperatura": float,   # graus Celsius, ex: 37.8
    "leucocitos": int,      # células/mm³, ex: 12000
    "neutrofilia": bool
}

# Saída
resultado = {
    "score": int,                  # 0-10
    "classificacao": str,          # "baixo" | "moderado" | "alto"
    "label": str,                  # "Baixo Risco" | "Risco Moderado" | "Alto Risco"
    "cor": str,                    # "success" | "warning" | "danger"
    "interpretacao": str,          # texto hardcoded com DOI
    "conduta": str,                # recomendação de conduta
    "disclaimer": str,             # aviso clínico obrigatório
    "detalhamento": [              # um item por critério
        {
            "criterio": str,       # nome do critério
            "presente": bool,      # se o critério foi positivo
            "pontos": int,         # pontos atribuídos (0 ou peso)
            "referencia": str      # DOI
        }
    ]
}
```

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|---|---|---|
| SPEC-01 (interface pública) | Obrigatória | Output incompatível com views.py |
| diagnostico/forms.py (SPEC-07) | Validação de entrada | Dados podem chegar malformados |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---|---|---|
| Todos os critérios positivos | Score = 10 | Funciona normalmente, classificação "alto" |
| Todos os critérios negativos | Score = 0 | Funciona normalmente, classificação "baixo" |
| Score calculado > 10 | Bug de lógica | `assert False, f"Score inválido: {score}"` |
| Chave ausente no dict de entrada | `dados["anorexia"]` KeyError | Propaga KeyError — forms.py deve garantir todas as chaves |
| Temperatura no limite exato (37.3) | `temperatura == 37.3` | NÃO pontua — critério é `> 37.3` |
| Leucócitos no limite exato (10000) | `leucocitos == 10000` | NÃO pontua — critério é `> 10000` |

---

## 12. Segurança e Privacidade

- Nenhum dado é persistido neste módulo
- Nenhuma chamada de rede
- Texto clínico hardcoded — sem geração dinâmica que possa produzir conteúdo incorreto

---

## 13. Plano de Rollout

Gerado em SPEC-03. Testado via `python -c "from ml.alvarado import testar_alvarado; testar_alvarado()"` antes de avançar para SPEC-04.

---

## 14. Open Questions

- OQ-01: Incluir o Pediatric Appendicitis Score (PAS) como alternativa para pacientes < 18 anos? Decisão: fora do escopo desta versão (NG-03). Pode ser SPEC-09 futura.
