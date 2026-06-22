# APPSPEC — API de Apoio ao Diagnóstico de Apendicite

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

API REST para apoio ao diagnóstico de apendicite aguda, combinando **Escala de Alvarado** (determinístico), **KNN** e **SVM** (Machine Learning). Projeto didático da disciplina **Agentes Inteligentes** — UFG.

---

## Índice

- [Arquitetura](#arquitetura)
- [Stack Tecnológico](#stack-tecnológico)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Endpoints](#endpoints)
- [Autenticação e RBAC](#autenticação-e-rbac)
- [Modelos de Machine Learning](#modelos-de-machine-learning)
- [Pipeline de Dados](#pipeline-de-dados)
- [Documentação Interativa](#documentação-interativa)
- [Como Executar](#como-executar)
- [Testes](#testes)

---

## Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│                       HTTP Client                             │
│                  (REST JSON / Swagger UI)                     │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼───────────────────────────────────┐
│                    FastAPI Application                         │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Middleware Chain                                        │   │
│  │  ├── CORSMiddleware      (CORS_ORIGINS configurável)     │   │
│  │  └── SecurityHeaders     (CSP, HSTS, XFO, etc)          │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │  Auth Router│  │  API v1 Router   │  │  Health + Static│  │
│  │  (/auth)    │  │  (/api/v1)       │  │  (/health,      │  │
│  │             │  │                  │  │   /static)      │  │
│  └──────┬──────┘  └────────┬─────────┘  └─────────────────┘  │
└─────────┼──────────────────┼──────────────────────────────────┘
          │                  │
┌─────────▼──────────────────▼──────────────────────────────────┐
│                    Service Layer                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  ml_service.py                                          │   │
│  │  ├── executar_modelos() → Alvarado + KNN + SVM         │   │
│  │  └── criar_historico()  → persiste no SQLite           │   │
│  └────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  HistoryRepository (Repository Pattern)                 │   │
│  │  save / find_by_id / list / delete                     │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    Domain Layer (ML)                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │
│  │ Alvarado │ │   KNN    │ │   SVM    │ │ Preprocess.    │  │
│  │ Score    │ │ Engine   │ │ Engine   │ │ + Avaliador    │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    Data Layer                                  │
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
| **Serviço** | `app/services/` | Orquestração dos modelos ML |
| **Repositório** | `app/repositories/` | Abstração de acesso a dados (CRUD) |
| **Domínio (ML)** | `ml/` | Algoritmos: Alvarado, KNN, SVM, Preprocessamento, Avaliação |
| **Dados** | `db.sqlite3`, `data/`, `ml/modelos/` | Persistência: banco, dataset, modelos serializados |
| **Autenticação** | `app/auth/` | JWT, bcrypt, RBAC |

---

## Stack Tecnológico

| Categoria | Tecnologia | Versão |
|-----------|-----------|--------|
| Framework | FastAPI | >=0.115 |
| Servidor ASGI | uvicorn | >=0.34 |
| ORM | SQLAlchemy | >=2.0 |
| Banco | SQLite | 3.x |
| Validação | Pydantic | >=2.0 |
| ML | scikit-learn | 1.4.x |
| ML | pandas, numpy | >=2.0, >=1.24 |
| Serialização | joblib | >=1.3 |
| Auth | python-jose, passlib[bcrypt] | >=3.3, >=1.7 |
| Visualização | matplotlib, seaborn | — |

---

## Estrutura do Projeto

```
appsec-fastapi/
├── app/                           # Aplicação web
│   ├── main.py                    # FastAPI app, middlewares, OpenAPI
│   ├── config.py                  # Configurações centralizadas
│   ├── database.py                # SQLAlchemy engine + session
│   ├── models.py                  # ORM: DiagnosisHistory
│   ├── schemas.py                 # Schemas Pydantic
│   ├── auth/                      # Autenticação JWT + RBAC
│   │   ├── models.py              # ORM: User
│   │   ├── schemas.py             # Schemas de auth
│   │   ├── router.py              # Endpoints /auth
│   │   ├── dependencies.py        # Dependências FastAPI
│   │   └── utils.py               # JWT + bcrypt
│   ├── routers/
│   │   └── api.py                 # Endpoints REST /api/v1
│   ├── repositories/
│   │   └── historico_repo.py      # Repository pattern
│   └── services/
│       └── ml_service.py          # Orquestração dos modelos
├── ml/                            # Machine Learning
│   ├── alvarado.py                # Escala de Alvarado
│   ├── knn_engine.py              # KNN
│   ├── svm_engine.py              # SVM
│   ├── preprocessamento.py        # Pré-processamento
│   ├── avaliador.py               # Métricas
│   ├── protocolo.py               # Protocolo typing
│   ├── _confianca.py              # Nível de confiança
│   └── modelos/                   # Modelos serializados
├── specs/                         # Documentação SDD/SPEC
├── tests/                         # Testes (pytest)
├── setup.py                       # Pipeline de treino
└── requirements.txt               # Dependências
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
| POST | `/api/v1/diagnosticos` | ✅ | admin, professional | Criar diagnóstico (executa Alvarado + KNN + SVM) |
| GET | `/api/v1/diagnosticos` | ✅ | admin, professional, viewer | Listar diagnósticos (paginado + filtros) |
| GET | `/api/v1/diagnosticos/{id}` | ✅ | admin, professional, viewer | Obter diagnóstico por ID |
| DELETE | `/api/v1/diagnosticos/{id}` | ✅ | admin | Remover diagnóstico |
| GET | `/api/v1/metricas` | ✅ | admin, professional, viewer | Métricas dos modelos ML |

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
| `admin` | Total: CRUD diagnósticos + CRUD usuários |
| `professional` | Criar e listar diagnósticos |
| `viewer` | Somente leitura (listar + métricas) |

### Implementação

- **Token JWT** com `sub` (username) e `role`, expiração configurável (padrão: 60 min)
- **Hash de senha** via bcrypt (passlib)
- **Dependência `require_role()`** protege cada endpoint, aplicando RBAC via `Depends()`
- **OpenAPI Security Scheme** configurado globalmente com exceção para endpoints públicos

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

---

## Pipeline de Dados

### Setup (treino) — `python pipeline.py`

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

## Documentação Interativa

A documentação OpenAPI 3.1 é gerada automaticamente:

| URL | Descrição |
|-----|-----------|
| `http://localhost:8082/docs` | **Swagger UI** — explore e teste os endpoints |
| `http://localhost:8082/redoc` | **ReDoc** — visualização alternativa |
| `http://localhost:8082/openapi.json` | Schema raw |

A documentação inclui:
- Tags organizadas: `auth`, `diagnosticos`, `metricas`, `health`
- Esquema de segurança **Bearer JWT** com botão "Authorize"
- Exemplos de request/response em todos os schemas
- Códigos de status documentados (200, 201, 204, 401, 403, 404, 409, 422, 503)
- Descrições detalhadas em português

---

## Como Executar

### Com venv

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
# ou source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
python pipeline.py              # treinar modelos (necessário na 1ª vez)
python app/main.py           # iniciar servidor (porta 8082)
```

### Com uv

```bash
uv venv
uv pip install -r requirements.txt
uv run python pipeline.py
uv run python app/main.py
```

---

## Testes

```bash
pytest tests/ -v
```

63 testes que cobrem:
- Alvarado Score (cálculo, classificação, detalhamento)
- API de autenticação (register, login, me, users)
- Autorização RBAC (perfis admin, professional, viewer)
- CORS e security headers
- KNN (carregamento, predição, imputação)
- SVM (carregamento, predição)
- Avaliador (matriz de confusão, métricas, gráficos)

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
