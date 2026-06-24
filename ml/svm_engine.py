import numpy as np
import pandas as pd
import joblib
import os
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score

from app.config import (
    SVM_MODEL_PATH,
    SVM_CANDIDATOS_KERNEL,
    SVM_RANDOM_STATE,
    SVM_CV_FOLDS,
    SVM_PROBABILITY,
    LIMIAR_DECISAO_PADRAO,
)
from ml.protocolo import ModeloMLProtocol
from ml._confianca import calcular_confianca
from ml.knn_engine import _carregar_imputer, _carregar_scaler, _montar_array

REFERENCIA_SVM = (
    "Cortes, C. & Vapnik, V. (1995). Support-vector networks. "
    "Machine Learning, 20(3), 273-297. DOI:10.1007/BF00994018"
)

LABELS_CLASSE = {0: "Sem Apendicite", 1: "Apendicite"}

DISCLAIMER_SVM = (
    "AVISO: Este resultado e gerado por um modelo de Machine Learning (SVM) "
    "treinado no dataset Regensburg (Marcinkevics et al., 2023). "
    "NAO substitui avaliacao medica presencial. "
    "Sistema exclusivamente didatico -- disciplina de Construção de APIs para Inteligência Artificial, (UFG)."
)


class SvmMotor:
    def __init__(self, modelo_path: str = SVM_MODEL_PATH):
        self.modelo_path = modelo_path

    def executar(self, dados: dict) -> dict:
        if not os.path.exists(self.modelo_path):
            return {
                "erro": f"Modelo SVM nao treinado. Execute setup.py. Path: {self.modelo_path}"
            }

        try:
            dados_modelo = joblib.load(self.modelo_path)
        except Exception as e:
            return {"erro": f"Erro ao carregar modelo SVM: {e}"}

        modelo = dados_modelo["modelo"]
        acuracia = dados_modelo.get("acuracia_teste", 0.0)
        features_ordem = dados_modelo["features"]

        modelo_dir = os.path.dirname(self.modelo_path)
        medianas_opcionais, features_opcionais = _carregar_imputer(modelo_dir)
        scaler = _carregar_scaler(modelo_dir)

        X_input, features_imputadas = _montar_array(
            dados, features_ordem, features_opcionais, medianas_opcionais
        )
        if isinstance(X_input, dict):
            return X_input

        if scaler is not None:
            X_input = pd.DataFrame(scaler.transform(X_input), columns=features_ordem)

        probabilidades = modelo.predict_proba(X_input)[0]
        prob_apendicite = float(probabilidades[1])
        classe_predita = int(modelo.predict(X_input)[0])
        confianca = calcular_confianca(prob_apendicite)

        return {
            "classe_predita": classe_predita,
            "label_predita": LABELS_CLASSE.get(
                classe_predita, f"Classe {classe_predita}"
            ),
            "probabilidade_apendicite": prob_apendicite,
            "probabilidade_percentual": f"{prob_apendicite:.1%}",
            "kernel": dados_modelo.get("kernel", "?"),
            "C": dados_modelo.get("C", 1.0),
            "acuracia_modelo": float(acuracia),
            "confianca": confianca,
            "limiar_decisao": LIMIAR_DECISAO_PADRAO,
            "algoritmo": "SVM -- sklearn.svm.SVC",
            "referencia_algoritmo": REFERENCIA_SVM,
            "disclaimer": DISCLAIMER_SVM,
            "features_imputadas": features_imputadas,
        }


def predizer(dados: dict, modelo_path: str = SVM_MODEL_PATH) -> dict:
    return SvmMotor(modelo_path).executar(dados)


def treinar_svm(X: pd.DataFrame, y: pd.Series, kernel: str | None = None) -> dict:
    if kernel is not None:
        candidatos = [{"kernel": kernel, "C": 1.0}]
    else:
        candidatos = SVM_CANDIDATOS_KERNEL

    n_amostras = len(X)
    melhor_config = candidatos[0]
    melhor_acuracia = 0.0
    resultados_cv = {}

    for cfg in candidatos:
        modelo_teste = SVC(
            kernel=cfg["kernel"],
            C=cfg["C"],
            probability=SVM_PROBABILITY,
            random_state=SVM_RANDOM_STATE,
        )
        cv_folds = min(SVM_CV_FOLDS, n_amostras)
        scores = cross_val_score(modelo_teste, X, y, cv=cv_folds, scoring="accuracy")
        acuracia_media = scores.mean()

        chave = f"{cfg['kernel']}_C{cfg['C']}"
        resultados_cv[chave] = {
            "kernel": cfg["kernel"],
            "C": cfg["C"],
            "acuracia_media": float(acuracia_media),
            "desvio_padrao": float(scores.std()),
            "scores": scores.tolist(),
        }
        if acuracia_media > melhor_acuracia:
            melhor_acuracia = acuracia_media
            melhor_config = cfg

    modelo_final = SVC(
        kernel=melhor_config["kernel"],
        C=melhor_config["C"],
        probability=SVM_PROBABILITY,
        random_state=SVM_RANDOM_STATE,
    )
    modelo_final.fit(X, y)
    acuracia_treino = float(modelo_final.score(X, y))

    return {
        "modelo": modelo_final,
        "kernel": melhor_config["kernel"],
        "C": melhor_config["C"],
        "acuracia_treino": acuracia_treino,
        "resultados_cv": resultados_cv,
    }


def testar_svm():
    print("=" * 50)
    print("  TESTE DO MOTOR SVM")
    print("=" * 50)

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    modelo_path = os.path.join(BASE_DIR, "ml", "modelos", "svm_model.joblib")

    assert os.path.exists(modelo_path), f"Modelo nao encontrado em: {modelo_path}"
    print(f"  [OK] Modelo encontrado: {modelo_path}")

    dados_modelo = joblib.load(modelo_path)
    assert "modelo" in dados_modelo, "Chave 'modelo' ausente no joblib"
    assert "kernel" in dados_modelo, "Chave 'kernel' ausente no joblib"
    assert "features" in dados_modelo, "Chave 'features' ausente no joblib"
    assert "acuracia_teste" in dados_modelo, "Chave 'acuracia_teste' ausente no joblib"
    print(
        f"  [OK] Modelo carregado: kernel={dados_modelo['kernel']}, C={dados_modelo['C']}"
    )
    print(f"  [OK] Features: {dados_modelo['features']}")
    print(f"  [OK] Acuracia treino: {dados_modelo['acuracia_treino']:.1%}")
    print(f"  [OK] Acuracia teste: {dados_modelo['acuracia_teste']:.1%}")

    features = dados_modelo["features"]
    dados_teste = {f: 0.5 for f in features}
    motor = SvmMotor(modelo_path)
    resultado = motor.executar(dados_teste)

    assert "erro" not in resultado, f"Predicao falhou: {resultado.get('erro')}"
    assert resultado["classe_predita"] in [0, 1], (
        f"Classe invalida: {resultado['classe_predita']}"
    )
    assert 0.0 <= resultado["probabilidade_apendicite"] <= 1.0, (
        "Probabilidade fora de [0,1]"
    )
    assert resultado["disclaimer"], "Disclaimer ausente"
    assert resultado["referencia_algoritmo"], "Referencia do algoritmo ausente"
    assert resultado["confianca"] in [
        "Alta",
        "Media",
        "Baixa -- resultado inconclusivo",
    ]

    print(
        f"  [OK] Predicao (dados medios): classe={resultado['classe_predita']}, "
        f"prob={resultado['probabilidade_percentual']}, confianca={resultado['confianca']}"
    )
    print(f"  [OK] Disclaimer presente")
    print(f"  [OK] Referencia DOI presente")

    print()
    print("  TODOS OS TESTES PASSARAM!")
    print("=" * 50)


if __name__ == "__main__":
    testar_svm()
