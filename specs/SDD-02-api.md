# SDD-02 — Especificação da API REST

**Versão:** 1.2  
**Status:** Final  
**Autor:** Engenharia Reversa  
**Data:** 2026-06-21  
**Sistema:** APPSPEC — Sistema de Apoio ao Diagnóstico de Apendicite

---

## 1. Resumo

O APPSPEC expõe uma API RESTful versionada (`/api/v1`) com 5 endpoints para criação, consulta, listagem e remoção de diagnósticos, além de consulta a métricas dos modelos. A API retorna respostas JSON padronizadas com links HATEOAS e schemas Pydantic tipados. Endpoints HTML também existem para interação via navegador.

---

## 2. Base URL

```
http://localhost:8082/api/v1
```

---

## 3. Autenticação e Segurança

Nenhuma autenticação implementada. Todos os endpoints são públicos.

A aplicação possui:
- **CORS:** configurado com `allow_origins=["*"]` via `CORSMiddleware`
- **Security headers:** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Content-Security-Policy`, `Strict-Transport-Security`, `Cache-Control`
- **Validação de entrada:** Pydantic com ranges fisiológicos (temperatura 35-42°C, leucócitos 1000-50000)

---

## 4. Endpoints

### 4.1 Criar Diagnóstico

**`POST /api/v1/diagnosticos`**

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
| dor_migratoria | boolean | sim | - | Dor migratória para FID |
| anorexia | boolean | sim | - | Perda de apetite |
| nauseas_vomitos | boolean | sim | - | Náuseas ou vômitos |
| dor_fid | boolean | sim | - | Dor à palpação em FID |
| descompressao_dolorosa | boolean | sim | - | Sinal de Blumberg |
| temperatura | float | sim | 35.0 – 42.0 | Temperatura axilar em °C |
| leucocitos | float | sim | 1000 – 50000 | Leucócitos totais /mm³ |
| neutrofilia | boolean | sim | - | Neutrofilia (>75%) |

#### Response `201 Created`

```json
{
  "id": 42,
  "alvarado": {
    "score": 7,
    "classificacao": "alto",
    "label": "Alto Risco",
    "cor": "danger",
    "interpretacao": "Score >= 7 indica alta probabilidade de apendicite aguda...",
    "conduta": "Avaliacao cirurgica imediata...",
    "disclaimer": "AVISO: Esta estimativa NAO substitui avaliacao medica presencial.",
    "detalhamento": [
      {
        "criterio": "Dor migratoria para FID",
        "criterio_completo": "Dor que iniciou em regiao periumbilical...",
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
    "label_predita": "Apendicite",
    "probabilidade_apendicite": 0.85,
    "probabilidade_percentual": "85.0%",
    "k_vizinhos": 5,
    "acuracia_modelo": 0.78,
    "distancia_media_vizinhos": 0.32,
    "confianca": "Alta",
    "limiar_decisao": 0.5,
    "algoritmo": "KNN -- sklearn.neighbors.KNeighborsClassifier",
    "referencia_algoritmo": "Cover & Hart, 1967. DOI:10.1109/TIT.1967.1053964",
    "disclaimer": "AVISO: Este resultado e gerado por um modelo de Machine Learning...",
    "features_imputadas": []
  },
  "svm": {
    "classe_predita": 1,
    "label_predita": "Apendicite",
    "probabilidade_apendicite": 0.78,
    "probabilidade_percentual": "78.0%",
    "kernel": "rbf",
    "C": 1.0,
    "acuracia_modelo": 0.81,
    "confianca": "Alta",
    "limiar_decisao": 0.5,
    "algoritmo": "SVM -- sklearn.svm.SVC",
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
  "detail": "Dados inválidos"
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

Retorna histórico paginado de diagnósticos com filtros opcionais.

#### Query Parameters

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| page | int | não (padrão: 1) | Número da página (>= 1) |
| page_size | int | não (padrão: 20) | Itens por página (1-100) |
| data_inicio | string | não | Filtrar por data início (YYYY-MM-DD) |
| data_fim | string | não | Filtrar por data fim (YYYY-MM-DD) |
| classificacao | string | não | Filtrar por classificação Alvarado |
| resultado_knn | string | não | Filtrar por resultado KNN (0/1) |
| resultado_svm | string | não | Filtrar por resultado SVM (0/1) |

#### Response `200 OK`

```json
{
  "items": [
    {
      "id": 42,
      "created_at": "2026-06-21T10:30:00",
      "alvarado_score": 7,
      "alvarado_classificacao": "alto",
      "predicao_knn": 1,
      "probabilidade_knn": 0.85,
      "predicao_svm": 1,
      "probabilidade_svm": 0.78,
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

Retorna um diagnóstico específico. Neste endpoint os dados vêm do banco SQLite, portanto apenas campos persistidos são retornados (campos não-persistidos ficam como `null` ou vazios).

#### Path Parameters

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| diagnostico_id | int | ID do diagnóstico |

#### Response `200 OK`

```json
{
  "id": 42,
  "alvarado": {
    "score": 7,
    "classificacao": "alto",
    "label": "",
    "cor": "",
    "interpretacao": null,
    "conduta": null,
    "disclaimer": null,
    "detalhamento": []
  },
  "knn": {
    "classe_predita": 1,
    "probabilidade_apendicite": 0.85,
    "confianca": "Alta",
    "label_predita": null,
    "probabilidade_percentual": null,
    "k_vizinhos": null,
    "acuracia_modelo": null,
    "distancia_media_vizinhos": null,
    "limiar_decisao": null,
    "algoritmo": null,
    "referencia_algoritmo": null,
    "disclaimer": null,
    "features_imputadas": []
  },
  "svm": {
    "classe_predita": 1,
    "probabilidade_apendicite": 0.78,
    "confianca": "Alta",
    "label_predita": null,
    "kernel": null,
    "C": null,
    "acuracia_modelo": null,
    "limiar_decisao": null,
    "algoritmo": null,
    "referencia_algoritmo": null,
    "disclaimer": null,
    "features_imputadas": []
  },
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

Retorna as métricas de avaliação dos modelos em formato JSON. Substitui o antigo `/metricas/json` (mantido como redirect para backward compatibility).

#### Response `200 OK`

```json
{
  "config_selecionada": "F",
  "k_otimo": 5,
  "acuracia_teste": 0.78,
  "acuracia_cv": 0.75,
  "features_usadas": ["Age", "Sex", "WBC_Count", ...],
  "avaliacao_knn": { "vp": 45, "fp": 12, "fn": 8, "vn": 35, ... },
  "avaliacao_svm": { "vp": 47, "fp": 10, "fn": 6, "vn": 37, ... },
  "curvas_roc_pr": { "knn": { "auc_roc": 0.85, ... }, ... }
}
```

#### Response `404 Not Found`

```json
{
  "detail": "Métricas não encontradas. Execute setup.py primeiro."
}
```

---

## 5. Schemas Pydantic

### DiagnosticoRequest
```python
class DiagnosticoRequest(BaseModel):
    dor_migratoria: bool
    anorexia: bool
    nauseas_vomitos: bool
    dor_fid: bool
    descompressao_dolorosa: bool
    temperatura: float    # ge=35.0, le=42.0
    leucocitos: float     # ge=1000, le=50000
    neutrofilia: bool
```

### Link
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
    classe_predita: Optional[int] = None
    label_predita: Optional[str] = None
    probabilidade_apendicite: Optional[float] = None
    probabilidade_percentual: Optional[str] = None
    k_vizinhos: Optional[int] = None
    acuracia_modelo: Optional[float] = None
    distancia_media_vizinhos: Optional[float] = None
    confianca: Optional[str] = None
    limiar_decisao: Optional[float] = None
    algoritmo: Optional[str] = None
    referencia_algoritmo: Optional[str] = None
    disclaimer: Optional[str] = None
    features_imputadas: list[str] = []
```

### SvmResult
```python
class SvmResult(BaseModel):
    classe_predita: Optional[int] = None
    label_predita: Optional[str] = None
    probabilidade_apendicite: Optional[float] = None
    probabilidade_percentual: Optional[str] = None
    kernel: Optional[str] = None
    C: Optional[float] = None
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
    alvarado: AlvaradoResult
    knn: KnnResult
    svm: SvmResult
    _links: list[Link]
```

### DiagnosticoSummary
```python
class DiagnosticoSummary(BaseModel):
    id: int
    created_at: Optional[str] = None
    alvarado_score: Optional[int] = None
    alvarado_classificacao: Optional[str] = None
    predicao_knn: Optional[int] = None
    probabilidade_knn: Optional[float] = None
    predicao_svm: Optional[int] = None
    probabilidade_svm: Optional[float] = None
    _links: list[Link]
```

### DiagnosticosListResponse
```python
class DiagnosticosListResponse(BaseModel):
    items: list[DiagnosticoSummary]
    total: int
    page: int
    page_size: int
    _links: list[Link]
```

### ErrorResponse
```python
class ErrorResponse(BaseModel):
    detail: str
```

---

## 6. Endpoints HTML (Web UI)

| Método | Path | Função | Response |
|--------|------|--------|----------|
| GET | `/diagnosticos/` | Formulário clínico | `index.html` |
| POST | `/diagnosticos/avaliar` | Executa avaliação | `resultado.html` |
| GET | `/diagnosticos/historico` | Histórico com filtros | `historico.html` |
| DELETE | `/api/v1/diagnosticos/{id}` | Remoção via botão na tabela de histórico | 204 No Content |
| GET | `/metricas/` | Dashboard de métricas | `metricas.html` |
| GET | `/` | Redireciona para `/diagnosticos/` | 302 Redirect |
| GET | `/health` | Health check | `{"status": "ok"}` |

> A página de histórico (`historico.html`) expõe um botão de exclusão por linha que consome o endpoint `DELETE /api/v1/diagnosticos/{id}` via JavaScript (`fetch()`). Não há rota HTML dedicada para exclusão — a operação é feita exclusivamente via API REST.

---

## 7. Códigos de Status

| Código | Uso |
|--------|-----|
| 200 | GET bem-sucedido |
| 201 | Recurso criado (POST) |
| 204 | Recurso removido (DELETE) |
| 302 | Redirecionamento |
| 404 | Recurso não encontrado |
| 422 | Dados inválidos (validação Pydantic) |
| 503 | Modelo ML indisponível |

---

## 8. Roteamento Completo

```
POST   /api/v1/diagnosticos                → criar_diagnostico     (201)
GET    /api/v1/diagnosticos                → listar_diagnosticos    (200)
GET    /api/v1/diagnosticos/{id}           → obter_diagnostico      (200/404)
DELETE /api/v1/diagnosticos/{id}           → deletar_diagnostico    (204/404)
GET    /api/v1/metricas                    → metricas_json          (200/404)
GET    /metricas/json                      → redirect /api/v1/metricas (302)
GET    /diagnosticos/                      → formulario             (HTML)
POST   /diagnosticos/avaliar               → avaliar                (HTML)
GET    /diagnosticos/historico             → historico              (HTML)
GET    /metricas/                          → pagina_metricas        (HTML)
GET    /                                   → redirect /diagnosticos (302)
GET    /health                             → health                 (200)
```
