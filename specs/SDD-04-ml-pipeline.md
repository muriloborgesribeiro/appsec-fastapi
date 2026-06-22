# SDD-04 — Pipeline de Machine Learning

**Versão:** 1.0  
**Status:** Final  
**Autor:** Engenharia Reversa  
**Data:** 2026-06-21  
**Sistema:** APPSPEC — Sistema de Apoio ao Diagnóstico de Apendicite

---

## 1. Resumo

O pipeline ML é composto por 4 etapas principais orquestradas pelo `setup.py`: pré-processamento do dataset Regensburg, treino KNN, treino SVM e avaliação comparativa. Em runtime, três motores independentes executam predições: Alvarado (determinístico), KNN (ML) e SVM (ML).

---

## 2. Dataset: Regensburg Pediatric Appendicitis

| Propriedade | Valor |
|-------------|-------|
| Fonte | UCI Machine Learning Repository |
| ID | 938 |
| Pacientes | 782 |
| Features | ~56 colunas (demográficas, clínicas, laboratoriais, ultrassom) |
| Target | Diagnosis (appendicitis / no appendicitis) |
| Prevalência | ~59% apendicite |
| Referência | Marcinkevics et al., 2023. DOI:10.5281/zenodo.7669442 |
| Download | Automático via `ucimlrepo.fetch_ucirepo(id=938)` |

---

## 3. Pré-processamento (`ml/preprocessamento.py`)

### 3.1 Etapas

```
CSV Bruto (56 colunas)
    │
    ▼
[Etapa 0] Remoção de colunas com data leakage:
    Alvarado_Score, Paedriatic_Appendicitis_Score,
    Management, Severity, Length_of_Stay, Segmented_Neutrophils
    │
    ▼
[Etapa 1] Remoção de linhas com target (Diagnosis) NaN
    │
    ▼
[Etapa 2] Conversão de categóricas para numéricas
    (binário: yes/no → 1/0, ordinal: mapeamento específico)
    │
    ▼
[Etapa 3] Split: Treino (70%) / Teste (15%) / Validação (15%)
    │
    ▼
[Etapa 4] Imputação (SimpleImputer, strategy='median')
    │
    ▼
[Etapa 5] Normalização MinMax (0-1)
    │
    ▼
[Etapa 6] Seleção da melhor configuração de features
```

### 3.2 Configurações de Features (6 variações)

| Config | Nome | Features | Status | Acurácia |
|--------|------|----------|--------|----------|
| A | 8 Alvarado completo | score + 7 individuais | RISCO | - |
| B | 8 Alvarado + Free_Fluids | score + individuais + US | RISCO | - |
| C | 10 features completas | score + individuais + US | RISCO | - |
| D | Score + US | Alvarado_Score + Appendix + Free_Fluids | **DESCARTADO** | 95.6% |
| **E** | 7 individuais + Free_Fluids | 7 critérios Alvarado + Free_Fluids | **LIMPO** | ~69% |
| **F** | Tabular completo Regensburg | 33 features limpas | **LIMPO** | **~78%** |

**Critério de seleção:** Maior acurácia entre configs com status **LIMPO** (sem data leakage). Config F é a vencedora por padrão.

### 3.3 Data Leakage Detection

**Problema:** Config D (Alvarado_Score + ultrassom) atingiu 95.6% de acurácia — artificialmente inflada porque o Alvarado_Score é derivado do próprio target (diagnóstico).

**Solução:** Configs contendo `Alvarado_Score` recebem status `RISCO` ou `DESCARTADO` e são excluídas da seleção automática.

**Referência:** Kaufman et al. (2012). DOI:10.1145/2020408.2020496

### 3.4 Features da Config Vencedora (F)

**Obrigatórias (10):**
`Age`, `Sex`, `Weight`, `Migratory_Pain`, `Lower_Right_Abd_Pain`,
`Contralateral_Rebound_Tenderness`, `Coughing_Pain`,
`Nausea`, `Loss_of_Appetite`, `Body_Temperature`,
`WBC_Count`, `CRP`, `US_Performed`

**Imputáveis (17):**
`BMI`, `Height`, `Dysuria`, `Stool`, `Peritonitis`, `Psoas_Sign`,
`Ipsilateral_Rebound_Tenderness`, `Neutrophil_Percentage`,
`Neutrophilia`, `RBC_Count`, `Hemoglobin`, `RDW`,
`Thrombocyte_Count`, `Ketones_in_Urine`, `RBC_in_Urine`,
`WBC_in_Urine`, `Appendix_on_US`, `Appendix_Diameter`, `Free_Fluids`

---

## 4. Motor Alvarado (`ml/alvarado.py`)

### 4.1 Descrição

Motor determinístico que implementa o Escore de Alvarado (MANTRELS). Zero dependência de ML. Todo texto clínico é hardcoded com referências DOI.

### 4.2 Critérios (8, máximo 10 pontos)

| Critério | Sigla | Pontos | Tipo | Categoria |
|----------|-------|--------|------|-----------|
| Dor migratória para FID | M | 1 | bool | Sintoma |
| Anorexia | A | 1 | bool | Sintoma |
| Náuseas/vômitos | N | 1 | bool | Sintoma |
| Dor em FID | T | 2 | bool | Sinal |
| Descompressão dolorosa | R | 1 | bool | Sinal |
| Temperatura > 37.3°C | E | 1 | threshold | Sinal |
| Leucócitos > 10.000/mm³ | L | 2 | threshold | Laboratorial |
| Neutrofilia | S | 1 | bool | Laboratorial |

### 4.3 Classificação

| Faixa | Classificação | Conduta |
|-------|--------------|---------|
| 0-4 | Baixo Risco | Alta com orientações |
| 5-6 | Risco Moderado | Observação hospitalar |
| 7-10 | Alto Risco | Avaliação cirúrgica imediata |

### 4.4 Interface

```python
calcular_alvarado(dados: dict) -> dict
# Input: 8 campos booleanos/numéricos
# Output: score, classificacao, label, cor, interpretacao,
#         conduta, disclaimer, detalhamento (8 itens com DOI)
```

**Referência:** Alvarado (1986). DOI:10.1016/S0196-0644(86)80468-2

---

## 5. Motor KNN (`ml/knn_engine.py`)

### 5.1 Descrição

K-Nearest Neighbors usando `sklearn.neighbors.KNeighborsClassifier` com distância euclidiana e权重 uniforme.

### 5.2 Treino

```python
treinar_knn(X: pd.DataFrame, y: pd.Series, k: int = None) -> dict
```

- Cross-validation com k=3,5,7,9,11 (ímpares, mínimo clínico=3)
- 5 folds (cv=5)
- Métrica: acurácia
- Seleciona o k com maior acurácia média
- Serializa modelo + scaler + imputer com joblib

### 5.3 Predição

```python
predizer(dados: dict, modelo_path: str) -> dict
```

- Carrega modelo serializado + scaler + imputer
- Imputa features opcionais ausentes pela mediana do treino
- Normaliza com MinMaxScaler
- Retorna classe, probabilidade, confiança, distâncias

### 5.4 Níveis de Confiança

| Probabilidade Máxima | Confiança |
|---------------------|-----------|
| >= 75% | Alta |
| >= 60% | Média |
| < 60% | Baixa — resultado inconclusivo |

### 5.5 Resultados Típicos (Config F)

- k ótimo: 5 ou 7
- Acurácia treino: ~80-85%
- Acurácia teste: ~75-78%
- AUC-ROC: ~0.82-0.85

**Referência:** Cover & Hart (1967). DOI:10.1109/TIT.1967.1053964

---

## 6. Motor SVM (`ml/svm_engine.py`)

### 6.1 Descrição

Support Vector Machine usando `sklearn.svm.SVC` com `probability=True` (Platt scaling).

### 6.2 Treino

```python
treinar_svm(X: pd.DataFrame, y: pd.Series, kernel: str = None) -> dict
```

- Grid search com 6 combinações:
  - kernel: rbf, linear
  - C: 0.1, 1.0, 10.0
- Cross-validation com 5 folds
- Seleciona melhor combo por acurácia

### 6.3 Predição

```python
predizer(dados: dict, modelo_path: str) -> dict
```

Mesmo padrão do KNN: carrega modelo + scaler + imputer. Usa limiar padrão 0.5 (Youden não aplicado na inferência para preservar sensibilidade).

### 6.4 Resultados Típicos

- Melhor kernel: rbf ou linear
- Melhor C: 1.0 ou 10.0
- Acurácia teste: ~78-81%
- AUC-ROC: ~0.83-0.87

**Referência:** Cortes & Vapnik (1995). DOI:10.1007/BF00994018

---

## 7. Avaliação (`ml/avaliador.py`)

### 7.1 Métricas Calculadas

| Métrica | Fórmula | Relevância Clínica |
|---------|---------|-------------------|
| Acurácia | (VP+VN)/Total | Taxa geral de acerto |
| Sensibilidade | VP/(VP+FN) | Capacidade de detectar doença |
| Especificidade | VN/(VN+FP) | Capacidade de excluir doença |
| VPP | VP/(VP+FP) | Chance de doença dado teste + |
| VPN | VN/(VN+FN) | Chance de não doença dado teste - |

### 7.2 Gráficos Gerados

| Gráfico | Arquivo | Tecnologia |
|---------|---------|------------|
| Matriz de Confusão KNN | `confusion_matrix_knn.png` | matplotlib + seaborn |
| Matriz de Confusão SVM | `confusion_matrix_svm.png` | matplotlib + seaborn |
| Curva ROC KNN | `roc_knn.png` | sklearn.metrics.roc_curve |
| Curva ROC SVM | `roc_svm.png` | sklearn.metrics.roc_curve |
| Curva PR KNN | `pr_knn.png` | precision_recall_curve |
| Curva PR SVM | `pr_svm.png` | precision_recall_curve |
| ROC Comparativa | `roc_comparativa.png` | Todos modelos sobrepostos |
| PR Comparativa | `pr_comparativa.png` | Todos modelos sobrepostos |

### 7.3 Limiar Ótimo de Youden

Calculado na curva ROC mas **NÃO aplicado na inferência** para preservar sensibilidade em triagem pediátrica. Exibido apenas como ferramenta pedagógica.

**Referência:** Youden (1950). DOI:10.1002/1097-0142(1950)3:1<32::AID-CNCR2820030106>3.0.CO;2-3

---

## 8. Workflow Orange3

O pipeline gera automaticamente `orange/validacao_knn.ows` — um workflow visual do Orange3 com:

```
CSV File Import → Select Columns → Data Sampler → kNN → Test and Score → Confusion Matrix
```

Permite validação visual no-code do modelo KNN, conforme ensinado na disciplina.

---

## 9. Modelos Serializados (`ml/modelos/`)

| Arquivo | Conteúdo | Formato |
|---------|----------|---------|
| `knn_model.joblib` | Modelo + k + features + acurácias + resultados_cv | joblib dict |
| `svm_model.joblib` | Modelo + kernel + C + features + acurácias | joblib dict |
| `knn_scaler.joblib` | MinMaxScaler ajustado | joblib |
| `imputer.joblib` | SimpleImputer + medianas opcionais | joblib dict |
| `metricas.json` | Todas as métricas de avaliação | JSON |

### 9.1 Estrutura do `knn_model.joblib`

```python
{
    'modelo': KNeighborsClassifier,   # modelo treinado
    'k': 5,                            # k ótimo
    'acuracia_treino': 0.83,           # acurácia no treino
    'acuracia_teste': 0.78,            # acurácia no teste
    'features': [...],                  # lista ordenada de features
    'features_opcionais': [...],       # features imputáveis
    'config': 'F',                     # config vencedora
    'resultados_cv': {                 # resultados por k
        '3': {'acuracia_media': 0.75, 'desvio_padrao': 0.03},
        ...
    },
}
```
