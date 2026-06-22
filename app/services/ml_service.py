from sqlalchemy.orm import Session

from app.config import KNN_MODEL_PATH, SVM_MODEL_PATH
from app.models import DiagnosisHistory
from app.repositories.historico_repo import HistoryRepository
from ml.alvarado import AlvaradoMotor
from ml.knn_engine import KnnMotor
from ml.svm_engine import SvmMotor

MAPA_SPEC_PARA_DATASET = {
    "dor_migratoria": "Migratory_Pain",
    "anorexia": "Loss_of_Appetite",
    "nauseas_vomitos": "Nausea",
    "dor_fid": "Lower_Right_Abd_Pain",
    "descompressao_dolorosa": "Ipsilateral_Rebound_Tenderness",
    "temperatura": "Body_Temperature",
    "leucocitos": "WBC_Count",
    "neutrofilia": "Neutrophilia",
}


def _mapear_features_para_dataset(dados: dict) -> dict:
    def _valor(v):
        return 1 if dados.get(v) else 0

    return {
        MAPA_SPEC_PARA_DATASET["dor_migratoria"]: _valor("dor_migratoria"),
        MAPA_SPEC_PARA_DATASET["anorexia"]: _valor("anorexia"),
        MAPA_SPEC_PARA_DATASET["nauseas_vomitos"]: _valor("nauseas_vomitos"),
        MAPA_SPEC_PARA_DATASET["dor_fid"]: _valor("dor_fid"),
        MAPA_SPEC_PARA_DATASET["descompressao_dolorosa"]: _valor(
            "descompressao_dolorosa"
        ),
        MAPA_SPEC_PARA_DATASET["temperatura"]: float(dados.get("temperatura", 36.5)),
        MAPA_SPEC_PARA_DATASET["leucocitos"]: float(dados.get("leucocitos", 8000)),
        MAPA_SPEC_PARA_DATASET["neutrofilia"]: _valor("neutrofilia"),
        "Contralateral_Rebound_Tenderness": 0,
    }


def executar_modelos(dados: dict) -> dict:
    alvarado = AlvaradoMotor().executar(dados)
    features = _mapear_features_para_dataset(dados)
    knn = KnnMotor(KNN_MODEL_PATH).executar(features)
    svm = SvmMotor(SVM_MODEL_PATH).executar(features)
    return {"alvarado": alvarado, "knn": knn, "svm": svm}


def criar_historico(db: Session, dados: dict, resultados: dict) -> DiagnosisHistory:
    repo = HistoryRepository(db)
    return repo.save(dados, resultados)
