# SDD-03 — Esquema do Banco de Dados

**Versão:** 1.0  
**Status:** Final  
**Autor:** Engenharia Reversa  
**Data:** 2026-06-21  
**Sistema:** APPSPEC — Sistema de Apoio ao Diagnóstico de Apendicite

---

## 1. Resumo

O sistema utiliza SQLite via SQLAlchemy 2.0 ORM com uma única tabela `diagnostico_avaliacao` que armazena o histórico completo de cada avaliação clínica, incluindo inputs do formulário, resultados dos três motores (Alvarado, KNN, SVM) e timestamp.

---

## 2. Tecnologia

- **Banco:** SQLite 3.x (arquivo `db.sqlite3` na raiz do projeto)
- **ORM:** SQLAlchemy 2.0 (DeclarativeBase)
- **Driver:** sqlite3 (síncrono) + aiosqlite (declarado mas não utilizado)
- **URL de Conexão:** `sqlite:///db.sqlite3`

---

## 3. Tabela: `diagnostico_avaliacao`

### 3.1 Definição ORM

```python
class DiagnosisHistory(Base):
    __tablename__ = "diagnostico_avaliacao"
```

### 3.2 Colunas

| Coluna | Tipo SQL | Tipo Python | Nulo | Padrão | Descrição |
|--------|----------|-------------|------|--------|-----------|
| id | INTEGER | int | PK | auto | Identificador único |
| dor_migratoria | BOOLEAN | bool | NOT NULL | - | Dor migratória para FID |
| anorexia | BOOLEAN | bool | NOT NULL | - | Perda de apetite |
| nauseas_vomitos | BOOLEAN | bool | NOT NULL | - | Náuseas ou vômitos |
| dor_fid | BOOLEAN | bool | NOT NULL | - | Dor à palpação em FID |
| descompressao_dolorosa | BOOLEAN | bool | NOT NULL | - | Sinal de Blumberg |
| temperatura | FLOAT | float | NOT NULL | - | Temperatura axilar em °C |
| leucocitos | INTEGER | int | NOT NULL | - | Leucócitos totais /mm³ |
| neutrofilia | BOOLEAN | bool | NOT NULL | - | Neutrofilia (>75%) |
| score_alvarado | INTEGER | int | NOT NULL | - | Alvarado Score (0-10) |
| classificacao_alvarado | VARCHAR(20) | str | NOT NULL | - | "baixo", "moderado" ou "alto" |
| predicao_knn | INTEGER | int | NULLABLE | - | Predição KNN (0 ou 1) |
| probabilidade_knn | FLOAT | float | NULLABLE | - | Probabilidade de apendicite (KNN) |
| confianca_knn | VARCHAR(20) | str | NOT NULL | - | Nível de confiança KNN |
| predicao_svm | INTEGER | int | NULLABLE | - | Predição SVM (0 ou 1) |
| probabilidade_svm | FLOAT | float | NULLABLE | - | Probabilidade de apendicite (SVM) |
| confianca_svm | VARCHAR(50) | str | NOT NULL | - | Nível de confiança SVM |
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

### 3.4 Índices

Nenhum índice explícito é definido no modelo ORM. SQLite cria índice implícito na PK `id`.

### 3.5 Observações sobre o Schema

1. **Colunas com nomes repetidos:** O modelo ORM especifica o nome da coluna SQL explicitamente com o mesmo nome do atributo Python (ex: `Column("dor_migratoria", Boolean)`), o que é redundante.
2. **`confianca_knn` NOT NULL:** Mesmo quando a predição KNN falha (modelo não treinado), o campo é salvo como string vazia `""`.
3. **`predicao_knn` / `predicao_svm` NULLABLE:** Permite que o registro seja criado mesmo se um dos modelos ML não estiver disponível.
4. **Sem índices de consulta:** Filtros por `classificacao_alvarado`, `predicao_knn`, `criado_em` são usados na listagem mas não têm índices — pode impactar performance com muitos registros.

---

## 4. Operações de Banco

### 4.1 Inserção

`app/services/ml_service.py:criar_historico()`:
1. Instancia `DiagnosisHistory` com todos os campos.
2. `db.add(historico)` → insere na sessão.
3. `db.commit()` → persiste.
4. `db.refresh(historico)` → carrega o id gerado.

### 4.2 Consultas

**Listagem com filtros** (`api.py:listar_diagnosticos` / `diagnostico.py:historico`):
```python
query = db.query(DiagnosisHistory)
if data_inicio:  query = query.filter(DiagnosisHistory.created_at >= data_inicio)
if data_fim:     query = query.filter(DiagnosisHistory.created_at < fim)
if classificacao: query = query.filter(DiagnosisHistory.alvarado_classificacao == classificacao)
if resultado_knn: query = query.filter(DiagnosisHistory.predicao_knn == int(resultado_knn))
if resultado_svm: query = query.filter(DiagnosisHistory.predicao_svm == int(resultado_svm))
query.order_by(DiagnosisHistory.created_at.desc()).offset(offset).limit(page_size)
```

**Busca por ID** (`api.py:obter_diagnostico`):
```python
db.query(DiagnosisHistory).filter(DiagnosisHistory.id == diagnostico_id).first()
```

---

## 5. Sessão e Conexão

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

**Nota:** Apesar de `get_db` ser `async def`, a sessão `SessionLocal()` é síncrona. O driver `aiosqlite` é declarado na DATABASE_URL mas substituído por `sqlite` puro no `create_engine`. Não há operações assíncronas reais no banco.
