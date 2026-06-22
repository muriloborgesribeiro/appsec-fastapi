import os
import pytest
import joblib
from ml.knn_engine import KnnMotor
from app.config import KNN_MODEL_PATH


@pytest.fixture
def modelo_path():
    return KNN_MODEL_PATH


@pytest.fixture
def dados_modelo(modelo_path):
    assert os.path.exists(modelo_path), f"Modelo nao encontrado: {modelo_path}"
    return joblib.load(modelo_path)


@pytest.fixture
def motor(modelo_path):
    return KnnMotor(modelo_path)


@pytest.fixture
def features(dados_modelo):
    return dados_modelo["features"]


class TestModeloCarregamento:
    def test_modelo_existe(self, modelo_path):
        assert os.path.exists(modelo_path)

    def test_chaves_obrigatorias(self, dados_modelo):
        assert "modelo" in dados_modelo
        assert "k" in dados_modelo
        assert "features" in dados_modelo
        assert "acuracia_teste" in dados_modelo

    def test_acuracia_minima(self, dados_modelo):
        assert dados_modelo["acuracia_teste"] >= 0.0


class TestKnnMotor:
    def test_predicao_dados_medios(self, motor, features):
        dados = {f: 0.5 for f in features}
        resultado = motor.executar(dados)
        assert "erro" not in resultado
        assert resultado["classe_predita"] in [0, 1]
        assert 0.0 <= resultado["probabilidade_apendicite"] <= 1.0
        assert resultado["disclaimer"]
        assert resultado["referencia_algoritmo"]
        assert resultado["confianca"] in [
            "Alta", "Media", "Baixa -- resultado inconclusivo"
        ]

    def test_predicao_zeros(self, motor, features):
        dados = {f: 0.0 for f in features}
        resultado = motor.executar(dados)
        assert "erro" not in resultado

    def test_predicao_uns(self, motor, features):
        dados = {f: 1.0 for f in features}
        resultado = motor.executar(dados)
        assert "erro" not in resultado

    def test_feature_obrigatoria_ausente(self, motor, features, dados_modelo):
        from ml.preprocessamento import FEATURES_OPCIONAIS_RUNTIME
        features_opcionais = dados_modelo.get("features_opcionais", [])
        features_obrig = [f for f in features if f not in FEATURES_OPCIONAIS_RUNTIME]
        if not features_obrig:
            pytest.skip("sem features obrigatorias para testar")
        dados_inc = {f: 0.5 for f in features}
        del dados_inc[features_obrig[0]]
        resultado = motor.executar(dados_inc)
        assert "erro" in resultado

    def test_modelo_inexistente(self, features):
        motor_sem = KnnMotor("caminho/inexistente.joblib")
        dados = {f: 0.5 for f in features}
        resultado = motor_sem.executar(dados)
        assert "erro" in resultado

    def test_features_opcionais_imputadas(self, motor, features, dados_modelo):
        from ml.preprocessamento import FEATURES_OPCIONAIS_RUNTIME
        features_opc = [f for f in features if f in FEATURES_OPCIONAIS_RUNTIME]
        if not features_opc:
            pytest.skip("modelo sem features opcionais")
        dados_sem_opc = {
            f: 0.5 for f in features if f not in FEATURES_OPCIONAIS_RUNTIME
        }
        resultado = motor.executar(dados_sem_opc)
        assert "erro" not in resultado
        assert len(resultado["features_imputadas"]) == len(features_opc)
