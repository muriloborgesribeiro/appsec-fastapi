import os
import pytest
import joblib
from ml.svm_engine import SvmMotor
from app.config import SVM_MODEL_PATH


@pytest.fixture
def modelo_path():
    return SVM_MODEL_PATH


@pytest.fixture
def dados_modelo(modelo_path):
    assert os.path.exists(modelo_path), f"Modelo nao encontrado: {modelo_path}"
    return joblib.load(modelo_path)


@pytest.fixture
def motor(modelo_path):
    return SvmMotor(modelo_path)


@pytest.fixture
def features(dados_modelo):
    return dados_modelo["features"]


class TestModeloCarregamento:
    def test_modelo_existe(self, modelo_path):
        assert os.path.exists(modelo_path)

    def test_chaves_obrigatorias(self, dados_modelo):
        assert "modelo" in dados_modelo
        assert "kernel" in dados_modelo
        assert "features" in dados_modelo
        assert "acuracia_teste" in dados_modelo


class TestSvmMotor:
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
