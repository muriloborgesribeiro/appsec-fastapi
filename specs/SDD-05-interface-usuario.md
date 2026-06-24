# SDD-05 — Interface de Usuário

**Versão:** 1.1  
**Status:** Final  
**Autor:** Engenharia Reversa  
**Data:** 2026-06-21  
**Sistema:** APPSPEC — Sistema de Apoio ao Diagnóstico de Apendicite

---

## 1. Resumo

A interface web é construída com **Jinja2 Templates** renderizados no servidor, estilizados com **Bootstrap 5** (CDN). São 5 templates HTML que compõem: formulário clínico, resultado da avaliação, histórico com filtros, dashboard de métricas e layout base.

---

## 2. Stack de Frontend

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| Jinja2 | >=3.1 | Templates server-side |
| Bootstrap 5 | 5.3.x (CDN) | CSS responsivo, componentes |
| Bootstrap Icons | CDN | Ícones |
| Chart.js (CDN) | 4.x | Gráficos no dashboard de métricas |
| HTML5 | - | Estrutura semântica |

---

## 3. Templates

### 3.1 `base.html` — Layout Base

`app/templates/base.html` (68 linhas)

- Navbar Bootstrap 5 com links para todas as páginas
- Container responsivo (`container-fluid`)
- Bloco `{% block content %}` para conteúdo específico
- Footer com créditos: "Disciplina: Construção de APIs para Inteligência Artificial, — UFG | Prof. Rogério Rodrigues Carvalho"
- Inclusão de Bootstrap 5 CSS/JS via CDN

### 3.2 `index.html` — Formulário Clínico

`app/templates/index.html` (80 linhas)

- **Header:** Título e descrição do sistema
- **Disclaimer vermelho:** "AVISO: Este sistema é uma ferramenta de apoio didática..."
- **Formulário** com 8 campos:
  - 6 checkboxes (sintomas/sinais booleanos)
  - 2 inputs numéricos (temperatura: step=0.1, leucócitos)
- **Botão:** "Calcular Risco" (post para `/diagnosticos/avaliar`)
- Layout 2 colunas (Bootstrap `row` + `col-md-6`)

### 3.3 `resultado.html` — Resultado da Avaliação

`app/templates/resultado.html` (94 linhas)

- **Disclaimer** em destaque (bg-warning)
- **3 colunas lado a lado** comparando os três modelos:

| Coluna | Conteúdo |
|--------|----------|
| Esquerda | **Alvarado Score** — score, classificação (badge colorido), conduta |
| Centro | **KNN** — classe predita, probabilidade percentual, confiança (badge), k vizinhos |
| Direita | **SVM** — classe predita, probabilidade percentual, confiança (badge), kernel |

- Badge Bootstrap com cor dinâmica: `success` (baixo), `warning` (moderado), `danger` (alto)
- Disclaimer Alvarado com DOI
- Disclaimer ML com referência ao dataset Regensburg

### 3.4 `historico.html` — Histórico de Avaliações

`app/templates/historico.html` (130 linhas)

- **Filtros** (barra horizontal):
  - Data início / Data fim (input date)
  - Classificação Alvarado (select: todas/baixo/moderado/alto)
  - Resultado KNN (select: todos/0/1)
  - Resultado SVM (select: todos/0/1)
- **Tabela** com colunas:
  ID, Data/Hora, Score Alv., Classificação, KNN (classe + prob), SVM (classe + prob), Ações
- Badge de classificação com cor
- **Botão de exclusão** por linha (ícone lixeira, `btn-outline-danger`)
  - Confirmação via `confirm()` nativo do navegador
  - Requisição `DELETE /api/v1/diagnosticos/{id}` via `fetch()`
  - Animação de fade-out (300ms) seguida de remoção da linha
  - Tratamento de erro: 404 (já removido → recarrega página), outros (exibe alerta)
- Mensagem "Nenhum resultado encontrado" se vazio
- Máximo 50 registros, ordenados por data decrescente

### 3.5 `metricas.html` — Dashboard de Métricas

`app/templates/metricas.html` (183 linhas)

Seções (cada uma com fallback se dado indisponível):

1. **Status dos Modelos:** Badges indicando se KNN e SVM estão treinados
2. **Configuração Vencedora:** Nome, descrição, features usadas, target 80%
3. **Hiperparâmetros:** k ótimo, acurácia CV, acurácia teste
4. **Matrizes de Confusão:** 2 imagens PNG (KNN e SVM)
5. **Curvas ROC:** Imagens para KNN, SVM e comparativa
6. **Curvas Precision-Recall:** Imagens para KNN, SVM e comparativa
7. **Comparativo Alvarado vs KNN vs SVM:** Tabela com todas as métricas
8. **Data Leakage:** Explicação do leakage detectado e corrigido

- Gráficos gerados com Chart.js para métricas interativas (quando dados disponíveis)

---

## 4. Rotas HTML

| Método | Path | Template | Função |
|--------|------|----------|--------|
| GET | `/` | - | Redireciona para `/diagnosticos/` |
| GET | `/diagnosticos/` | `index.html` | Exibe formulário |
| POST | `/diagnosticos/avaliar` | `resultado.html` | Processa avaliação |
| GET | `/diagnosticos/historico` | `historico.html` | Histórico com filtros |
| GET | `/metricas/` | `metricas.html` | Dashboard de métricas |
| GET | `/health` | - | JSON: `{"status":"ok"}` |

---

## 5. Mapeamento Formulário → Modelos

| Campo Formulário | Alvarado | Dataset (KNN/SVM) |
|-----------------|----------|-------------------|
| dor_migratoria | dor_migratoria | Migratory_Pain |
| anorexia | anorexia | Loss_of_Appetite |
| nauseas_vomitos | nauseas_vomitos | Nausea |
| dor_fid | dor_fid | Lower_Right_Abd_Pain |
| descompressao_dolorosa | descompressao_dolorosa | Ipsilateral_Rebound_Tenderness |
| temperatura | temperatura | Body_Temperature |
| leucocitos | leucocitos | WBC_Count |
| neutrofilia | neutrofilia | Neutrophilia |

O mapeamento é definido em `ml/preprocessamento.py:MAPEAMENTO_SPEC_PARA_DATASET`.

---

## 6. Cores e Feedback Visual

| Classificação | Badge Bootstrap | Cor |
|---------------|----------------|-----|
| Baixo Risco | `bg-success` | Verde |
| Risco Moderado | `bg-warning` | Amarelo |
| Alto Risco | `bg-danger` | Vermelho |

| Confiança ML | Badge Bootstrap | Cor |
|-------------|----------------|-----|
| Alta | `bg-success` | Verde |
| Média | `bg-warning` | Amarelo |
| Baixa | `bg-danger` | Vermelho |
