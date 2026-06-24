import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO_DIR = os.path.join(BASE_DIR, "ml", "modelos")
KNN_MODEL_PATH = os.path.join(MODELO_DIR, "knn_model.joblib")
SVM_MODEL_PATH = os.path.join(MODELO_DIR, "svm_model.joblib")
METRICAS_PATH = os.path.join(MODELO_DIR, "metricas.json")
IMG_DIR = os.path.join(BASE_DIR, "diagnostico", "static", "diagnostico", "img")
STATIC_DIR = os.path.join(BASE_DIR, "diagnostico", "static")
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}"

# ── ML — Confiança ────────────────────────────────────────
LIMIAR_CONFIANCA_ALTA = 0.75
LIMIAR_CONFIANCA_MEDIA = 0.60
LIMIAR_DECISAO_PADRAO = 0.5

# ── KNN ───────────────────────────────────────────────────
K_MINIMO_CLINICO = 3
CANDIDATOS_K = [3, 5, 7, 9, 11]
KNN_METRIC = "euclidean"
KNN_WEIGHTS = "uniform"
KNN_CV_FOLDS = 5

# ── SVM ───────────────────────────────────────────────────
SVM_CANDIDATOS_KERNEL = [
    {"kernel": "rbf", "C": 0.1},
    {"kernel": "rbf", "C": 1.0},
    {"kernel": "rbf", "C": 10.0},
    {"kernel": "linear", "C": 0.1},
    {"kernel": "linear", "C": 1.0},
    {"kernel": "linear", "C": 10.0},
]
SVM_RANDOM_STATE = 42
SVM_CV_FOLDS = 5
SVM_PROBABILITY = True

# ── Alvarado ──────────────────────────────────────────────
ALVARADO_TEMP_THRESHOLD = 37.3
ALVARADO_LEUCOCITOS_THRESHOLD = 10000

# ── Preprocessamento ─────────────────────────────────────
PREPROC_TEST_SIZE = 0.30
PREPROC_VAL_FRAC = 0.50
PREPROC_RANDOM_STATE = 42

# ── CORS ──────────────────────────────────────────────────
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:8082,http://127.0.0.1:8082"
).split(",")
CORS_ALLOW_CREDENTIALS = True
CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS = ["Content-Type", "Authorization", "X-API-Key"]

# ── Auth / JWT ────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "appsec-dev-secret-key-nao-use-em-producao")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@appsec.local")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin12")

# ── Logging ───────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_BUFFER_SIZE = int(os.getenv("LOG_BUFFER_SIZE", "200"))

# ── Groq / LLM ─────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if GROQ_API_KEY.startswith("xai-"):
    GROQ_MODEL = os.getenv("GROQ_MODEL", "grok-beta")
    GROQ_BASE_URL = "https://api.x.ai/v1"
else:
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# ── RAG ─────────────────────────────────────────────────────
DOCS_DIR = os.path.join(BASE_DIR, "specs")
ML_SRC_DIR = os.path.join(BASE_DIR, "ml")
AUTH_SRC_DIR = os.path.join(BASE_DIR, "app", "auth")
RAG_CHUNK_SIZE = 1000
RAG_CHUNK_OVERLAP = 200
RAG_TOP_K = 5
RAG_TEMPERATURE = 0.2
RAG_SIMILARIDADE_MINIMA = 0.03
