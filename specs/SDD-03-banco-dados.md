# SDD-03 — Esquema do Banco de Dados

**Versão:** 1.1  
**Status:** Final  
**Autor:** Engenharia Reversa  
**Data:** 2026-06-22  
**Sistema:** APPSPEC — Sistema de Apoio ao Diagnóstico de Apendicite

---

## 1. Resumo

O sistema utiliza SQLite via SQLAlchemy 2.0 ORM com duas tabelas: `diagnostico_avaliacao` (histórico de avaliações clínicas) e `users` (usuários do sistema com autenticação JWT).

---

## 2. Tecnologia

- **Banco:** SQLite 3.x (arquivo `db.sqlite3` na raiz do projeto)
- **ORM:** SQLAlchemy 2.0 (DeclarativeBase)
- **Driver:** sqlite3 (síncrono) + aiosqlite (declarado mas não utilizado)
- **URL de Conexão:** `sqlite:///db.sqlite3`

---

## 3. Tabela: `diagnostico_avaliacao`

### 3.1 Definição ORM

`app/models.py:DiagnosisHistory`

### 3.2 Colunas

| Coluna | Tipo SQL | Tipo Python | Nulo | Padrão | Descrição |
|--------|----------|-------------|------|--------|-----------|
| id | INTEGER | int | PK | auto | Identificador único |
| dor_migratoria | BOOLEAN | bool | NOT NULL | — | Dor migratória para FID |
| anorexia | BOOLEAN | bool | NOT NULL | — | Perda de apetite |
| nauseas_vomitos | BOOLEAN | bool | NOT NULL | — | Náuseas ou vômitos |
| dor_fid | BOOLEAN | bool | NOT NULL | — | Dor à palpação em FID |
| descompressao_dolorosa | BOOLEAN | bool | NOT NULL | — | Sinal de Blumberg |
| temperatura | FLOAT | float | NOT NULL | — | Temperatura axilar em °C |
| leucocitos | INTEGER | int | NOT NULL | — | Leucócitos totais /mm³ |
| neutrofilia | BOOLEAN | bool | NOT NULL | — | Neutrofilia (>75%) |
| score_alvarado | INTEGER | int | NOT NULL | — | Alvarado Score (0–10) |
| classificacao_alvarado | VARCHAR(20) | str | NOT NULL | — | "baixo", "moderado" ou "alto" |
| predicao_knn | INTEGER | int | NULLABLE | — | Predição KNN (0 ou 1) |
| probabilidade_knn | FLOAT | float | NULLABLE | — | Probabilidade de apendicite (KNN) |
| confianca_knn | VARCHAR(20) | str | NOT NULL | — | Nível de confiança KNN |
| predicao_svm | INTEGER | int | NULLABLE | — | Predição SVM (0 ou 1) |
| probabilidade_svm | FLOAT | float | NULLABLE | — | Probabilidade de apendicite (SVM) |
| confianca_svm | VARCHAR(50) | str | NOT NULL | — | Nível de confiança SVM |
| criado_em | DATETIME | datetime | NOT NULL | func.now() | Timestamp de criação |

### 3.3 DDL Equivalente

```sql
CREATE TABLE diagnostico_avaliacao (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    dor_migratoria              BOOLEAN NOT NULL,
    anorexia                    BOOLEAN NOT NULL,
    nauseas_vomitos             BOOLEAN NOT NULL,
    dor_fid                     BOOLEAN NOT NULL,
    descompressao_dolorosa      BOOLEAN NOT NULL,
    temperatura                 FLOAT NOT NULL,
    leucocitos                  INTEGER NOT NULL,
    neutrofilia                 BOOLEAN NOT NULL,
    score_alvarado              INTEGER NOT NULL,
    classificacao_alvarado      VARCHAR(20) NOT NULL,
    predicao_knn                INTEGER NULL,
    probabilidade_knn           FLOAT NULL,
    confianca_knn               VARCHAR(20) NOT NULL,
    predicao_svm                INTEGER NULL,
    probabilidade_svm           FLOAT NULL,
    confianca_svm               VARCHAR(50) NOT NULL,
    criado_em                   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Tabela: `users`

### 4.1 Definição ORM

`app/auth/models.py:User`

### 4.2 Colunas

| Coluna | Tipo SQL | Tipo Python | Nulo | Padrão | Descrição |
|--------|----------|-------------|------|--------|-----------|
| id | INTEGER | int | PK | auto | Identificador único |
| username | VARCHAR(50) | str | NOT NULL, UNIQUE, INDEX | — | Nome de usuário |
| email | VARCHAR(120) | str | NOT NULL, UNIQUE | — | E-mail do usuário |
| hashed_password | VARCHAR(255) | str | NOT NULL | — | Hash bcrypt da senha |
| role | VARCHAR(20) | str | NOT NULL | "professional" | Papel: admin / professional / viewer |
| is_active | BOOLEAN | bool | NOT NULL | True | Usuário ativo ou desativado |
| created_at | DATETIME | datetime | NOT NULL | func.now() | Timestamp de criação |

### 4.3 DDL Equivalente

```sql
CREATE TABLE users (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    username         VARCHAR(50) NOT NULL UNIQUE,
    email            VARCHAR(120) NOT NULL UNIQUE,
    hashed_password  VARCHAR(255) NOT NULL,
    role             VARCHAR(20) NOT NULL DEFAULT 'professional',
    is_active        BOOLEAN NOT NULL DEFAULT 1,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_users_username ON users (username);
CREATE INDEX ix_users_id ON users (id);
```

---

## 5. Operações de Banco

### 5.1 Inserção (Diagnóstico)

`app/services/ml_service.py:criar_historico()` → delega para `HistoryRepository.save()`:

1. Instancia `DiagnosisHistory` com todos os campos.
2. `db.add(historico)` → insere na sessão.
3. `db.commit()` → persiste.
4. `db.refresh(historico)` → carrega o id gerado.

### 5.2 Inserção (Usuário)

`app/auth/router.py:register()`:

1. Verifica unicidade de username e email.
2. Cria hash bcrypt da senha.
3. Instancia `User` com papel `professional`.
4. `db.add(user)`, `db.commit()`, `db.refresh(user)`.

### 5.3 Consultas (Diagnóstico)

**Listagem com filtros** (`api.py:listar_diagnosticos` → `HistoryRepository.list()`):
```python
query = db.query(DiagnosisHistory)
if data_inicio:   query = query.filter(DiagnosisHistory.created_at >= data_inicio)
if data_fim:      query = query.filter(DiagnosisHistory.created_at < fim)
if classificacao:  query = query.filter(DiagnosisHistory.alvarado_classificacao == classificacao)
if resultado_knn:  query = query.filter(DiagnosisHistory.predicao_knn == int(resultado_knn))
if resultado_svm:  query = query.filter(DiagnosisHistory.predicao_svm == int(resultado_svm))
query.order_by(DiagnosisHistory.id.desc()).offset(offset).limit(page_size)
```

**Busca por ID** (`HistoryRepository.find_by_id()`):
```python
db.query(DiagnosisHistory).filter(DiagnosisHistory.id == diagnostico_id).first()
```

### 5.4 Consultas (Usuário)

**Busca por username** (login):
```python
db.query(User).filter(User.username == payload.username).first()
```

**Listar todos** (admin):
```python
db.query(User).all()
```

### 5.5 Deleção

`HistoryRepository.delete()`:
1. Busca por ID (404 se não encontrado).
2. `db.delete(historico)`.
3. `db.commit()`.

---

## 6. Sessão e Conexão

```python
engine = create_engine(DATABASE_URL.replace("+aiosqlite", ""), echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Nota:** Apesar de `get_db` ser `async def`, a sessão `SessionLocal()` é síncrona. O driver `aiosqlite` é declarado na `DATABASE_URL` mas substituído por `sqlite` puro no `create_engine`. Não há operações assíncronas reais no banco.

---

## 7. Índices

- **diagnostico_avaliacao:** índice implícito na PK `id`. Sem índices adicionais — filtros por `classificacao_alvarado`, `predicao_knn`, `criado_em` podem impactar performance com muitos registros.
- **users:** índice explícito em `username` (via `index=True` no modelo ORM) e índice implícito na PK `id`.
