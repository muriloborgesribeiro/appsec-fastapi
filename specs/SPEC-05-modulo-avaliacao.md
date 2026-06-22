# Spec: APPSPEC-05 — Módulo de Avaliação

**Versão:** 1.0  
**Status:** Aprovada  
**Autor:** Neri  
**Data:** 2026-04-26  
**Depende de:** SPEC-00, SPEC-01, SPEC-04

---

## 1. Resumo

Implementa `ml/avaliador.py` — módulo que calcula e exibe todas as métricas de avaliação de modelos ensinadas na disciplina: Matriz de Confusão (VP, FP, FN, VN), Sensibilidade, Especificidade, Acurácia, VPP e VPN. Também gera o workflow Orange3 (`.ows`) automaticamente para validação visual. Cada métrica é exibida com sua fórmula visível na UI.

---

## 2. Contexto e Motivação

**Problema:** O projeto original listava sensibilidade e especificidade sem estrutura real de cálculo nem visualização.

**Evidências:** O Prof. Ronaldo ensinou explicitamente a Matriz de Confusão, Sensibilidade (TPR) e Especificidade como métricas centrais de avaliação clínica de classificadores. O sistema deve mostrá-las com as fórmulas visíveis.

**Por que agora:** Depende do modelo KNN treinado (SPEC-04).

---

## 3. Goals

- [ ] G-01: Calcular as 7 métricas da disciplina com fórmulas hardcoded
- [ ] G-02: Gerar imagem PNG da matriz de confusão com matplotlib/seaborn
- [ ] G-03: Gerar workflow Orange3 (.ows) automaticamente
- [ ] G-04: Comparar Alvarado vs KNN nas mesmas métricas
- [ ] G-05: Cada fórmula visível na UI com notação matemática

| Métrica | Baseline | Target | Prazo |
|---|---|---|---|
| Métricas calculadas | 0/7 | 7/7 | SPEC-05 |
| Imagem da matriz gerada | não | sim (.png) | SPEC-05 |
| Workflow Orange gerado | não | sim (.ows) | SPEC-05 |

---

## 4. Non-Goals

- NG-01: **NÃO** calcula AUC-ROC nesta versão — apenas métricas ensinadas na disciplina
- NG-02: **NÃO** faz comparação com outros algoritmos (SVM, Random Forest)
- NG-03: **NÃO** usa bibliotecas de visualização além de matplotlib + seaborn
- NG-04: **NÃO** gera relatório PDF — apenas imagens e métricas para a UI

---

## 5. Usuários e Personas

**Primário:** `setup.py` — chama avaliador durante o setup para gerar artefatos  
**Secundário:** `diagnostico/views.py` — carrega métricas pré-calculadas para exibir na tela de avaliação

---

## 6. Requisitos Funcionais

### 6.1 As 7 Métricas da Disciplina

```python
# Referência: Fawcett T. (2006). An introduction to ROC analysis.
# Pattern Recognit Lett. DOI:10.1016/j.patrec.2005.10.010

METRICAS = {
    "acuracia": {
        "formula": "Acurácia = (VP + VN) / Total",
        "descricao": "Proporção de classificações corretas no total",
        "referencia": "Fawcett, 2006. DOI:10.1016/j.patrec.2005.10.010"
    },
    "sensibilidade": {
        "formula": "Sensibilidade = VP / (VP + FN)",
        "descricao": "Taxa de Verdadeiros Positivos (TPR) — capacidade de detectar doença",
        "relevancia_clinica": "Alta sensibilidade = poucos casos de apendicite perdidos",
        "referencia": "Fawcett, 2006. DOI:10.1016/j.patrec.2005.10.010"
    },
    "especificidade": {
        "formula": "Especificidade = VN / (VN + FP)",
        "descricao": "Taxa de Verdadeiros Negativos (TNR) — capacidade de excluir doença",
        "relevancia_clinica": "Alta especificidade = poucos casos normais operados desnecessariamente",
        "referencia": "Fawcett, 2006. DOI:10.1016/j.patrec.2005.10.010"
    },
    "vpp": {
        "formula": "VPP = VP / (VP + FP)",
        "descricao": "Valor Preditivo Positivo — probabilidade de ter doença dado teste positivo",
        "referencia": "Fawcett, 2006. DOI:10.1016/j.patrec.2005.10.010"
    },
    "vpn": {
        "formula": "VPN = VN / (VN + FN)",
        "descricao": "Valor Preditivo Negativo — probabilidade de não ter doença dado teste negativo",
        "referencia": "Fawcett, 2006. DOI:10.1016/j.patrec.2005.10.010"
    }
}
```

### 6.2 Fluxo Principal — Geração de Métricas

```
1. Recebe y_real (array) e y_pred (array) do KNN
2. Calcula VP, FP, FN, VN via sklearn.metrics.confusion_matrix
3. Calcula as 7 métricas com as fórmulas hardcoded
4. Gera imagem da matriz de confusão com seaborn.heatmap
5. Salva PNG em diagnostico/static/diagnostico/img/confusion_matrix.png
6. Retorna dict com todas as métricas e path da imagem
```

### 6.3 Fluxo — Geração do Workflow Orange3

```python
# O .ows é um arquivo XML que o Orange3 abre diretamente
# Contém: File → Preprocess → KNN → Confusion Matrix → ROC

OWS_TEMPLATE = """<?xml version='1.0' encoding='utf-8'?>
<scheme version="2.0" title="APPSPEC - Validação KNN Apendicite" 
        description="Workflow gerado automaticamente pelo APPSPEC
        Disciplina: Agentes Inteligentes - UFG
        Prof. Ronaldo Martins da Costa">
  <nodes>
    <node id="0" name="File" ... />          <!-- Carrega regensburg_processed.csv -->
    <node id="1" name="Preprocess" ... />    <!-- Normalização Min-Max -->
    <node id="2" name="KNN" ... />           <!-- k=[k_otimo], metric=euclidean -->
    <node id="3" name="Test and Score" ... /> <!-- Train/Test split 70/30 -->
    <node id="4" name="Confusion Matrix" ... />
  </nodes>
  ...
</scheme>"""
```

### 6.4 Comparação Alvarado vs KNN

```python
# Roda o Alvarado Score em todos os pacientes do conjunto de teste
# Compara com as predições do KNN
# Gera tabela lado a lado com as métricas de ambos

TABELA_COMPARACAO = {
    "alvarado": {
        "sensibilidade": float,
        "especificidade": float,
        "acuracia": float,
        "metodo": "Regra determinística (1986)"
    },
    "knn": {
        "sensibilidade": float,
        "especificidade": float,
        "acuracia": float,
        "metodo": "KNN — scikit-learn"
    }
}
```

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|---|---|---|---|
| RNF-01 | Imagem da matriz | PNG, 800x600px | Legível em tela e projetor |
| RNF-02 | Cores da matriz | Verde=VP/VN, Vermelho=FP/FN | Convenção clínica |
| RNF-03 | Fórmulas na UI | LaTeX-like em HTML | `VP / (VP + FN)` plaintext é suficiente |

---

## 8. Design e Interface

A tela `avaliacao.html` exibe:
1. Matriz de confusão como imagem PNG com legenda explicativa
2. Tabela de métricas com colunas: Métrica | Fórmula | Valor Alvarado | Valor KNN
3. Interpretação clínica de cada métrica (hardcoded)
4. Botão "Abrir no Orange3" que instrui como abrir o .ows gerado

---

## 9. Modelo de Dados

```python
# Output de avaliar_modelo()
{
    "vp": int,
    "fp": int,
    "fn": int,
    "vn": int,
    "acuracia": float,
    "sensibilidade": float,
    "especificidade": float,
    "vpp": float,
    "vpn": float,
    "imagem_matriz": str,           # path relativo para uso no template
    "comparacao_alvarado": dict,    # métricas do Alvarado no mesmo teste
    "comparacao_knn": dict          # métricas do KNN
}
```

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|---|---|---|
| sklearn.metrics | Obrigatória | Métricas não calculadas |
| matplotlib + seaborn | Obrigatória | Sem imagem da matriz |
| SPEC-04 (y_pred do KNN) | Obrigatória | Sem predições para avaliar |
| Orange3 | Opcional | .ows não gerado; sistema funciona sem ele |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---|---|---|
| Divisão por zero em sensibilidade | VP + FN = 0 | Retorna 0.0 e loga aviso |
| matplotlib não instalado | ImportError | Pula geração de imagem, retorna path None |
| Orange3 não instalado | ImportError | Loga aviso, pula geração .ows |
| Todas as predições iguais | KNN viciado | Métricas calculadas normalmente, UI mostra aviso |

---

## 12. Segurança e Privacidade

- Imagem gerada não contém dados individuais de pacientes — apenas agregados
- Workflow .ows não contém dados, apenas configuração de pipeline

---

## 13. Plano de Rollout

Gerado em SPEC-05. Depende de SPEC-04 (modelo treinado). Testado via `python -c "from ml.avaliador import testar_avaliador; testar_avaliador()"`.

---

## 14. Open Questions

- OQ-01: Gerar também curva ROC? Relevante academicamente mas não ensinada explicitamente. Decisão: incluir como elemento visual secundário na tela de avaliação.
