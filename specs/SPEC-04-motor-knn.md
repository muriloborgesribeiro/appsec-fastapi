# Spec: APPSPEC-04 — Motor KNN

**Versão:** 1.0  
**Status:** Aprovada  
**Autor:** Neri  
**Data:** 2026-04-26  
**Depende de:** SPEC-00, SPEC-01, SPEC-02

---

## 1. Resumo

Implementa `ml/knn_engine.py` — motor de Machine Learning usando K-Nearest Neighbors (KNN) do scikit-learn, conforme ensinado na disciplina. Treina o modelo no dataset Regensburg pré-processado, encontra o melhor k por cross-validation, serializa o modelo com joblib e expõe uma função de predição com saída estruturada que inclui os metadados pedagógicos (k usado, distâncias, acurácia).

---

## 2. Contexto e Motivação

**Problema:** O projeto original mencionava KNN apenas "para comparação". Na disciplina, KNN é a tecnologia central ensinada — deve ser o motor principal do sistema.

**Evidências:** O Prof. Ronaldo ensinou KNN em aula, implementou com scikit-learn, usou Orange3 para validar e ensinou as métricas de avaliação. O sistema deve mostrar isso visivelmente.

**Por que agora:** Depende de SPEC-02 (dataset pré-processado disponível).

---

## 3. Goals

- [ ] G-01: Implementar KNN com scikit-learn conforme ensinado na disciplina
- [ ] G-02: Encontrar melhor k por cross-validation (k = 3, 5, 7, 9, 11)
- [ ] G-03: Serializar modelo treinado com joblib para uso em runtime
- [ ] G-04: Predição retorna metadados pedagógicos (k, acurácia, distâncias)
- [ ] G-05: Acurácia mínima de 80% no conjunto de teste

| Métrica | Baseline | Target | Prazo |
|---|---|---|---|
| Acurácia no teste | — | ≥ 80% | SPEC-04 |
| k ótimo identificado | — | Por cross-validation | SPEC-04 |
| Output com metadados pedagógicos | 0 | 5 campos pedagógicos | SPEC-04 |

---

## 4. Non-Goals

- NG-01: **NÃO** usa outros algoritmos — apenas KNN (`KNeighborsClassifier`)
- NG-02: **NÃO** faz feature engineering complexo — usa features da SPEC-02
- NG-03: **NÃO** otimiza hiperparâmetros além de k — sem GridSearchCV exaustivo
- NG-04: **NÃO** re-treina em runtime — modelo é carregado do joblib
- NG-05: **NÃO** usa features de imagem (ultrassom raw) — apenas dados tabulares

---

## 5. Usuários e Personas

**Primário:** `setup.py` — chama `treinar_knn()` durante o setup  
**Secundário:** `diagnostico/views.py` — chama `predizer()` a cada avaliação clínica

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| RF-01 | Treinar KNN com scikit-learn | Must | `KNeighborsClassifier` importado e usado |
| RF-02 | Cross-validation para k ótimo | Must | Testa k in [3, 5, 7, 9, 11], escolhe o de maior acurácia |
| RF-03 | Serializar modelo com joblib | Must | knn_model.joblib existe após setup |
| RF-04 | Carregar modelo serializado em predição | Must | joblib.load() usado em predizer() |
| RF-05 | Retornar probabilidade por classe | Must | `predict_proba()` ativo |
| RF-06 | Retornar metadados pedagógicos no output | Must | k, acurácia, distâncias dos vizinhos |
| RF-07 | Log pedagógico durante treino | Must | Imprime cada k testado com sua acurácia |

### 6.2 Fluxo de Treino (Happy Path — chamado pelo setup.py)

```
1. Recebe X_train, y_train, X_test, y_test do preprocessamento
2. Para cada k em [3, 5, 7, 9, 11]:
   a. Cria KNeighborsClassifier(n_neighbors=k, metric='euclidean')
   b. Executa cross_val_score com cv=5
   c. Loga: "  k={k}: acurácia média = {score:.1%}"
3. Seleciona k com maior acurácia média
4. Re-treina com k ótimo no conjunto de treino completo
5. Avalia no conjunto de teste → acurácia_teste
6. Serializa com joblib.dump() → ml/modelos/knn_model.joblib
7. Retorna dict com modelo, k, acurácia_treino, acurácia_teste
```

### 6.3 Fluxo de Predição (Happy Path — chamado por views.py)

```
1. Recebe dados clínicos do formulário (dict)
2. Carrega modelo via joblib.load('ml/modelos/knn_model.joblib')
3. Converte dados para array numpy com a mesma ordem das features de treino
4. Aplica normalização Min-Max (usando scaler salvo no setup)
5. Executa knn.predict() → classe predita (0 ou 1)
6. Executa knn.predict_proba() → [prob_negativo, prob_positivo]
7. Obtém distâncias dos k vizinhos via knn.kneighbors()
8. Retorna dict conforme interface SPEC-01
```

### 6.4 Log Pedagógico do Treino

```
[4/10] Treinando KNN com scikit-learn...
       Tecnologia: sklearn.neighbors.KNeighborsClassifier
       Referência: Cover & Hart (1967). Nearest neighbor pattern classification.
                   IEEE Trans. Inf. Theory. DOI:10.1109/TIT.1967.1053964

        Testando valores de k por cross-validation (cv=5):
          k=3:  acurácia = [X.X]%
          k=5:  acurácia = [X.X]%
          ...
          k=N:  acurácia = [X.X]%  ← MELHOR

        ✓ k ótimo selecionado: k=[N]
        ✓ Acurácia no conjunto de teste: [Y.Y]%
       ✓ Modelo serializado: ml/modelos/knn_model.joblib
```

### 6.5 Fluxos Alternativos

**Modelo já existe:**
1. setup.py detecta knn_model.joblib
2. Loga "✓ Modelo já treinado — pulando treino"
3. Carrega e valida modelo existente

**Acurácia abaixo de 80%:**
1. Loga aviso: "⚠️ Acurácia {valor}% abaixo do target de 80%"
2. Continua a execução — não para
3. Resultado exibido na UI com aviso de baixa acurácia

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|---|---|---|---|
| RNF-01 | Tempo de treino | < 30s | KNN com ~550 amostras de treino |
| RNF-02 | Tempo de predição | < 100ms | Carregamento do joblib incluso |
| RNF-03 | Tamanho do modelo serializado | < 5MB | KNN armazena os dados de treino |
| RNF-04 | Reprodutibilidade | random_state=42 em todo split | Mesma acurácia em cada execução |

---

## 8. Design e Interface

O output de `predizer()` alimenta o card KNN em `resultado.html`. A UI deve exibir visivelmente:
- "Algoritmo: KNN (K-Nearest Neighbors)" com badge de tecnologia da disciplina
- Valor de k utilizado
- Probabilidade de apendicite em percentual
- Acurácia do modelo como indicador de confiança
- Distância média dos k vizinhos (quanto menor, mais confiante)

---

## 9. Modelo de Dados

```python
# Output de treinar_knn()
{
    "modelo": KNeighborsClassifier,   # objeto sklearn
    "k": int,                          # k ótimo encontrado
    "acuracia_treino": float,          # acurácia cross-val
    "acuracia_teste": float,           # acurácia no conjunto de teste
    "features": list                   # ordem das features usadas
}

# Output de predizer()
{
    "classe_predita": int,             # 0 = sem apendicite, 1 = apendicite
    "label_predita": str,              # "Apendicite" | "Sem Apendicite"
    "probabilidade_apendicite": float, # 0.0 a 1.0
    "probabilidade_percentual": str,   # "83.2%"
    "k_vizinhos": int,                 # k do modelo
    "acuracia_modelo": float,          # acurácia no teste
    "distancia_media_vizinhos": float, # média das distâncias
    "confianca": str,                  # "Alta" | "Média" | "Baixa"
    "algoritmo": str,                  # "KNN — sklearn.neighbors.KNeighborsClassifier"
    "referencia_algoritmo": str,       # DOI do artigo original do KNN
    "disclaimer": str                  # aviso clínico obrigatório
}
```

### Lógica de confiança:
```python
# probabilidade >= 0.75 → "Alta"
# probabilidade >= 0.60 → "Média"
# probabilidade < 0.60  → "Baixa — resultado inconclusivo"
```

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|---|---|---|
| SPEC-02 (dataset pré-processado) | Obrigatória para treino | Sem dados, sem treino |
| scikit-learn | Obrigatória | Módulo inteiro não funciona |
| joblib | Obrigatória | Sem serialização/carregamento |
| numpy | Obrigatória | Conversão de dados para array |
| ml/modelos/knn_scaler.joblib | Obrigatória em predição | Normalização incorreta sem scaler |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---|---|---|
| Modelo não encontrado | joblib.load() FileNotFoundError | Retorna erro estruturado: `{"erro": "Modelo não treinado. Execute setup.py"}` |
| Feature faltando na entrada | KeyError ao montar array | Captura e retorna erro com nome da feature ausente |
| Probabilidade = 0.5 exato | Empate entre classes | Prediz classe 1 (apendicite) — conservador por segurança clínica |
| Dataset muito pequeno | < 50 amostras de treino | Loga aviso mas treina mesmo assim |
| k maior que amostras de treino | KNN falha | Reduz k automaticamente para n_amostras - 1 |

---

## 12. Segurança e Privacidade

- Modelo serializado (joblib) contém apenas parâmetros e dados de treino do Regensburg — sem dados de pacientes reais
- Sem chamadas de rede em runtime

---

## 13. Plano de Rollout

Gerado em SPEC-04. Testado via `python -c "from ml.knn_engine import testar_knn; testar_knn()"` antes de SPEC-05.

---

## 14. Open Questions

- OQ-01: Incluir features de ultrassom (appendix_diameter, free_fluids) no KNN? Enriquece o modelo mas o formulário web fica mais longo. Decisão: incluir como campos opcionais no formulário — se ausentes, KNN usa apenas as 8 features do Alvarado.
