# SPEC-06 — Rota de Dúvidas com RAG + Groq

**Versão:** 1.0  
**Status:** Rascunho  
**Autor:** —  
**Data:** 2026-06-22  
**Sistema:** APPSPEC — Sistema de Apoio ao Diagnóstico de Apendicite

---

## 1. Resumo

O APPSPEC expõe um endpoint de perguntas e respostas sobre o projeto utilizando **RAG (Retrieval-Augmented Generation)**. O usuário autenticado envia uma pergunta em linguagem natural; o sistema recupera os trechos mais relevantes da documentação do projeto usando **TF-IDF** (sklearn) e envia o contexto para a **API Groq** (modelo Llama 3 70B), que gera a resposta com base exclusivamente nos trechos fornecidos.

A rota é stateless (não persiste o histórico) e exige autenticação JWT.

---

## 2. Base URL

```
API:  http://localhost:8082/api/v1
Docs: http://localhost:8082/docs
```

---

## 3. Autenticação e Segurança

### 3.1 JWT Bearer Token

A rota utiliza o mesmo esquema de autenticação JWT das demais rotas do APPSPEC.

```
Authorization: Bearer <token>
```

### 3.2 Perfis de Acesso

| Papel | Acesso |
|-------|--------|
| `admin` | Perguntar |
| `professional` | Perguntar |
| `viewer` | Perguntar |

### 3.3 Chave da API Groq

A chave da API Groq é fornecida via variável de ambiente `GROQ_API_KEY`.  
Não é exposta em nenhum response da API.

### 3.4 Anti-hallucination

O system prompt do modelo instrui:

- Responder **exclusivamente** com base nos trechos da documentação fornecidos no contexto
- **Não** inventar informações, referências ou números não presentes nos trechos
- Informar "Não encontrei essa informação na documentação do projeto" quando a resposta não estiver disponível
- Citar a fonte (arquivo) de onde a informação foi extraída

---

## 4. Endpoint de Dúvidas

### 4.1 Perguntar

**`POST /api/v1/duvidas`**

Autenticação: **Bearer Token** — qualquer papel (`admin`, `professional`, `viewer`)

Recebe uma pergunta em linguagem natural sobre o projeto e retorna uma resposta gerada pela LLM com base na documentação.

#### Request Body

```json
{
  "pergunta": "Como o escore de Alvarado classifica o risco de apendicite?"
}
```

| Campo | Tipo | Obrigatório | Validação | Descrição |
|-------|------|-------------|-----------|-----------|
| pergunta | string | sim | 10–1000 caracteres | Pergunta sobre o projeto em português |

#### Response `200 OK`

```json
{
  "pergunta": "Como o escore de Alvarado classifica o risco de apendicite?",
  "resposta": "O escore de Alvarado classifica o risco em três faixas:\n- **Baixa Probabilidade** (0–4): risco baixo, conduta expectante\n- **Moderada Probabilidade** (5–6): risco moderado, observação clínica\n- **Alta Probabilidade** (7–10): risco alto, avaliacao cirurgica imediata\n\nFonte: `specs/SPEC-03-motor-alvarado.md` e `ml/alvarado.py`.",
  "contexto_utilizado": [
    "specs/SPEC-03-motor-alvarado.md (trecho sobre faixas de classificacao)",
    "ml/alvarado.py (trecho sobre interpretacao do score)"
  ],
  "modelo": "llama3-70b-8192"
}
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| pergunta | string | Pergunta enviada pelo usuário (eco) |
| resposta | string | Resposta gerada pela LLM com base na documentação |
| contexto_utilizado | list[string] | Arquivos e trechos utilizados como contexto |
| modelo | string | Modelo da Groq utilizado para gerar a resposta |

#### Response `400 Bad Request`

```json
{
  "detail": "Pergunta deve ter entre 10 e 1000 caracteres"
}
```

#### Response `401 Unauthorized`

```json
{
  "detail": "Token invalido ou ausente"
}
```

#### Response `503 Service Unavailable`

```json
{
  "detail": "Servico de IA temporariamente indisponivel"
}
```

---

## 5. Fluxo de Processamento

```
┌──────────┐     ┌──────────────────┐     ┌────────────────┐     ┌──────────┐
│ Usuário  │────▶│  RAG Service     │────▶│  LLM Service   │────▶│ Usuário  │
│ (pergunta)│    │  (TF-IDF Search) │     │  (Groq API)    │     │(resposta)│
└──────────┘     └──────────────────┘     └────────────────┘     └──────────┘
                        │                        ▲
                        ▼                        │
                 ┌──────────────┐         ┌──────────────┐
                 │ Documentos   │         │  Contexto     │
                 │ (specs/*.md, │         │  (top-5       │
                 │  README.md,  │         │   chunks)     │
                 │  código-fonte)│         └──────────────┘
                 └──────────────┘
```

### 5.1 Indexação (uma vez, na inicialização)

1. Ler todos os arquivos da documentação (`specs/*.md`, `README.md`, docstrings relevantes)
2. Dividir em chunks de ~1000 caracteres com overlap de 200
3. Vetorizar com `TfidfVectorizer` do sklearn
4. Manter matriz TF-IDF em memória

### 5.2 Consulta (a cada requisição)

1. Vetorizar a pergunta do usuário com o mesmo `TfidfVectorizer`
2. Calcular similaridade cosseno com todos os chunks
3. Selecionar os top-5 chunks mais similares
4. Montar prompt com sistema + contexto + pergunta
5. Enviar para a API da Groq (`llama3-70b-8192`, temperature 0.2)
6. Retornar resposta ao usuário

---

## 6. Schemas Pydantic

### DuvidaRequest

```python
class DuvidaRequest(BaseModel):
    pergunta: str  # 10–1000 caracteres
```

### DuvidaResponse

```python
class DuvidaResponse(BaseModel):
    pergunta: str
    resposta: str
    contexto_utilizado: list[str] = []
    modelo: str
```

### ErrorResponse (existente)

```python
class ErrorResponse(BaseModel):
    detail: str
```

---

## 7. Configurações

| Variável | Tipo | Padrão | Descrição |
|----------|------|--------|-----------|
| `GROQ_API_KEY` | string | `""` | Chave de API da Groq (obrigatória) |
| `GROQ_MODEL` | string | `"llama3-70b-8192"` | Modelo da Groq para geração |
| `GROQ_BASE_URL` | string | `"https://api.groq.com/openai/v1"` | URL base da API Groq |
| `RAG_CHUNK_SIZE` | int | `1000` | Tamanho do chunk em caracteres |
| `RAG_CHUNK_OVERLAP` | int | `200` | Overlap entre chunks |
| `RAG_TOP_K` | int | `5` | Número de chunks recuperados |
| `RAG_TEMPERATURE` | float | `0.2` | Temperatura do modelo (0.0–1.0) |

---

## 8. Dependências

Além das dependências já existentes no projeto:

| Biblioteca | Versão | Uso |
|------------|--------|-----|
| `openai` | >=1.0 | Cliente HTTP para API da Groq (compatível com OpenAI) |

O **TF-IDF** é fornecido pelo `scikit-learn` (`sklearn.feature_extraction.text.TfidfVectorizer`), já instalado no projeto.

---

## 9. Códigos de Status

| Código | Uso |
|--------|-----|
| 200 | Pergunta respondida com sucesso |
| 400 | Pergunta inválida (fora dos limites de tamanho) |
| 401 | Token não fornecido, inválido ou expirado |
| 503 | Serviço de IA (Groq) indisponível |

---

## 10. Roteamento Completo (Atualizado)

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

# Dúvidas (RAG + Groq)
POST   /api/v1/duvidas              → perguntar          (200/400/503)

# Métricas
GET    /api/v1/metricas              → metricas_json      (200/404)

# Health Check
GET    /health                       → health             (200)
```

---

## 11. Exemplos de Perguntas

| Pergunta | Tópico |
|----------|--------|
| "Como o escore de Alvarado classifica o risco?" | Especificação do motor Alvarado |
| "Quais features o modelo KNN utiliza?" | ML Pipeline / Preprocessamento |
| "O que significa cada papel de usuário?" | Autenticação e RBAC |
| "Como executar o projeto localmente?" | README / Setup |
| "Qual a acurácia do modelo SVM?" | Métricas / Avaliação |

---

## 12. Possíveis Evoluções Futuras

- **Histórico de perguntas**: persistir perguntas e respostas em banco SQLite
- **Streaming**: responder em SSE (Server-Sent Events) para melhor UX
- **Embeddings semânticos**: substituir TF-IDF por `sentence-transformers` para melhor compreensão
- **Feedback**:允許 usuário avaliar a resposta (útil/não útil)
- **Múltiplos modelos**: permitir selecionar o modelo da Groq por requisição
