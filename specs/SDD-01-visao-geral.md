# SDD-01 — Visão Geral da Arquitetura

**Versão:** 1.1  
**Status:** Final  
**Autores:** Anahi Philbois, Francisco Neri e Murilo Borges Ribeiro  
**Data:** 2026-06-22  
**Sistema:** APPSPEC — Sistema de Apoio ao Diagnóstico de Apendicite

---

## 1. Resumo

O APPSPEC é um sistema web para apoio didático ao diagnóstico de apendicite aguda, desenvolvido como trabalho final da disciplina Construção de APIs para Inteligência Artificial, (UFG). O sistema implementa três motores de classificação — Alvarado Score (determinístico), KNN (Machine Learning) e SVM (Machine Learning) — e os apresenta lado a lado para comparação pedagógica. A aplicação segue uma arquitetura em 4 camadas com API RESTful documentada via OpenAPI/Swagger.

---

## 2. Stack Tecnológico

| Camada | Tecnologia | Versão | Função |
|--------|-----------|--------|--------|
| Framework Web | FastAPI | >=0.115 | Servidor web, rotas, injeção de dependência, OpenAPI |
| Servidor ASGI | uvicorn | >=0.34 | Servidor HTTP assíncrono |
| ORM | SQLAlchemy | >=2.0 | Mapeamento objeto-relacional |
| Banco | SQLite | 3.x | Persistência de dados |
| Validação | Pydantic | >=2.0 | Schemas de request/response |
| ML | scikit-learn | 1.4.x | KNN, SVM, métricas de avaliação |
| ML | pandas + numpy | >=2.0 / >=1.24 | Manipulação de dados |
| ML | joblib | >=1.3 | Serialização de modelos |
| Visualização | matplotlib + seaborn | - | Gráficos (matriz de confusão, ROC, PR) |
| Autenticação | python-jose + passlib | >=3.3 / >=1.7 | JWT + bcrypt |
| Dataset | Regensburg (UCI id=938) | - | 782 pacientes pediátricos |

---

## 3. Arquitetura em Camadas

```
┌──────────────────────────────────────────────────────────────────┐
│                      CLIENTE (HTTP Client)                         │
│              REST JSON + OpenAPI Docs (Swagger UI)                 │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTPS (REST)
┌────────────────────────▼─────────────────────────────────────────┐
│                    CAMADA WEB (FastAPI + uvicorn)                   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Middleware                                                    │  │
│  │  ├── CORSMiddleware (CORS_ORIGINS configurável)               │  │
│  │  └── SecurityHeadersMiddleware (X-Content-Type-Options,       │  │
│  │       X-Frame-Options, CSP, HSTS, Cache-Control)              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────┐  ┌────────────────────────────────────┐  │
│  │  Auth Router        │  │  API v1 Router                     │  │
│  │  (/auth)            │  │  (/api/v1)                         │  │
│  │  ├── POST /register │  │  ├── POST /diagnosticos            │  │
│  │  ├── POST /login    │  │  ├── GET  /diagnosticos            │  │
│  │  ├── GET  /me       │  │  ├── GET  /diagnosticos/{id}       │  │
│  │  └── GET  /users    │  │  ├── DELETE /diagnosticos/{id}     │  │
│  └─────────────────────┘  │  └── GET  /metricas                │  │
│                            └────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Health (/health) + Static Files (/static)                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│                   CAMADA DE SERVIÇO (services/)                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ml_service.py                                                │  │
│  │  ├── executar_modelos(dados) → roda Alvarado + KNN + SVM     │  │
│  │  └── criar_historico(db, dados, resultados) → persiste        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│                    CAMADA DE DOMÍNIO (ML)                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────┐ │
│  │ Alvarado     │ │ KNN          │ │ SVM          │ │Avaliador │ │
│  │(alvarado.py) │ │(knn_engine)  │ │(svm_engine)  │ │(avaliador│ │
│  │              │ │ .py)         │ │ .py)         │ │ .py)     │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────┘ │
│  ┌──────────────────┐ ┌─────────────────────────────────────────┐ │
│  │ Preprocessamento │ │ Modelos serializados (joblib / .json)   │ │
│  │(preprocessamento │ │ knn_model, svm_model, scaler, imputer,  │ │
│  │ .py)             │ │ metricas.json                            │ │
│  └──────────────────┘ └─────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│                     CAMADA DE DADOS                                 │
│  ┌──────────────────────┐  ┌───────────────────────────────────┐  │
│  │ SQLite (db.sqlite3)  │  │ Dataset Regensburg (CSV)          │  │
│  │ Tabelas:             │  │ data/regensburg_raw.csv           │  │
│  │ ├── diagnostico_     │  │ data/regensburg_processed.csv     │  │
│  │ │   avaliacao        │  │                                   │  │
│  │ └── users            │  │                                   │  │
│  └──────────────────────┘  └───────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Imagens PNG (diagnostico/static/diagnostico/img/)             │  │
│  │ confusion_matrix, ROC, PR curves                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.1 Camada Web (FastAPI)

Responsável por receber requisições HTTP e retornar respostas JSON. A camada web é composta por:

- **Middlewares globais:** CORS configurável via variável de ambiente `CORS_ORIGINS` e Security Headers (CSP, HSTS, X-Frame-Options, etc.)
- **Auth Router** (`/auth`): Endpoints de autenticação JWT (registro, login, perfil, listagem de usuários)
- **API v1 Router** (`/api/v1`): Endpoints REST protegidos por JWT + RBAC
- **Health** (`/health`): Endpoint público de health check

A documentação OpenAPI é gerada automaticamente e acessível em `/docs` (Swagger UI) e `/redoc` (ReDoc).

### 3.2 Camada de Repositório

`app/repositories/historico_repo.py` implementa o padrão **Repository** para abstrair operações de banco:

- `save()`: Persiste um diagnóstico
- `find_by_id()` / `find_by_id_or_404()`: Consulta por ID
- `list()`: Listagem paginada com filtros
- `delete()`: Remoção de registro

### 3.3 Camada de Serviço

`app/services/ml_service.py` orquestra a execução dos três modelos e a persistência:

- `executar_modelos(dados)`: Executa Alvarado, KNN e SVM em sequência, mapeando os campos do formulário (Português) para as colunas do dataset (Inglês)
- `criar_historico(db, dados, resultados)`: Persiste o resultado no SQLite via Repository

### 3.4 Camada de Domínio (ML)

Cinco módulos em `ml/`:

- **alvarado.py**: Motor determinístico do Escore de Alvarado (8 critérios, max 10 pontos, 3 faixas de risco)
- **knn_engine.py**: Motor KNN com treino (cross-validation k=3-11) e predição
- **svm_engine.py**: Motor SVM com treino (grid search kernel rbf/linear, C=0.1/1.0/10) e predição
- **preprocessamento.py**: Carregamento, limpeza e normalização do dataset Regensburg (6 configurações de features A-F)
- **avaliador.py**: Métricas (matriz de confusão, ROC, PR) e geração de gráficos PNG

### 3.5 Camada de Autenticação

`app/auth/` implementa autenticação stateless via JWT:

- **models.py**: Modelo SQLAlchemy `User` (username, email, hashed_password, role, is_active)
- **schemas.py**: Pydantic schemas para criação, login e resposta de usuários
- **utils.py**: Funções de hash (bcrypt), criação e validação de tokens JWT
- **dependencies.py**: Dependências FastAPI (`get_current_user`, `require_role`) para proteção de endpoints com RBAC

### 3.6 Camada de Dados

- **SQLite** (`db.sqlite3`): Tabelas `diagnostico_avaliacao` (histórico) e `users` (usuários)
- **CSV** (`data/regensburg_raw.csv`): Dataset bruto baixado do UCI Repository
- **Joblib** (`ml/modelos/`): Modelos serializados (KNN, SVM, scaler, imputer)
- **JSON** (`ml/modelos/metricas.json`): Métricas de avaliação persistidas
- **PNG** (`diagnostico/static/diagnostico/img/`): Gráficos gerados (matriz de confusão, ROC, PR)

---

## 4. Fluxo de Dados

### 4.1 Setup Inicial (setup.py — 11 etapas)

```
[1]  verificar_dependencias()
[2]  baixar_dataset()        → data/regensburg_raw.csv (UCI id=938)
[3]  preprocessar_dados()    → Config vencedora (F: 33 features)
[4]  treinar_knn()           → ml/modelos/knn_model.joblib
[5]  treinar_svm()           → ml/modelos/svm_model.joblib
[6]  avaliar_modelo()        → Gráficos PNG + metricas.json
[7]  atualizar_metricas()    → metricas.json (avaliação completa)
[8]  gerar_orange()          → orange/validacao_knn.ows
```

### 4.2 Fluxo de Predição (Runtime)

```
Cliente autenticado (JWT) → POST /api/v1/diagnosticos
        │
        ▼
require_role("admin", "professional")
        │
        ▼ Validação Pydantic (DiagnosticoRequest)
        │
        ▼ executar_modelos(dados)
        │
        ├──► AlvaradoMotor.executar()
        │       Score 0-10 + classificação + detalhamento
        │
        ├──► KnnMotor.executar()
        │       Carrega knn_model.joblib + scaler + imputer
        │       classe_predita (0/1) + probabilidade + confiança
        │
        └──► SvmMotor.executar()
                Carrega svm_model.joblib + scaler + imputer
                classe_predita (0/1) + probabilidade + confiança
        │
        ▼ Repository.save()
        │
        ▼ DiagnosticoResponse (JSON + HATEOAS _links)
```

---

## 5. Estrutura de Diretórios

```
appsec-fastapi/
├── app/                          # Aplicação web FastAPI
│   ├── main.py                   # Entry point + middlewares + OpenAPI
│   ├── config.py                 # Configurações centralizadas
│   ├── database.py               # SQLAlchemy engine + session
│   ├── models.py                 # ORM: DiagnosisHistory
│   ├── schemas.py                # Pydantic: request/response
│   ├── auth/                     # Autenticação JWT + RBAC
│   │   ├── models.py             # ORM: User
│   │   ├── schemas.py            # Pydantic: auth schemas
│   │   ├── router.py             # Endpoints /auth
│   │   ├── dependencies.py       # Dependências (get_current_user, require_role)
│   │   └── utils.py              # JWT + bcrypt utilities
│   ├── routers/
│   │   └── api.py                # REST API endpoints (/api/v1)
│   ├── repositories/
│   │   └── historico_repo.py     # HistoryRepository (CRUD)
│   └── services/
│       └── ml_service.py         # Orquestração dos modelos
├── ml/                           # Machine Learning
│   ├── alvarado.py               # Motor Alvarado Score
│   ├── knn_engine.py             # Motor KNN
│   ├── svm_engine.py             # Motor SVM
│   ├── preprocessamento.py       # Pré-processamento do dataset
│   ├── avaliador.py              # Avaliação e métricas
│   ├── protocolo.py              # Protocolo typing para modelos
│   ├── _confianca.py             # Calculadora de confiança
│   └── modelos/                  # Modelos serializados
│       ├── knn_model.joblib
│       ├── svm_model.joblib
│       ├── knn_scaler.joblib
│       ├── imputer.joblib
│       └── metricas.json
├── specs/                        # Documentação de especificação
│   ├── SDD-01-visao-geral.md
│   ├── SDD-02-api.md
│   ├── SDD-03-banco-dados.md
│   ├── SDD-04-ml-pipeline.md
│   ├── SDD-05-interface-usuario.md
│   ├── SDD-06-implantacao.md
│   ├── SDD-07-mecanismos-seguranca.md
│   ├── SPEC-03-motor-alvarado.md
│   ├── SPEC-04-motor-knn.md
│   └── SPEC-05-modulo-avaliacao.md
├── data/                         # Dataset
│   ├── regensburg_raw.csv
│   └── regensburg_processed.csv
├── orange/                       # Workflow Orange3
│   └── validacao_knn.ows
├── diagnostico/                  # Arquivos estáticos (frontend)
│   └── static/diagnostico/img/   # Gráficos PNG
├── tests/                        # Testes automatizados
│   ├── conftest.py               # Fixtures (in-memory SQLite)
│   ├── test_alvarado.py
│   ├── test_auth_api.py
│   ├── test_auth_unit.py
│   ├── test_authorization_api.py
│   ├── test_avaliador.py
│   ├── test_cors.py
│   ├── test_knn.py
│   └── test_svm.py
├── setup.py                      # Pipeline de setup (treino dos modelos)
├── start.sh                      # Script de inicialização
├── requirements.txt              # Dependências Python
├── pyproject.toml                # Config ruff + mypy
├── render.yaml                   # Deploy Render.com
└── db.sqlite3                    # Banco SQLite
```

---

## 6. Configurações Centralizadas

`app/config.py` define todos os paths e constantes do sistema:

| Constante | Caminho / Valor |
|-----------|----------------|
| BASE_DIR | Raiz do projeto |
| MODELO_DIR | `ml/modelos/` |
| KNN_MODEL_PATH | `ml/modelos/knn_model.joblib` |
| SVM_MODEL_PATH | `ml/modelos/svm_model.joblib` |
| METRICAS_PATH | `ml/modelos/metricas.json` |
| IMG_DIR | `diagnostico/static/diagnostico/img/` |
| STATIC_DIR | `diagnostico/static/` |
| DATABASE_URL | `sqlite:///db.sqlite3` |
| SECRET_KEY | Chave secreta JWT (configurável via env) |
| ACCESS_TOKEN_EXPIRE_MINUTES | 60 min (configurável via env) |
| CORS_ORIGINS | `http://localhost:8082,http://127.0.0.1:8082` (configurável via env) |

---

## 7. Dependências Externas

Ver `requirements.txt` — 17 dependências:

**Web:** fastapi, uvicorn, jinja2, python-multipart  
**Banco:** sqlalchemy, aiosqlite  
**Validação:** pydantic  
**ML:** scikit-learn, pandas, numpy, joblib, ucimlrepo  
**Gráficos:** matplotlib, seaborn  
**Auth:** python-jose[cryptography], passlib[bcrypt], bcrypt

---

## 8. Documentação da API

| URL | Descrição |
|-----|-----------|
| `http://localhost:8082/docs` | Swagger UI interativa |
| `http://localhost:8082/redoc` | ReDoc alternativa |
| `http://localhost:8082/openapi.json` | Schema OpenAPI 3.1 raw |

