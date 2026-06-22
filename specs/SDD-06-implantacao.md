# SDD-06 — Implantação e Configuração

**Versão:** 1.0  
**Status:** Final  
**Autor:** Engenharia Reversa  
**Data:** 2026-06-21  
**Sistema:** APPSPEC — Sistema de Apoio ao Diagnóstico de Apendicite

---

## 1. Resumo

O APPSPEC é uma aplicação Python que pode ser executada localmente. O setup completo envolve: criação de ambiente virtual, instalação de dependências, execução do pipeline ML (download do dataset, pré-processamento, treino KNN e SVM, avaliação) e inicialização do servidor web FastAPI.

---

## 2. Pré-requisitos

- **Python:** 3.10+ (testado nas versões 3.10, 3.11, 3.12)
- **pip:** Atualizado (>= 24.0)
- **Sistema:** Windows, Linux ou macOS
- **Conexão com internet:** Necessária apenas para download do dataset (UCI id=938)

---

## 3. Instalação

### 3.1 Ambiente Virtual

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar (Windows Git Bash)
source .venv/Scripts/activate

# Ativar (Windows PowerShell)
.venv\Scripts\activate

# Ativar (Linux/macOS)
source .venv/bin/activate
```

### 3.2 Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Dependências (requirements.txt)

```
fastapi>=0.115.0,<1.0
uvicorn[standard]>=0.34.0,<1.0
jinja2>=3.1.0,<4.0
sqlalchemy>=2.0.0,<3.0
aiosqlite>=0.20.0,<1.0
pydantic>=2.0.0,<3.0
python-multipart>=0.0.18,<1.0
scikit-learn==1.4.*
pandas>=2.0,<3.0
numpy>=1.24,<2.0
joblib>=1.3
ucimlrepo>=0.0.3
matplotlib>=3.7
seaborn>=0.12
```

---

## 4. Pipeline ML (Setup)

### 4.1 Execução Completa

```bash
python pipeline.py setup
```

Executa 11 etapas automaticamente:

| Etapa | Descrição | Saída |
|-------|-----------|-------|
| 1/11 | Verificar dependências | Log de OK/ERRO |
| 2/11 | Baixar dataset (UCI id=938) | `data/regensburg_raw.csv` |
| 3/11 | Pré-processar dados (6 configs) | Dataset limpo e normalizado |
| 4/11 | Treinar KNN (cross-validation) | `ml/modelos/knn_model.joblib` |
| 5/11 | Serializar KNN + scaler + imputer | `knn_scaler.joblib`, `imputer.joblib` |
| 6/11 | Treinar SVM (grid search) | `ml/modelos/svm_model.joblib` |
| 7/11 | Avaliar (matrizes de confusão) | PNGs em `diagnostico/static/img/` |
| 8/11 | Salvar métricas completas | `ml/modelos/metricas.json` |
| 9/11 | Curvas ROC e PR | 6 PNGs de curvas |
| 10/11 | Gerar workflow Orange3 | `orange/validacao_knn.ows` |
| 11/11 | Resumo final | Tabela com métricas |

### 4.2 Idempotência

O pipeline é idempotente: se `data/regensburg_raw.csv` e `ml/modelos/knn_model.joblib` já existirem, as etapas correspondentes são puladas com `[OK]` em vez de reexecutadas.

---

## 5. Execução do Servidor

### 5.1 Via pipeline.py

```bash
python pipeline.py start
```

Inicia o servidor em `http://0.0.0.0:8082` com reload automático.

### 5.2 Direta com uvicorn

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload
```

### 5.3 Script start.sh (Linux/macOS)

```bash
./start.sh
```

Script automatizado que:
1. Detecta o interpretador Python disponível
2. Cria ambiente virtual se necessário
3. Atualiza pip
4. Instala dependências do `requirements.txt`
5. Executa `setup.py`
6. Inicia o servidor

---

## 6. Configurações

### 6.1 Arquivo de Configuração

`app/config.py` contém todas as constantes de path:

| Constante | Valor | Descrição |
|-----------|-------|-----------|
| BASE_DIR | `os.path.dirname(...)` | Raiz do projeto |
| MODELO_DIR | `ml/modelos/` | Modelos serializados |
| KNN_MODEL_PATH | `ml/modelos/knn_model.joblib` | Modelo KNN |
| SVM_MODEL_PATH | `ml/modelos/svm_model.joblib` | Modelo SVM |
| METRICAS_PATH | `ml/modelos/metricas.json` | Métricas |
| IMG_DIR | `diagnostico/static/diagnostico/img/` | Gráficos |
| STATIC_DIR | `diagnostico/static/` | Arquivos estáticos |
| TEMPLATES_DIR | `app/templates/` | Templates Jinja2 |
| DATABASE_URL | `sqlite:///db.sqlite3` | Banco de dados |

### 6.2 Variáveis do Servidor

| Parâmetro | Padrão | Flag |
|-----------|--------|------|
| Host | `0.0.0.0` | `--host` |
| Porta | `8082` | `--port` |
| Reload | `False` | `--reload` |

---

## 7. Estrutura de Dados Gerados

```
├── data/
│   └── regensburg_raw.csv          # Dataset baixado (idempotente)
├── ml/modelos/
│   ├── knn_model.joblib            # Modelo KNN treinado
│   ├── svm_model.joblib            # Modelo SVM treinado
│   ├── knn_scaler.joblib           # MinMaxScaler ajustado
│   ├── imputer.joblib              # SimpleImputer + medianas
│   └── metricas.json               # Todas as métricas
├── diagnostico/static/diagnostico/img/
│   ├── confusion_matrix_knn.png    # Matriz KNN
│   ├── confusion_matrix_svm.png    # Matriz SVM
│   ├── confusion_matrix.png        # Cópia da KNN
│   ├── roc_knn.png                 # ROC KNN
│   ├── roc_svm.png                 # ROC SVM
│   ├── roc_alvarado.png            # ROC Alvarado
│   ├── roc_comparativa.png         # ROC comparativa
│   ├── pr_knn.png                  # PR KNN
│   ├── pr_svm.png                  # PR SVM
│   ├── pr_alvarado.png             # PR Alvarado
│   └── pr_comparativa.png          # PR comparativa
├── orange/
│   └── validacao_knn.ows           # Workflow Orange3
└── db.sqlite3                      # Banco de dados (gerado na 1ª predição)
```

---

## 8. Portas e URLs

| Serviço | URL | Porta |
|---------|-----|-------|
| Web UI | `http://localhost:8082` | 8082 |
| API REST | `http://localhost:8082/api/v1` | 8082 |
| Docs OpenAPI | `http://localhost:8082/docs` | 8082 |
| Health Check | `http://localhost:8082/health` | 8082 |

---

## 9. Solução de Problemas

| Problema | Causa | Solução |
|----------|-------|---------|
| `ModuleNotFoundError` | Dependência faltando | `pip install -r requirements.txt` |
| Dataset não baixado | Sem internet | Baixar manualmente de `https://archive.ics.uci.edu/dataset/938` |
| Modelo não treinado | Setup não executado | `python pipeline.py setup` |
| Porta ocupada | :8082 em uso | `python pipeline.py start --port 8083` |
| Erro de permissão | Static dir não encontrado | Executar `pipeline.py` primeiro para gerar PNGs |
