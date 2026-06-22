# SDD-07 — Mecanismos Anti-Alucinação e Segurança

**Versão:** 1.0  
**Status:** Final  
**Autor:** Engenharia Reversa  
**Data:** 2026-06-21  
**Sistema:** APPSPEC — Sistema de Apoio ao Diagnóstico de Apendicite

---

## 1. Resumo

O APPSPEC não possui uma camada pedagógica isolada (o módulo `ml/pedagogico.py` foi removido por ser código morto — nunca integrado ao sistema). No entanto, os **mecanismos anti-alucinação** estão distribuídos pelos módulos reais da aplicação. Este documento mapeia onde cada mecanismo está implementado no código em execução.

---

## 2. Mecanismos Anti-Alucinação (8)

| # | Mecanismo | Descrição | Onde está |
|---|-----------|-----------|-----------|
| 1 | **Texto hardcoded** | Nenhum texto clínico é gerado por IA. Critérios, condutas e interpretações estão fixos no código | `ml/alvarado.py` — dicionários INTERPRETACOES, CONDUTAS, DETALHAMENTO |
| 2 | **Score bounds** | Score Alvarado sempre validado entre 0 e 10 | `ml/alvarado.py:254` — `assert 0 <= score <= 10` |
| 3 | **Disclaimer obrigatório** | Aviso "não é diagnóstico" visível sem scroll em todas as páginas | `app/templates/base.html:10` (CSS `.disclaimer-global`) e `resultado.html` hardcoded |
| 4 | **Referências DOI** | Toda afirmação clínica/técnica tem referência DOI rastreável | `ml/alvarado.py` (cada critério), `ml/knn_engine.py:36`, `ml/svm_engine.py:18`, `ml/avaliador.py:31`, `ml/preprocessamento.py:310` |
| 5 | **Confiança mínima** | KNN e SVM avisam quando o resultado é inconclusivo | `ml/knn_engine.py:_calcular_confianca()`, `ml/svm_engine.py:_calcular_confianca()` — alerta se probabilidade máxima < 60% |
| 6 | **Linguagem de risco** | Sistema usa "risco", "probabilidade", nunca "diagnóstico" | Templates HTML: `resultado.html`, `index.html` — textos revisados |
| 7 | **Sem identificação** | Nenhum dado pessoal (nome, CPF) é coletado | `app/schemas.py:DiagnosticoRequest` — apenas 8 campos clínicos |
| 8 | **Validação de entrada** | Rejeita valores clinicamente impossíveis | `app/schemas.py:DiagnosticoRequest` — `temperatura: float = Field(ge=35.0, le=42.0)`, `leucocitos: float = Field(ge=1000, le=50000)` |

---

## 3. Disclaimer Global

Presente em todas as páginas via HTML hardcoded no template (`base.html`):

```html
<div class="disclaimer-global">
    AVISO: Este sistema é uma ferramenta de apoio didática
    desenvolvida na disciplina de Agentes Inteligentes (UFG).
    NÃO substitui avaliação médica presencial.
    NÃO deve ser usado para decisão clínica real.
    Sistema exclusivamente educacional.
</div>
```

---

## 4. Referências Científicas com DOI

Distribuídas nos módulos onde são usadas:

| Módulo | Referência | DOI | Uso |
|--------|-----------|-----|-----|
| `ml/alvarado.py` | Alvarado A. (1986) | `10.1016/S0196-0644(86)80468-2` | Escore Alvarado |
| `ml/alvarado.py` | Ohle R et al. (2011) | `10.1186/1741-7015-9-139` | Meta-análise do escore |
| `ml/knn_engine.py` | Cover & Hart (1967) | `10.1109/TIT.1967.1053964` | Algoritmo KNN |
| `ml/svm_engine.py` | Cortes & Vapnik (1995) | `10.1007/BF00994018` | Algoritmo SVM |
| `ml/avaliador.py` | Fawcett T. (2006) | `10.1016/j.patrec.2005.10.010` | Curvas ROC e PR |
| `ml/avaliador.py` | Youden WJ (1950) | `10.1002/1097-0142(...)` | Limiar ótimo |
| `ml/preprocessamento.py` | Kaufman S et al. (2012) | `10.1145/2020408.2020496` | Data leakage |
| `ml/preprocessamento.py` | Marcinkevics et al. (2023) | `10.5281/zenodo.7669442` | Dataset Regensburg |

---

## 5. Data Leakage — Conteúdo Explicativo

`ml/preprocessamento.py` contém em seu código-fonte (variável `DATA_LEAKAGE_EXPLICACAO`) a explicação didática do leakage detectado, com definição, evidência (Config D 95.6% vs Config E 69%) e referência DOI.

---

## 6. Nota sobre o Mapa Aula ↔ Código

O `MAPA_DISCIPLINA` (que mapeava cada conteúdo de aula ao arquivo de código correspondente) existia apenas no `ml/pedagogico.py` e **não foi reimplementado** em nenhum outro lugar. Este conteúdo não está disponível no sistema em execução.
