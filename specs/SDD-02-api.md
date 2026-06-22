# SDD-02 — Especificação da API REST

**Versão:** 1.3  
**Status:** Final  
**Autor:** Engenharia Reversa  
**Data:** 2026-06-22  
**Sistema:** APPSPEC — Sistema de Apoio ao Diagnóstico de Apendicite

---

## 1. Resumo

O APPSPEC expõe uma API RESTful versionada (`/api/v1`) com 5 endpoints para criação, consulta, listagem e remoção de diagnósticos, além de consulta a métricas dos modelos. O módulo de autenticação (`/auth`) fornece 4 endpoints para registro, login e gerenciamento de usuários com JWT Bearer Token e controle de acesso baseado em papéis (RBAC). A API retorna respostas JSON padronizadas com links HATEOAS e schemas Pydantic tipados.

A documentação interativa é gerada automaticamente via OpenAPI 3.1 e acessível em `/docs` (Swagger UI) e `/redoc`.

---

## 2. Base URL

```
API:     http://localhost:8082/api/v1
Auth:    http://localhost:8082/auth
Docs:    http://localhost:8082/docs
```

---

## 3. Autenticação e Segurança

### 3.1 JWT Bearer Token

A API utiliza **JWT (JSON Web Token)** para autenticação stateless.

```
Authorization: Bearer <token>
```

### 3.2 Fluxo de Autenticação

1. `POST /auth/register` — criar usuário (perfil `professional`)
2. `POST /auth/login` — obter token JWT
3. Incluir token no header `Authorization` das requisições protegidas

### 3.3 Perfis de Acesso (RBAC)

| Papel | Acesso |
|-------|--------|
| `admin` | Total: criar, listar, deletar diagnósticos + gerenciar usuários |
| `professional` | Criar e listar diagnósticos |
| `viewer` | Somente leitura (listar diagnósticos e métricas) |

### 3.4 Endpoints Públicos

Os seguintes endpoints **não** exigem autenticação:

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`

### 3.5 CORS

Configurado com origens controladas via variável de ambiente `CORS_ORIGINS`.  
Padrão: `http://localhost:8082,http://127.0.0.1:8082`

### 3.6 Security Headers

Todos os responses incluem:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy` (restritiva)
- `Strict-Transport-Security: max-age=31536000`
- `Cache-Control: no-cache, no-store, must-revalidate`

### 3.7 Validação de Entrada

Pydantic com ranges fisiológicos: temperatura 35–42°C, leucócitos 1000–50000/mm³.

---

## 4. Endpoints de Diagnóstico

### 4.1 Criar Diagnóstico

**`POST /api/v1/diagnosticos`**

Autenticação: **Bearer Token** — papéis: `admin`, `professional`

Cria uma nova avaliação clínica executando os três motores (Alvarado, KNN, SVM).

#### Request Body

```json
{
  "dor_migratoria": true,
  "anorexia": false,
  "nauseas_vomitos": true,
  "dor_fid": true,
  "descompressao_dolorosa": false,
  "temperatura": 38.5,
  "leucocitos": 15000,
  "neutrofilia": true
}
```

| Campo | Tipo | Obrigatório | Validação | Descrição |
|-------|------|-------------|-----------|-----------|
| dor_migratoria | boolean | sim | — | Dor migratória para FID |
| anorexia | boolean | sim | — | Perda de apetite |
| nauseas_vomitos | boolean | sim | — | Náuseas ou vômitos |
| dor_fid | boolean | sim | — | Dor à palpação em FID |
| descompressao_dolorosa | boolean | sim | — | Sinal de Blumberg |
| temperatura | float | sim | 35.0 – 42.0 | Temperatura axilar em °C |
| leucocitos | float | sim | 1000 – 50000 | Leucócitos totais /mm³ |
| neutrofilia | boolean | sim | — | Neutrofilia (>75%) |

#### Response `201 Created`

```json
{
  "id": 42,
  "dor_migratoria": true,
  "anorexia": false,
  "nauseas_vomitos": true,
  "dor_fid": true,
  "descompressao_dolorosa": false,
  "temperatura": 38.5,
  "leucocitos": 15000,
  "neutrofilia": true,
  "alvarado": {
    "score": 7,
    "classificacao": "Alta Probabilidade",
    "label": "Alta",
    "cor": "#dc3545",
    "interpretacao": "Score >= 7 indica alta probabilidade de apendicite aguda...",
    "conduta": "Avaliacao cirurgica imediata...",
    "disclaimer": "AVISO: Esta estimativa NAO substitui avaliacao medica presencial.",
    "detalhamento": [
      {
        "criterio": "Dor migratória",
        "criterio_completo": "Dor migratória para FID",
        "presente": true,
        "pontos": 1,
        "pontos_max": 1,
        "categoria": "Sintomas",
        "referencia": "Alvarado, 1986. DOI:10.1016/S0196-0644(86)80468-2"
      }
    ]
  },
  "knn": {
    "classe_predita": 1,
    "label_predita": "Positivo",
    "probabilidade_apendicite": 0.92,
    "probabilidade_percentual": "92.0%",
    "k_vizinhos": 5,
    "acuracia_modelo": 0.89,
    "distancia_media_vizinhos": 0.35,
    "confianca": "Alta",
    "limiar_decisao": 0.5,
    "algoritmo": "K-Nearest Neighbors",
    "referencia_algoritmo": "Cover & Hart, 1967. DOI:10.1109/TIT.1967.1053964",
    "disclaimer": "AVISO: Este resultado e gerado por um modelo de Machine Learning...",
    "features_imputadas": []
  },
  "svm": {
    "classe_predita": 1,
    "label_predita": "Positivo",
    "probabilidade_apendicite": 0.87,
    "probabilidade_percentual": "87.0%",
    "kernel": "rbf",
    "C": 1.0,
    "acuracia_modelo": 0.91,
    "confianca": "Alta",
    "limiar_decisao": 0.5,
    "algoritmo": "Support Vector Machine",
    "referencia_algoritmo": "Cortes & Vapnik, 1995. DOI:10.1007/BF00994018",
    "disclaimer": "AVISO: Este resultado e gerado por um modelo de Machine Learning...",
    "features_imputadas": []
  },
  "_links": [
    { "href": "/api/v1/diagnosticos/42", "rel": "self", "method": "GET" },
    { "href": "/api/v1/diagnosticos", "rel": "collection", "method": "GET" }
  ]
}
```

#### Response `422 Unprocessable Entity`

```json
{
  "detail": "Dados inválidos — campos fora dos limites permitidos"
}
```

#### Response `503 Service Unavailable`

```json
{
  "detail": "Modelo ML indisponível"
}
```

---

### 4.2 Listar Diagnósticos

**`GET /api/v1/diagnosticos`**

Autenticação: **Bearer Token** — papéis: `admin`, `professional`, `viewer`

Retorna histórico paginado de diagnósticos com filtros opcionais.

#### Query Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| page | int | não (padrão: 1) | Número da página (>= 1) |
| page_size | int | não (padrão: 20) | Itens por página (1–100) |
| data_inicio | string | não | Filtrar por data início (YYYY-MM-DD) |
| data_fim | string | não | Filtrar por data fim (YYYY-MM-DD) |
| classificacao | string | não | Filtrar por classificação Alvarado |
| resultado_knn | string | não | Filtrar por resultado KNN (0 ou 1) |
| resultado_svm | string | não | Filtrar por resultado SVM (0 ou 1) |

#### Response `200 OK`

```json
{
  "items": [
    {
      "id": 42,
      "created_at": "2026-06-21T10:30:00",
      "dor_migratoria": true,
      "anorexia": false,
      "nauseas_vomitos": true,
      "dor_fid": true,
      "descompressao_dolorosa": false,
      "temperatura": 38.5,
      "leucocitos": 15000,
      "neutrofilia": true,
      "alvarado_score": 7,
      "alvarado_classificacao": "Alta Probabilidade",
      "predicao_knn": 1,
      "probabilidade_knn": 0.92,
      "predicao_svm": 1,
      "probabilidade_svm": 0.87,
      "_links": [
        { "href": "/api/v1/diagnosticos/42", "rel": "self", "method": "GET" }
      ]
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "_links": [
    { "href": "/api/v1/diagnosticos", "rel": "self", "method": "GET" },
    { "href": "/api/v1/diagnosticos?page=2&page_size=20", "rel": "next", "method": "GET" }
  ]
}
```

---

### 4.3 Obter Diagnóstico por ID

**`GET /api/v1/diagnosticos/{diagnostico_id}`**

Autenticação: **Bearer Token** — papéis: `admin`, `professional`, `viewer`

Retorna um diagnóstico específico. Dados vêm do banco SQLite — campos não persistidos ficam como `null`.

#### Path Parameters

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| diagnostico_id | int | ID do diagnóstico |

#### Response `200 OK`

```json
{
  "id": 42,
  "alvarado": { "score": 7, "classificacao": "Alta Probabilidade", "label": "", "cor": "" },
  "knn": { "classe_predita": 1, "probabilidade_apendicite": 0.92, "confianca": "Alta" },
  "svm": { "classe_predita": 1, "probabilidade_apendicite": 0.87, "confianca": "Alta" },
  "_links": [
    { "href": "/api/v1/diagnosticos/42", "rel": "self", "method": "GET" },
    { "href": "/api/v1/diagnosticos", "rel": "collection", "method": "GET" }
  ]
}
```

#### Response `404 Not Found`

```json
{
  "detail": "Diagnóstico não encontrado"
}
```

---

### 4.4 Deletar Diagnóstico

**`DELETE /api/v1/diagnosticos/{diagnostico_id}`**

Autenticação: **Bearer Token** — papel: `admin` apenas

Remove um diagnóstico do histórico.

#### Path Parameters

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| diagnostico_id | int | ID do diagnóstico |

#### Response `204 No Content`

Sem corpo na resposta.

#### Response `404 Not Found`

```json
{
  "detail": "Diagnóstico não encontrado"
}
```

---

### 4.5 Métricas

**`GET /api/v1/metricas`**

Autenticação: **Bearer Token** — papéis: `admin`, `professional`, `viewer`

Retorna as métricas de avaliação dos modelos ML em formato JSON.

#### Response `200 OK`

```json
{
  "config_selecionada": "F",
  "k_otimo": 5,
  "acuracia_teste": 0.78,
  "acuracia_cv": 0.75,
  "features_usadas": ["Age", "Sex", "WBC_Count", ...],
  "avaliacao_knn": { "vp": 45, "fp": 12, "fn": 8, "vn": 35 },
  "avaliacao_svm": { "vp": 47, "fp": 10, "fn": 6, "vn": 37 },
  "curvas_roc_pr": { "knn": { "auc_roc": 0.85 } }
}
```

#### Response `404 Not Found`

```json
{
  "detail": "Métricas não encontradas. Execute setup.py primeiro."
}
```

---

## 5. Endpoints de Autenticação

### 5.1 Registrar Usuário

**`POST /auth/register`**

Público (sem autenticação). Cria um novo usuário com perfil `professional`.

#### Request Body

```json
{
  "username": "joao.silva",
  "email": "joao.silva@email.com",
  "password": "segura123"
}
```

| Campo | Tipo | Validação | Descrição |
|-------|------|-----------|-----------|
| username | string | 3–50 caracteres | Nome de usuário único |
| email | string | máx. 120 caracteres | E-mail do usuário |
| password | string | 6–100 caracteres | Senha (hash bcrypt) |

#### Response `201 Created`

```json
{
  "id": 2,
  "username": "joao.silva",
  "email": "joao.silva@email.com",
  "role": "professional",
  "is_active": true
}
```

#### Response `409 Conflict`

```json
{
  "detail": "Username ja existe"
}
```

---

### 5.2 Login

**`POST /auth/login`**

Público (sem autenticação). Retorna um token JWT.

#### Request Body

```json
{
  "username": "joao.silva",
  "password": "segura123"
}
```

#### Response `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Response `401 Unauthorized`

```json
{
  "detail": "Credenciais invalidas"
}
```

---

### 5.3 Obter Usuário Atual

**`GET /auth/me`**

Autenticação: **Bearer Token** — qualquer papel.

#### Response `200 OK`

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@appsec.local",
  "role": "admin",
  "is_active": true
}
```

---

### 5.4 Listar Usuários

**`GET /auth/users`**

Autenticação: **Bearer Token** — papel: `admin` apenas.

#### Response `200 OK`

```json
[
  { "id": 1, "username": "admin", "email": "admin@appsec.local", "role": "admin", "is_active": true },
  { "id": 2, "username": "joao.silva", "email": "joao.silva@email.com", "role": "professional", "is_active": true }
]
```

---

## 6. Health Check

**`GET /health`**

Público (sem autenticação).

#### Response `200 OK`

```json
{
  "status": "ok",
  "app": "appspec-fastapi"
}
```

---

## 7. Schemas Pydantic

### DiagnosticoRequest
```python
class DiagnosticoRequest(BaseModel):
    dor_migratoria: bool           # Dor migratória para FID
    anorexia: bool                 # Perda de apetite
    nauseas_vomitos: bool          # Náuseas ou vômitos
    dor_fid: bool                  # Dor à palpação em FID
    descompressao_dolorosa: bool   # Sinal de Blumberg
    temperatura: float             # 35.0 – 42.0 °C
    leucocitos: float              # 1000 – 50000 /mm³
    neutrofilia: bool              # Neutrofilia (>75%)
```

### Link (HATEOAS)
```python
class Link(BaseModel):
    href: str
    rel: str       # "self" | "collection" | "prev" | "next"
    method: str    # "GET" (padrão)
```

### AlvaradoDetalhe
```python
class AlvaradoDetalhe(BaseModel):
    criterio: str
    criterio_completo: str
    presente: bool
    pontos: int
    pontos_max: int
    categoria: str
    referencia: str
```

### AlvaradoResult
```python
class AlvaradoResult(BaseModel):
    score: int
    classificacao: str
    label: str
    cor: str
    interpretacao: Optional[str] = None
    conduta: Optional[str] = None
    disclaimer: Optional[str] = None
    detalhamento: list[AlvaradoDetalhe] = []
```

### KnnResult
```python
class KnnResult(BaseModel):
    classe_predita: Optional[int] = None       # 0 = negativo, 1 = positivo
    label_predita: Optional[str] = None
    probabilidade_apendicite: Optional[float] = None  # 0 a 1
    probabilidade_percentual: Optional[str] = None
    k_vizinhos: Optional[int] = None
    acuracia_modelo: Optional[float] = None
    distancia_media_vizinhos: Optional[float] = None
    confianca: Optional[str] = None           # Alta / Média / Baixa
    limiar_decisao: Optional[float] = None
    algoritmo: Optional[str] = None
    referencia_algoritmo: Optional[str] = None
    disclaimer: Optional[str] = None
    features_imputadas: list[str] = []
```

### SvmResult
```python
class SvmResult(BaseModel):
    classe_predita: Optional[int] = None       # 0 = negativo, 1 = positivo
    label_predita: Optional[str] = None
    probabilidade_apendicite: Optional[float] = None
    probabilidade_percentual: Optional[str] = None
    kernel: Optional[str] = None              # rbf / linear
    C: Optional[float] = None                 # regularização
    acuracia_modelo: Optional[float] = None
    confianca: Optional[str] = None
    limiar_decisao: Optional[float] = None
    algoritmo: Optional[str] = None
    referencia_algoritmo: Optional[str] = None
    disclaimer: Optional[str] = None
    features_imputadas: list[str] = []
```

### DiagnosticoResponse
```python
class DiagnosticoResponse(BaseModel):
    id: int
    dor_migratoria: bool
    anorexia: bool
    nauseas_vomitos: bool
    dor_fid: bool
    descompressao_dolorosa: bool
    temperatura: float
    leucocitos: float
    neutrofilia: bool
    alvarado: AlvaradoResult
    knn: KnnResult
    svm: SvmResult
    _links: list[Link] = []
```

### DiagnosticoSummary
```python
class DiagnosticoSummary(BaseModel):
    id: int
    created_at: Optional[str] = None
    dor_migratoria: Optional[bool] = None
    anorexia: Optional[bool] = None
    nauseas_vomitos: Optional[bool] = None
    dor_fid: Optional[bool] = None
    descompressao_dolorosa: Optional[bool] = None
    temperatura: Optional[float] = None
    leucocitos: Optional[float] = None
    neutrofilia: Optional[bool] = None
    alvarado_score: Optional[int] = None
    alvarado_classificacao: Optional[str] = None
    predicao_knn: Optional[int] = None
    probabilidade_knn: Optional[float] = None
    predicao_svm: Optional[int] = None
    probabilidade_svm: Optional[float] = None
    _links: list[Link] = []
```

### DiagnosticosListResponse
```python
class DiagnosticosListResponse(BaseModel):
    items: list[DiagnosticoSummary]
    total: int
    page: int
    page_size: int
    _links: list[Link] = []
```

### ErrorResponse
```python
class ErrorResponse(BaseModel):
    detail: str
```

### Schemas de Autenticação

```python
class UserCreate(BaseModel):
    username: str   # 3–50 caracteres
    email: str      # máx. 120 caracteres
    password: str   # 6–100 caracteres (hash bcrypt)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str          # "admin" | "professional" | "viewer"
    is_active: bool

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

---

## 8. Códigos de Status

| Código | Uso |
|--------|-----|
| 200 | GET bem-sucedido |
| 201 | Recurso criado (POST) |
| 204 | Recurso removido (DELETE) |
| 401 | Token não fornecido, inválido ou expirado |
| 403 | Permissão insuficiente (papel não autorizado) ou usuário inativo |
| 404 | Recurso não encontrado |
| 409 | Conflito (username ou email já existem) |
| 422 | Dados inválidos (validação Pydantic) |
| 503 | Modelo ML indisponível |

---

## 9. Roteamento Completo

```
# Autenticação
POST   /auth/register                → register          (201/409)
POST   /auth/login                   → login             (200/401/403)
GET    /auth/me                      → me                (200/401)
GET    /auth/users                   → list_users        (200/403)

# Diagnósticos (API v1)
POST   /api/v1/diagnosticos          → criar_diagnostico  (201/422/503)
GET    /api/v1/diagnosticos          → listar_diagnosticos (200)
GET    /api/v1/diagnosticos/{id}     → obter_diagnostico  (200/404)
DELETE /api/v1/diagnosticos/{id}     → deletar_diagnostico (204/404)

# Métricas
GET    /api/v1/metricas              → metricas_json      (200/404)

# Health Check
GET    /health                       → health             (200)
```

---

## 10. Documentação Swagger

A documentação OpenAPI 3.1 é gerada automaticamente pelo FastAPI com:

- **Título:** "APPSPEC API — Sistema de Apoio ao Diagnóstico de Apendicite"
- **Versão:** 1.2.0
- **Tags:** `auth`, `diagnosticos`, `metricas`, `health`
- **Security Scheme:** Bearer JWT (global, exceto endpoints públicos)
- **Exemplos** em todos os schemas Pydantic
- **Respostas de erro** documentadas (401, 403, 404, 409, 422, 503)

Acessar:
- Swagger UI: `http://localhost:8082/docs`
- ReDoc: `http://localhost:8082/redoc`
- OpenAPI JSON: `http://localhost:8082/openapi.json`
