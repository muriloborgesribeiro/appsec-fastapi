# SDD-01 — Visão Geral da Arquitetura

**Versão:** 1.0  
**Status:** Final  
**Autor:** Engenharia Reversa  
**Data:** 2026-06-21  
**Sistema:** APPSPEC — Sistema de Apoio ao Diagnóstico de Apendicite

---

## 1. Resumo

O APPSPEC é um sistema web para apoio didático ao diagnóstico de apendicite aguda, desenvolvido como trabalho final da disciplina de Agentes Inteligentes (UFG). O sistema implementa três motores de classificação — Alvarado Score (determinístico), KNN (Machine Learning) e SVM (Machine Learning) — e os apresenta lado a lado para comparação pedagógica.

---

## 2. Stack Tecnológico

| Camada | Tecnologia | Versão | Função |
|--------|-----------|--------|--------|
| Framework Web | FastAPI | >=0.115 | Servidor web, rotas, injeção de dependência |
| Servidor ASGI | uvicorn | >=0.34 | Servidor HTTP assíncrono |
| ORM | SQLAlchemy | >=2.0 | Mapeamento objeto-relacional |
| Banco | SQLite | 3.x | Persistência de dados |
| Templates | Jinja2 | >=3.1 | Renderização HTML no servidor |
| Frontend | Bootstrap 5 | 5.x | Estilização CSS responsiva |
| ML | scikit-learn | 1.4.x | KNN, SVM, métricas de avaliação |
| ML | pandas | >=2.0 | Manipulação de dados |
| ML | joblib | >=1.3 | Serialização de modelos |
| Visualização | matplotlib + seaborn | - | Gráficos (matriz de confusão, ROC, PR) |
| Workflow Visual | Orange3 | - | Validação visual no-code (.ows) |
| Dataset | Regensburg (UCI id=938) | - | 782 pacientes pediátricos |

---

## 3. Arquitetura em Camadas

```
┌──────────────────────────────────────────────────────────────┐
│                     CLIENTE (Browser)                         │
│              HTML + Bootstrap 5 + Jinja2 Templates            │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP (GET/POST)
┌────────────────────────▼─────────────────────────────────────┐
│                CAMADA WEB (FastAPI + uvicorn)                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ diagnostico │  │  metricas    │  │  api (REST v1)       │ │
│  │ router(HTML)│  │  router(HTML)│  │  POST /diagnosticos  │ │
│  │             │  │              │  │  GET /diagnosticos   │ │
│  │             │  │              │  │  DELETE /diagnosticos│ │
│  │             │  │              │  │  GET /metricas       │ │
│  └─────────────┘  └──────────────┘  └──────────────────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                  CAMADA DE SERVIÇO (services/)                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  ml_service.py: executar_modelos(), criar_historico()    │  │
│  │  Orquestra Alvarado + KNN + SVM + persistência no banco │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                     CAMADA DE DOMÍNIO (ML)                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ │
│  │ Alvarado   │ │    KNN     │ │    SVM     │ │ Avaliador  │ │
│  │(alvarado   │ │(knn_engine)│ │(svm_engine)│ │(avaliador) │ │
│  │ .py)       │ │            │ │            │ │  .py)      │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ │
│  ┌──────────────────┐ ┌────────────────────────────────────┐ │
│  │ Preprocessamento │ │          Modelos (joblib/.json)    │ │
│  │(preprocessamento │ │                                    │ │
│  │ .py)             │ │                                    │ │
│  └──────────────────┘ └────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                    CAMADA DE DADOS                              │
│  ┌─────────────────────┐  ┌────────────────────────────────┐  │
│  │ SQLite (db.sqlite3) │  │ Dataset Regensburg (CSV)       │  │
│  │ DiagnosisHistory    │  │ data/regensburg_raw.csv        │  │
│  └─────────────────────┘  └────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 3.1 Camada Web (FastAPI)

Responsável por receber requisições HTTP e retornar respostas HTML ou JSON. Três routers:

- **diagnostico.router** (`/diagnosticos/`): Páginas HTML para formulário, resultado e histórico.
- **metricas.router** (`/metricas/`): Página HTML para métricas dos modelos (endpoint JSON em `/api/v1/metricas`).
- **api.router** (`/api/v1/`): API RESTful com endpoints JSON para integração.

### 3.2 Camada de Serviço

`app/services/ml_service.py` orquestra a execução dos três modelos e a persistência no banco:
- `executar_modelos(dados)`: Executa Alvarado, KNN e SVM em sequência.
- `criar_historico(db, dados, resultados)`: Persiste o resultado no SQLite.

### 3.3 Camada de Domínio (ML)

Cinco módulos em `ml/`:
- **alvarado.py**: Motor determinístico do Escore de Alvarado (8 critérios, max 10 pontos).
- **knn_engine.py**: Motor KNN com treino (cross-validation) e predição.
- **svm_engine.py**: Motor SVM com treino (kernel rbf/linear) e predição.
- **preprocessamento.py**: Carregamento, limpeza e normalização do dataset Regensburg.
- **avaliador.py**: Métricas (matriz de confusão, ROC, PR) e geração de gráficos.

### 3.4 Camada de Dados

- **SQLite** (`db.sqlite3`): Tabela `diagnostico_avaliacao` com histórico de avaliações.
- **CSV** (`data/regensburg_raw.csv`): Dataset bruto baixado do UCI.
- **Joblib** (`ml/modelos/`): Modelos serializados (KNN, SVM, scaler, imputer).
- **JSON** (`ml/modelos/metricas.json`): Métricas de avaliação persistidas.
- **PNG** (`diagnostico/static/diagnostico/img/`): Gráficos gerados (matriz de confusão, ROC, PR).

---

## 4. Fluxo de Dados

### 4.1 Setup Inicial (setup.py — 11 etapas)

```
[1]  verificar_dependencias()
[2]  baixar_dataset()        → data/regensburg_raw.csv (UCI id=938)
[3]  preprocessar_dados()    → Config vencedora (F: 33 features)
[4]  treinar_modelo()        → ml/modelos/knn_model.joblib
[5]  treinar_svm()           → ml/modelos/svm_model.joblib
[6]  avaliar_modelo()        → Gráficos PNG + metricas.json
[7]  atualizar_metricas()    → metricas.json (avaliação completa)
[8]  gerar_orange()          → orange/validacao_knn.ows
```

### 4.2 Fluxo de Predição (Runtime)

```
Usuário preenche formulário (8 campos clínicos)
       │
       ▼
POST /diagnosticos/avaliar (ou POST /api/v1/diagnosticos)
       │
       ▼
executar_modelos(dados)
       │
       ├──► _executar_alvarado() → ml/alvarado.calcular_alvarado()
       │       Score 0-10 + classificação (baixo/moderado/alto)
       │
       ├──► _executar_knn() → ml/knn_engine.predizer()
       │       Carrega knn_model.joblib + scaler + imputer
       │       classe_predita (0/1) + probabilidade + confiança
       │
       └──► _executar_svm() → ml/svm_engine.predizer()
               Carrega svm_model.joblib + scaler + imputer
               classe_predita (0/1) + probabilidade + confiança
       │
       ▼
criar_historico(db, dados, resultados)
       │
       ▼
DB: INSERT INTO diagnostico_avaliacao ...
       │
       ▼
Retorno: HTML (TemplateResponse) ou JSON (DiagnosticoResponse)
```

---

## 5. Estrutura de Diretórios

```
appsec-fastapi/
├── app/                          # Código da aplicação web
│   ├── main.py                   # Entry point FastAPI
│   ├── config.py                 # Configurações centralizadas
│   ├── database.py               # SQLAlchemy engine + session
│   ├── models.py                 # ORM: DiagnosisHistory
│   ├── schemas.py                # Pydantic: request/response
│   ├── routers/
│   │   ├── api.py                # REST API endpoints (/api/v1)
│   │   ├── diagnostico.py        # Web UI endpoints
│   │   └── metricas.py           # Métricas endpoints
│   ├── services/
│   │   └── ml_service.py         # Orquestração dos modelos
│   └── templates/                # Jinja2 templates
│       ├── base.html             # Layout base (Bootstrap 5)
│       ├── index.html            # Formulário clínico
│       ├── resultado.html        # Resultado da avaliação
│       ├── historico.html        # Histórico com filtros
│       └── metricas.html         # Dashboard de métricas
├── ml/                           # Código de Machine Learning
│   ├── alvarado.py               # Motor Alvarado Score
│   ├── knn_engine.py             # Motor KNN
│   ├── svm_engine.py             # Motor SVM
│   ├── preprocessamento.py       # Pré-processamento do dataset
│   ├── avaliador.py              # Avaliação e métricas
│   └── modelos/                  # Modelos serializados
│       ├── knn_model.joblib      # KNN treinado
│       ├── svm_model.joblib      # SVM treinado
│       ├── knn_scaler.joblib     # MinMaxScaler
│       ├── imputer.joblib        # SimpleImputer
│       └── metricas.json         # Métricas de avaliação
├── specs/                        # Especificações
├── data/                         # Dataset
│   └── regensburg_raw.csv        # Dataset Regensburg (UCI)
├── orange/                       # Workflow Orange3
│   └── validacao_knn.ows         # Pipeline visual KNN
├── diagnostico/                  # Arquivos estáticos
│   └── static/diagnostico/img/   # Gráficos PNG
├── .venv/                        # Ambiente virtual
├── setup.py                      # Pipeline de setup (11 etapas)
├── start.sh                      # Script de inicialização
└── requirements.txt              # Dependências Python
```

---

## 6. Configurações Centralizadas

`app/config.py` define todos os paths do sistema:

| Constante | Caminho |
|-----------|---------|
| BASE_DIR | Raiz do projeto |
| MODELO_DIR | `ml/modelos/` |
| KNN_MODEL_PATH | `ml/modelos/knn_model.joblib` |
| SVM_MODEL_PATH | `ml/modelos/svm_model.joblib` |
| METRICAS_PATH | `ml/modelos/metricas.json` |
| IMG_DIR | `diagnostico/static/diagnostico/img/` |
| STATIC_DIR | `diagnostico/static/` |
| TEMPLATES_DIR | `app/templates/` |
| DATABASE_URL | `sqlite:///db.sqlite3` |

---

## 7. Dependências Externas

Ver `requirements.txt` — 14 dependências principais agrupadas por função:

**Web:** fastapi, uvicorn, jinja2, python-multipart  
**Banco:** sqlalchemy, aiosqlite  
**Validação:** pydantic  
**ML:** scikit-learn, pandas, numpy, joblib, ucimlrepo  
**Gráficos:** matplotlib, seaborn
