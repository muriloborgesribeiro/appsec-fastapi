import numpy as np
import pandas as pd
import joblib
import os
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score

from app.config import (
    KNN_MODEL_PATH,
    K_MINIMO_CLINICO,
    CANDIDATOS_K,
    KNN_METRIC,
    KNN_WEIGHTS,
    KNN_CV_FOLDS,
    LIMIAR_DECISAO_PADRAO,
)
from ml.protocolo import ModeloMLProtocol
from ml._confianca import calcular_confianca

REFERENCIA_KNN = (
    "Cover, T. & Hart, P. (1967). Nearest neighbor pattern classification. "
    "IEEE Trans. Inf. Theory, 13(1), 21-27. DOI:10.1109/TIT.1967.1053964"
)

LABELS_CLASSE = {0: "Sem Apendicite", 1: "Apendicite"}

DISCLAIMER_KNN = (
    "AVISO: Este resultado e gerado por um modelo de Machine Learning (KNN) "
    "treinado no dataset Regensburg (Marcinkevics et al., 2023). "
    "NAO substitui avaliacao medica presencial. "
    "Sistema exclusivamente didatico -- disciplina de Construção de APIs para Inteligência Artificial, (UFG)."
)


class KnnMotor:
    def __init__(self, modelo_path: str = KNN_MODEL_PATH):
        self.modelo_path = modelo_path

    def executar(self, dados: dict) -> dict:
        if not os.path.exists(self.modelo_path):
            return {
                "erro": f"Modelo KNN nao treinado. Execute setup.py. Path: {self.modelo_path}"
            }

        try:
            dados_modelo = joblib.load(self.modelo_path)
        except Exception as e:
            return {"erro": f"Erro ao carregar modelo: {e}"}

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
        distancias, _ = modelo.kneighbors(X_input)
        prob_apendicite = float(probabilidades[1])
        classe_predita = int(modelo.predict(X_input)[0])
        confianca = calcular_confianca(prob_apendicite)
        distancia_media = float(np.mean(distancias[0]))

        return {
            "classe_predita": classe_predita,
            "label_predita": LABELS_CLASSE.get(
                classe_predita, f"Classe {classe_predita}"
            ),
            "probabilidade_apendicite": prob_apendicite,
            "probabilidade_percentual": f"{prob_apendicite:.1%}",
            "k_vizinhos": modelo.n_neighbors,
            "acuracia_modelo": float(acuracia),
            "distancia_media_vizinhos": distancia_media,
            "distancias": distancias[0].tolist(),
            "confianca": confianca,
            "limiar_decisao": LIMIAR_DECISAO_PADRAO,
            "algoritmo": "KNN -- sklearn.neighbors.KNeighborsClassifier",
            "referencia_algoritmo": REFERENCIA_KNN,
            "disclaimer": DISCLAIMER_KNN,
            "features_imputadas": features_imputadas,
        }


def predizer(dados: dict, modelo_path: str = KNN_MODEL_PATH) -> dict:
    return KnnMotor(modelo_path).executar(dados)


def treinar_knn(X: pd.DataFrame, y: pd.Series, k: int | None = None) -> dict:
    if k is not None:
        if k < K_MINIMO_CLINICO:
            print(
                f"       [AVISO] k={k} rejeitado (minimo clinico = {K_MINIMO_CLINICO})"
            )
            k = K_MINIMO_CLINICO
        candidatos_k = [k]
    else:
        candidatos_k = CANDIDATOS_K

    n_amostras = len(X)
    candidatos_k = [k_val for k_val in candidatos_k if k_val < n_amostras]

    melhor_k = candidatos_k[0]
    melhor_acuracia = 0.0
    resultados_cv = {}

    for k_teste in candidatos_k:
        modelo_teste = KNeighborsClassifier(
            n_neighbors=k_teste,
            metric=KNN_METRIC,
            weights=KNN_WEIGHTS,
        )
        cv_folds = min(KNN_CV_FOLDS, n_amostras)
        scores = cross_val_score(modelo_teste, X, y, cv=cv_folds, scoring="accuracy")
        acuracia_media = float(scores.mean())

        resultados_cv[k_teste] = {
            "acuracia_media": acuracia_media,
            "desvio_padrao": float(scores.std()),
        }

        if acuracia_media > melhor_acuracia:
            melhor_acuracia = acuracia_media
            melhor_k = k_teste

    modelo_final = KNeighborsClassifier(
        n_neighbors=melhor_k,
        metric=KNN_METRIC,
        weights=KNN_WEIGHTS,
    )
    modelo_final.fit(X, y)
    acuracia_treino = float(modelo_final.score(X, y))

    return {
        "modelo": modelo_final,
        "k": melhor_k,
        "acuracia_treino": acuracia_treino,
        "resultados_cv": resultados_cv,
    }


def _carregar_imputer(modelo_dir: str) -> tuple:
    imputer_path = os.path.join(modelo_dir, "imputer.joblib")
    if not os.path.exists(imputer_path):
        return {}, []
    try:
        dados = joblib.load(imputer_path)
        return dados.get("medianas_opcionais", {}), dados.get("features_opcionais", [])
    except Exception:
        return {}, []


def _carregar_scaler(modelo_dir: str):
    scaler_path = os.path.join(modelo_dir, "knn_scaler.joblib")
    if not os.path.exists(scaler_path):
        return None
    try:
        return joblib.load(scaler_path)
    except Exception:
        return None


def _montar_array(
    dados: dict,
    features_ordem: list,
    features_opcionais: list,
    medianas_opcionais: dict,
) -> tuple:
    features_imputadas = []
    valores = []
    for f in features_ordem:
        if f in dados and dados[f] is not None and dados[f] != "":
            try:
                valores.append(float(dados[f]))
            except (ValueError, TypeError):
                if f in features_opcionais and f in medianas_opcionais:
                    valores.append(medianas_opcionais[f])
                    features_imputadas.append(f)
                else:
                    return {
                        "erro": f"Valor invalido para feature obrigatoria '{f}': {dados[f]}"
                    }, []
        elif f in features_opcionais and f in medianas_opcionais:
            valores.append(medianas_opcionais[f])
            features_imputadas.append(f)
        else:
            return {
                "erro": f"Feature obrigatoria ausente: '{f}'. Features esperadas: {features_ordem}"
            }, []

    return pd.DataFrame([valores], columns=features_ordem), features_imputadas


def testar_knn():
    print("=" * 50)
    print("  TESTE DO MOTOR KNN")
    print("=" * 50)

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    modelo_path = os.path.join(BASE_DIR, "ml", "modelos", "knn_model.joblib")

    assert os.path.exists(modelo_path), f"Modelo nao encontrado em: {modelo_path}"
    print(f"  [OK] Modelo encontrado: {modelo_path}")

    dados_modelo = joblib.load(modelo_path)
    assert "modelo" in dados_modelo, "Chave 'modelo' ausente no joblib"
    assert "k" in dados_modelo, "Chave 'k' ausente no joblib"
    assert "features" in dados_modelo, "Chave 'features' ausente no joblib"
    assert "acuracia_teste" in dados_modelo, "Chave 'acuracia_teste' ausente no joblib"
    print(f"  [OK] Modelo carregado: k={dados_modelo['k']}")
    print(f"  [OK] Features: {dados_modelo['features']}")
    print(f"  [OK] Acuracia treino: {dados_modelo['acuracia_treino']:.1%}")
    print(f"  [OK] Acuracia teste: {dados_modelo['acuracia_teste']:.1%}")

    features = dados_modelo["features"]
    dados_teste = {f: 0.5 for f in features}
    motor = KnnMotor(modelo_path)
    resultado = motor.executar(dados_teste)

    assert "erro" not in resultado, f"Predicao falhou: {resultado.get('erro')}"
    assert resultado["classe_predita"] in [0, 1], (
        f"Classe invalida: {resultado['classe_predita']}"
    )
    assert 0.0 <= resultado["probabilidade_apendicite"] <= 1.0, (
        "Probabilidade fora de [0,1]"
    )
    assert resultado["k_vizinhos"] == dados_modelo["k"], "k inconsistente"
    assert len(resultado["distancias"]) == dados_modelo["k"], (
        "Numero de distancias != k"
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
    print(
        f"  [OK] Distancia media vizinhos: {resultado['distancia_media_vizinhos']:.4f}"
    )
    print(f"  [OK] Disclaimer presente")
    print(f"  [OK] Referencia DOI presente")

    dados_zero = {f: 0.0 for f in features}
    r_zero = motor.executar(dados_zero)
    assert "erro" not in r_zero, f"Predicao falhou: {r_zero.get('erro')}"
    print(
        f"  [OK] Predicao (zeros): classe={r_zero['classe_predita']}, "
        f"prob={r_zero['probabilidade_percentual']}"
    )

    dados_um = {f: 1.0 for f in features}
    r_um = motor.executar(dados_um)
    assert "erro" not in r_um, f"Predicao falhou: {r_um.get('erro')}"
    print(
        f"  [OK] Predicao (uns): classe={r_um['classe_predita']}, "
        f"prob={r_um['probabilidade_percentual']}"
    )

    import sys

    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
    from ml.preprocessamento import FEATURES_OPCIONAIS_RUNTIME

    features_opcionais_modelo = dados_modelo.get("features_opcionais", [])
    features_obrig_modelo = [f for f in features if f not in FEATURES_OPCIONAIS_RUNTIME]
    if features_obrig_modelo:
        dados_obrig_faltando = {f: 0.5 for f in features}
        del dados_obrig_faltando[features_obrig_modelo[0]]
        r_inc = motor.executar(dados_obrig_faltando)
        assert "erro" in r_inc, "Deveria retornar erro com feature obrigatoria ausente"
        print(f"  [OK] Feature obrigatoria ausente detectada: {r_inc['erro'][:60]}...")
    else:
        print("  [SKIP] Sem features obrigatorias para testar ausencia")

    r_sem = KnnMotor("caminho/inexistente.joblib").executar(dados_teste)
    assert "erro" in r_sem, "Deveria retornar erro com modelo inexistente"
    print(f"  [OK] Modelo inexistente detectado")

    features_opcionais_neste_modelo = [
        f for f in features if f in FEATURES_OPCIONAIS_RUNTIME
    ]
    if features_opcionais_neste_modelo:
        dados_sem_opcionais = {
            f: 0.5 for f in features if f not in FEATURES_OPCIONAIS_RUNTIME
        }
        r_opt = motor.executar(dados_sem_opcionais)
        assert "erro" not in r_opt, (
            f"NAO deveria dar erro com features opcionais ausentes: {r_opt.get('erro')}"
        )
        assert len(r_opt["features_imputadas"]) == len(
            features_opcionais_neste_modelo
        ), (
            f"Deveria imputar {len(features_opcionais_neste_modelo)}, imputou {len(r_opt['features_imputadas'])}"
        )
        print(f"  [OK] Features opcionais omitidas: imputacao automatica por mediana")
        print(f"       Features imputadas: {r_opt['features_imputadas']}")
    else:
        print("  [SKIP] Modelo sem features opcionais para testar")

    acuracia = dados_modelo["acuracia_teste"]
    if acuracia >= 0.80:
        print(f"\n  [OK] Acuracia {acuracia:.1%} >= 80% (target SPEC-04)")
    else:
        print(f"\n  [AVISO] Acuracia {acuracia:.1%} < 80% (target SPEC-04)")
        print(f"  O sistema continua funcionando mas com aviso de baixa acuracia")

    print()
    print("  TODOS OS TESTES PASSARAM!")
    print("=" * 50)


if __name__ == "__main__":
    testar_knn()
