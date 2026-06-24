# APPSPEC — API de Apoio ao Diagnóstico de Apendicite

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

API REST para apoio ao diagnóstico de apendicite aguda, combinando **Escala de Alvarado** (determinístico), **KNN** e **SVM** (Machine Learning), com **RAG + Groq** para tirar dúvidas sobre o projeto. Projeto didático da disciplina **Construção de APIs para Inteligência Artificial,** — UFG.

---

## Índice
- [Documentação completa da API](https://appsec-fastapi.onrender.com/docs)
- [Frontend](https://appsec-fastapi-frontend.onrender.com/)
- [Acesso ao frontend](#frontend)
- [Arquitetura](#arquitetura)
- [Stack Tecnológico](#stack-tecnológico)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Endpoints](#endpoints)
- [Autenticação e RBAC](#autenticação-e-rbac)
- [Usuários Padrão](#usuários-padrão)
- [Modelos de Machine Learning](#modelos-de-machine-learning)
- [Pipeline de Dados](#pipeline-de-dados)
- [RAG / LLM — Tire Dúvidas](#rag--llm--tire-dúvidas)
- [Logging](#logging)
- [Documentação Interativa](#documentação-interativa)
- [Configuração via Ambiente](#configuração-via-ambiente)
- [Como Executar](#como-executar)
- [Testes](#testes)
- [CI/CD](#cicd)
- [Especificações](#especificações)
- [Licença](#licença)

---

## Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│                       HTTP Client                             │
│                  (REST JSON / Swagger UI)                     │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼───────────────────────────────────────────┐
│                    FastAPI Application                               │
│                                                                      │
│  ┌────────────────────────────────────────────────────────┐          │
│  │  Middleware Chain                                      │          │
│  │  ├── CORSMiddleware      (CORS_ORIGINS configurável)   │          │
│  │  ├── SecurityHeaders     (CSP, HSTS, XFO, etc)         │          │
│  │  └── RequestLogging      (método, rota, status, tempo) │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                      │
│  ┌────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────┐ ┌───────┐   │
│  │ Auth   │ │ Diagnósticos │ │ Dúvidas    │ │ Logs     │ │Health │   │
│  │ (/auth)│ │ Métricas     │ │(/api/v1/   │ │(/api/v1/ │ │(/     │   │
│  │        │ │(/api/v1/...) │ │ duvidas)   │ │ logs)    │ │health)│   │
│  └───┬────┘ └──────┬───────┘ └─────┬──────┘ └────┬─────┘ └───┬───┘   │
└──────┼─────────────┼───────────────┼─────────────┼───────────┼───────┘
       │             │               │             │           │
┌──────▼─────────────▼───────────────▼─────────────▼───────────▼───────┐
│                      Service Layer                                   │
│     ┌────────────────────────────────────────────────────────┐       │
│     │  ml_service.py                                         │       │
│     │  ├── executar_modelos() → Alvarado + KNN + SVM         │       │
│     │  └── criar_historico()  → persiste no SQLite           │       │
│     ├────────────────────────────────────────────────────────┤       │
│     │  llm_service.py         → interface com Groq/xAI       │       │
│     ├────────────────────────────────────────────────────────┤       │
│     │  rag_service.py         → TF-IDF + cosine similarity   │       │
│     └────────────────────────────────────────────────────────┘       │
│     ┌────────────────────────────────────────────────────────┐       │
│     │  HistoryRepository (Repository Pattern)                │       │
│     │  save / find_by_id / list / delete                     │       │
│     └────────────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    Domain Layer (ML)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐   │
│  │ Alvarado │ │   KNN    │ │   SVM    │ │ Preprocess.    │   │
│  │ Score    │ │ Engine   │ │ Engine   │ │ + Avaliador    │   │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘   │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ SQLite       │  │ CSV Dataset  │  │ Modelos serializ.  │  │
│  │ (db.sqlite3) │  │ (Regensburg) │  │ (joblib / .json)   │  │
│  └──────────────┘  └──────────────┘  └────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Camadas

| Camada | Diretório | Responsabilidade |
|--------|-----------|------------------|
| **Web** | `app/` | Rotas FastAPI, middlewares, OpenAPI/Swagger |
| **Serviço** | `app/services/` | Orquestração dos modelos ML, LLM e RAG |
| **Repositório** | `app/repositories/` | Abstração de acesso a dados (CRUD) |
| **Domínio (ML)** | `ml/` | Algoritmos: Alvarado, KNN, SVM, Preprocessamento, Avaliação |
| **Dados** | `db.sqlite3`, `data/`, `ml/modelos/` | Persistência: banco, dataset, modelos serializados |
| **Autenticação** | `app/auth/` | JWT, bcrypt, RBAC |

---

## Stack Tecnológico

| Categoria | Tecnologia | Versão |
|-----------|-----------|--------|
| Framework | FastAPI | >=0.115 |
| Servidor ASGI | uvicorn[standard] | >=0.34 |
| Templates | Jinja2 | >=3.1 |
| ORM | SQLAlchemy | >=2.0 |
| Banco | SQLite (aiosqlite) | 3.x |
| Validação | Pydantic | >=2.0 |
| ML | scikit-learn | 1.4.x |
| ML | pandas, numpy | >=2.0, >=1.24 |
| Serialização | joblib | >=1.3 |
| Auth | python-jose[cryptography], passlib[bcrypt], bcrypt | >=3.3, >=1.7, >=4.0 |
| LLM | openai (API compatível com Groq/xAI) | >=1.0 |
| Dataset | ucimlrepo | >=0.0.3 |
| Visualização | matplotlib, seaborn | >=3.7, >=0.12 |
| Lint / Type | ruff, mypy | — |

---

## Estrutura do Projeto

```
appsec-fastapi/
├── app/                           # Aplicação web
│   ├── main.py                    # FastAPI app, middlewares, lifespan
│   ├── config.py                  # Configurações centralizadas
│   ├── database.py                # SQLAlchemy engine + session
│   ├── models.py                  # ORM: DiagnosisHistory
│   ├── schemas.py                 # Schemas Pydantic
│   ├── logging_config.py          # Configuração de logging (stdout + buffer)
│   ├── auth/                      # Autenticação JWT + RBAC
│   │   ├── models.py              # ORM: User
│   │   ├── schemas.py             # Schemas de auth
│   │   ├── router.py              # Endpoints /auth
│   │   ├── dependencies.py        # Dependências FastAPI
│   │   └── utils.py               # JWT + bcrypt
│   ├── routers/
│   │   ├── api.py                 # Endpoints /api/v1 (diagnósticos + métricas)
│   │   ├── duvidas.py             # Endpoint /api/v1/duvidas (RAG + LLM)
│   │   └── logs.py                # Endpoint /api/v1/logs (admin)
│   ├── repositories/
│   │   └── historico_repo.py      # Repository pattern
│   └── services/
│       ├── ml_service.py          # Orquestração dos modelos
│       ├── llm_service.py         # Interface com Groq/xAI
│       └── rag_service.py         # TF-IDF + busca por similaridade
├── ml/                            # Machine Learning
│   ├── alvarado.py                # Escala de Alvarado
│   ├── knn_engine.py              # KNN
│   ├── svm_engine.py              # SVM
│   ├── preprocessamento.py        # Pré-processamento
│   ├── avaliador.py               # Métricas e gráficos
│   ├── protocolo.py               # Protocolo typing
│   ├── _confianca.py              # Nível de confiança
│   └── modelos/                   # Modelos serializados (joblib)
├── data/                          # Dataset Regensburg (raw + processed)
├── diagnostico/
│   └── static/diagnostico/img/    # Gráficos (ROC, PR, matriz confusão)
├── specs/                         # Documentação SDD/SPEC
├── tests/                         # Testes (pytest)
├── orange/                        # Workflows Orange3
│   └── validacao_knn.ows
├── pipeline.py                    # Pipeline de treino dos modelos ML
├── start.sh                       # Script de inicialização
├── render.yaml                    # Configuração de deploy Render.com
├── .env.example                   # Template de variáveis de ambiente
├── .github/workflows/ci.yml       # CI/CD GitHub Actions
├── pyproject.toml                 # Metadados + config. ferramentas
└── requirements.txt               # Dependências Python
```

---

## Endpoints

### Autenticação (`/auth`)

| Método | Rota | Auth | Papéis | Descrição |
|--------|------|------|--------|-----------|
| POST | `/auth/register` | ❌ | — | Registrar novo usuário |
| POST | `/auth/login` | ❌ | — | Login → JWT token |
| GET | `/auth/me` | ✅ | qualquer | Dados do usuário atual |
| GET | `/auth/users` | ✅ | admin | Listar todos os usuários |

### Diagnósticos (`/api/v1`)

| Método | Rota | Auth | Papéis | Descrição |
|--------|------|------|--------|-----------|
| POST | `/api/v1/diagnosticos` | ✅ | admin, professional | Criar diagnóstico (Alvarado + KNN + SVM) |
| GET | `/api/v1/diagnosticos` | ✅ | admin, professional, viewer | Listar diagnósticos (paginado + filtros) |
| GET | `/api/v1/diagnosticos/{id}` | ✅ | admin, professional, viewer | Obter diagnóstico por ID |
| DELETE | `/api/v1/diagnosticos/{id}` | ✅ | admin | Remover diagnóstico |

### Métricas (`/api/v1`)

| Método | Rota | Auth | Papéis | Descrição |
|--------|------|------|--------|-----------|
| GET | `/api/v1/metricas` | ✅ | admin, professional, viewer | Métricas dos modelos ML |

### Dúvidas / RAG (`/api/v1`)

| Método | Rota | Auth | Papéis | Descrição |
|--------|------|------|--------|-----------|
| POST | `/api/v1/duvidas` | ✅ | admin, professional, viewer | Pergunta em linguagem natural → resposta baseada na documentação |

### Logs (`/api/v1`)

| Método | Rota | Auth | Papéis | Descrição |
|--------|------|------|--------|-----------|
| GET | `/api/v1/logs` | ✅ | admin | Visualizar logs recentes da aplicação |

### Health

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/health` | ❌ | Health check da aplicação |

---

## Autenticação e RBAC

### Fluxo

```
1. POST /auth/register  ───→  cria usuário (role: professional)
2. POST /auth/login     ───→  retorna { access_token, token_type }
3. Authorization: Bearer <token>  ───→  endpoints protegidos
```

### Papéis

| Papel | Acesso |
|-------|--------|
| `admin` | Total: CRUD diagnósticos + CRUD usuários + logs |
| `professional` | Criar e listar diagnósticos |
| `viewer` | Somente leitura (listar + métricas + dúvidas) |

### Implementação

- **Token JWT** com `sub` (username) e `role`, expiração configurável (padrão: 60 min)
- **Hash de senha** via bcrypt (passlib)
- **Dependência `require_role()`** protege cada endpoint, aplicando RBAC via `Depends()`
- **OpenAPI Security Scheme** configurado globalmente com exceção para endpoints públicos
- **Usuários padrão** criados automaticamente na inicialização (ver abaixo)

---

## Usuários Padrão

Criados automaticamente no `lifespan` da aplicação (primeira execução):

| Usuário | Senha | Papel |
|---------|-------|-------|
| `admin` | `admin123` | admin |
| `medico_01` | `senha123` | professional |
| `estudante_01` | `senha123` | viewer |

A senha do admin pode ser alterada via variável de ambiente `ADMIN_PASSWORD`.

---

## Modelos de Machine Learning

### Escala de Alvarado

- **Tipo:** Determinístico (regras clínicas)
- **Critérios:** 8 (dor migratória, anorexia, náuseas, dor FID, descompressão dolorosa, temperatura, leucócitos, neutrofilia)
- **Score:** 0–10
- **Classificação:** Baixa (0–4), Moderada (5–6), Alta (7–10)

### K-Nearest Neighbors (KNN)

- **Algoritmo:** `sklearn.neighbors.KNeighborsClassifier`
- **Hiperparâmetros:** k ótimo selecionado via cross-validation (candidatos: 3, 5, 7, 9, 11)
- **Métrica:** distância euclidiana
- **Pré-processamento:** MinMaxScaler + SimpleImputer

### Support Vector Machine (SVM)

- **Algoritmo:** `sklearn.svm.SVC` (com probability=True)
- **Grid Search:** kernel rbf/linear, C = 0.1/1.0/10
- **CV folds:** 5

### Performance

| Modelo | Acurácia | Sensibilidade | Especificidade | AUC-ROC |
|--------|----------|---------------|----------------|---------|
| Alvarado (corte >=5) | 68,1% | 83,3% | 46,8% | 0,719 |
| KNN (k=11) | 74,3% | 78,8% | 68,1% | 0,857 |
| **SVM** (linear, C=10) | **82,3%** | **83,3%** | **80,9%** | **0,922** |

---

## Pipeline de Dados

### Setup (treino) — `python pipeline.py setup`

```
Baixar dataset (UCI id=938)
  → Preprocessar (6 configs de features, A–F)
    → Treinar KNN (cross-validation)
      → Treinar SVM (grid search)
        → Avaliar (matriz confusão, ROC, PR)
          → Salvar modelos (joblib) + métricas (JSON) + gráficos (PNG)
```

### Predição (runtime)

```
POST /api/v1/diagnosticos
  → Validar entrada (Pydantic)
    → Mapear campos (Português → Inglês do dataset)
      → Executar Alvarado (determinístico)
        → Executar KNN (carrega modelo joblib)
          → Executar SVM (carrega modelo joblib)
            → Persistir no SQLite
              → Retornar JSON com HATEOAS
```

---

## RAG / LLM — Tire Dúvidas

O endpoint `POST /api/v1/duvidas` implementa um sistema de **perguntas e respostas** sobre o projeto usando **RAG** (Retrieval-Augmented Generation):

1. **Indexação:** Documentos da pasta `specs/`, `ml/`, `app/auth/` e `README.md` são divididos em chunks de 1000 caracteres (com 200 de overlap)
2. **Busca:** TF-IDF + similaridade cosseno encontra os chunks mais relevantes (top-5, threshold mínimo 0,03)
3. **Geração:** O prompt com os chunks + pergunta é enviado para a **Groq API** (modelo `llama-3.3-70b-versatile`) ou **xAI** (modelo `grok-beta`)
4. **Resposta:** O LLM sintetiza a resposta em português, citando as fontes utilizadas

> Nota: Requer a variável de ambiente `GROQ_API_KEY` configurada.

---

## Logging

O sistema possui logging estruturado em duas camadas:

- **Técnico:** Registra toda requisição HTTP (método, rota, status, tempo de resposta) e erros do servidor
- **Clínico:** Anota no livro de ocorrências toda visita ao plantão

Os logs são armazenados em um **buffer circular em memória** (200 linhas) e podem ser consultados por administradores via `GET /api/v1/logs`.

Níveis configuráveis via `LOG_LEVEL` (INFO, DEBUG, WARNING, ERROR).

---

## Documentação Interativa

A documentação OpenAPI 3.1 é gerada automaticamente:

| URL | Descrição |
|-----|-----------|
| `http://localhost:8082/docs` | **Swagger UI** — explore e teste os endpoints |
| `http://localhost:8082/redoc` | **ReDoc** — visualização alternativa |
| `http://localhost:8082/openapi.json` | Schema raw |

A documentação inclui:
- Tags organizadas: `auth`, `diagnosticos`, `metricas`, `duvidas`, `logs`, `health`
- Esquema de segurança **Bearer JWT** com botão "Authorize"
- Exemplos de request/response em todos os schemas
- Códigos de status documentados (200, 201, 204, 401, 403, 404, 409, 422, 503)
- Descrições detalhadas em português

---

## Configuração via Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `GROQ_API_KEY` | — | Chave da API Groq (ou xAI) para o RAG |
| `ADMIN_PASSWORD` | `admin123` | Senha do usuário admin inicial |
| `CORS_ORIGINS` | `http://localhost:8082` | Origens permitidas (CORS) |
| `LOG_LEVEL` | `INFO` | Nível de logging |
| `SECRET_KEY` | chave-dev | Chave para assinatura JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Expiração do token JWT em minutos |

Copie `.env.example` para `.env` e ajuste conforme necessário.

---

## Como Executar

### Com venv

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
# ou source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
cp .env.example .env        # configurar variáveis de ambiente
python pipeline.py setup    # treinar modelos (necessário na 1ª vez)
python app/main.py          # iniciar servidor (porta 8082)
```

### Com uv

```bash
uv venv
uv pip install -r requirements.txt
cp .env.example .env
uv run python pipeline.py setup
uv run python app/main.py
```

### Render.com

O arquivo `render.yaml` contém a configuração para deploy no Render.com com dois serviços:
- **appspec-backend:** API (este repositório)
- **appspec-frontend:** Interface web (https://github.com/muriloborgesribeiro/appsec-frontend)

---

## Testes

```bash
pytest tests/ -v
```

Testes que cobrem:

| Arquivo | Descrição |
|---------|-----------|
| `test_alvarado.py` | Cálculo, classificação, detalhamento do Alvarado Score |
| `test_knn.py` | Carregamento, predição, imputação, tratamento de erros |
| `test_svm.py` | Carregamento, predição, parâmetros kernel/C |
| `test_avaliador.py` | Matriz de confusão, métricas, curvas ROC/PR |
| `test_auth_unit.py` | Hash de senha, criação/decode de tokens |
| `test_auth_api.py` | Register, login, me — integração |
| `test_authorization_api.py` | RBAC (admin, professional, viewer) |
| `test_cors.py` | Headers CORS |
| `test_logs.py` | Endpoint de logs |

---

## CI/CD

O projeto utiliza **GitHub Actions** (`.github/workflows/ci.yml`) com os seguintes jobs:

- **lint:** ruff (formatação + lint), mypy (type checking)
- **security:** bandit (análise estática), pip-audit (vulnerabilidades)
- **test:** pytest com cobertura (Python 3.10 e 3.11)

---

## Especificações

Documentação detalhada em `specs/`:

| Documento | Descrição |
|-----------|-----------|
| `SDD-01-visao-geral.md` | Arquitetura em camadas |
| `SDD-02-api.md` | Especificação completa da API REST |
| `SDD-03-banco-dados.md` | Esquema do banco SQLite |
| `SDD-04-ml-pipeline.md` | Pipeline de Machine Learning |
| `SDD-05-interface-usuario.md` | Interface web (Jinja2/Bootstrap) |
| `SDD-06-implantacao.md` | Deploy e configuração |
| `SDD-07-mecanismos-seguranca.md` | Mecanismos anti-alucinação |
| `SPEC-03-motor-alvarado.md` | Especificação do Alvarado Score |
| `SPEC-04-motor-knn.md` | Especificação do KNN |
| `SPEC-05-modulo-avaliacao.md` | Especificação da avaliação |

---

## Licença

MIT
