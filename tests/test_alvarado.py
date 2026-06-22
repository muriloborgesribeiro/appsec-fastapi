import pytest
from ml.alvarado import calcular_alvarado, AlvaradoMotor, CHAVES_ALVARADO


class TestCalcularAlvarado:
    def test_todos_negativos_score_zero(self):
        caso = {
            "dor_migratoria": False,
            "anorexia": False,
            "nauseas_vomitos": False,
            "dor_fid": False,
            "descompressao_dolorosa": False,
            "temperatura": 36.5,
            "leucocitos": 8000,
            "neutrofilia": False,
        }
        r = calcular_alvarado(caso)
        assert r["score"] == 0
        assert r["classificacao"] == "baixo"

    def test_todos_positivos_score_dez(self):
        caso = {
            "dor_migratoria": True,
            "anorexia": True,
            "nauseas_vomitos": True,
            "dor_fid": True,
            "descompressao_dolorosa": True,
            "temperatura": 38.5,
            "leucocitos": 15000,
            "neutrofilia": True,
        }
        r = calcular_alvarado(caso)
        assert r["score"] == 10
        assert r["classificacao"] == "alto"

    def test_score_cinco_moderado(self):
        caso = {
            "dor_migratoria": True,
            "anorexia": False,
            "nauseas_vomitos": False,
            "dor_fid": True,
            "descompressao_dolorosa": False,
            "temperatura": 36.8,
            "leucocitos": 12000,
            "neutrofilia": False,
        }
        r = calcular_alvarado(caso)
        assert r["score"] == 5
        assert r["classificacao"] == "moderado"

    def test_temperatura_37_3_nao_pontua(self):
        caso = {
            "dor_migratoria": False,
            "anorexia": False,
            "nauseas_vomitos": False,
            "dor_fid": False,
            "descompressao_dolorosa": False,
            "temperatura": 37.3,
            "leucocitos": 5000,
            "neutrofilia": False,
        }
        r = calcular_alvarado(caso)
        assert r["score"] == 0

    def test_leucocitos_10000_nao_pontua(self):
        caso = {
            "dor_migratoria": False,
            "anorexia": False,
            "nauseas_vomitos": False,
            "dor_fid": False,
            "descompressao_dolorosa": False,
            "temperatura": 36.5,
            "leucocitos": 10000,
            "neutrofilia": False,
        }
        r = calcular_alvarado(caso)
        assert r["score"] == 0

    def test_score_sete_alto(self):
        caso = {
            "dor_migratoria": True,
            "anorexia": True,
            "nauseas_vomitos": True,
            "dor_fid": True,
            "descompressao_dolorosa": True,
            "temperatura": 36.5,
            "leucocitos": 5000,
            "neutrofilia": True,
        }
        r = calcular_alvarado(caso)
        assert r["score"] == 7
        assert r["classificacao"] == "alto"

    def test_score_quatro_baixo(self):
        caso = {
            "dor_migratoria": True,
            "anorexia": True,
            "nauseas_vomitos": True,
            "dor_fid": False,
            "descompressao_dolorosa": False,
            "temperatura": 37.5,
            "leucocitos": 5000,
            "neutrofilia": False,
        }
        r = calcular_alvarado(caso)
        assert r["score"] == 4
        assert r["classificacao"] == "baixo"

    def test_detalhamento_oito_criterios_com_doi(self):
        caso = {
            "dor_migratoria": True,
            "anorexia": True,
            "nauseas_vomitos": True,
            "dor_fid": True,
            "descompressao_dolorosa": True,
            "temperatura": 38.5,
            "leucocitos": 15000,
            "neutrofilia": True,
        }
        r = calcular_alvarado(caso)
        assert len(r["detalhamento"]) == 8
        for item in r["detalhamento"]:
            assert "referencia" in item
            assert "DOI" in item["referencia"]

    def test_disclaimer_em_todas_classificacoes(self):
        caso_baixo = {
            "dor_migratoria": False,
            "anorexia": False,
            "nauseas_vomitos": False,
            "dor_fid": False,
            "descompressao_dolorosa": False,
            "temperatura": 36.5,
            "leucocitos": 8000,
            "neutrofilia": False,
        }
        caso_moderado = {
            "dor_migratoria": True,
            "anorexia": False,
            "nauseas_vomitos": False,
            "dor_fid": True,
            "descompressao_dolorosa": False,
            "temperatura": 36.8,
            "leucocitos": 12000,
            "neutrofilia": False,
        }
        caso_alto = {
            "dor_migratoria": True,
            "anorexia": True,
            "nauseas_vomitos": True,
            "dor_fid": True,
            "descompressao_dolorosa": True,
            "temperatura": 38.5,
            "leucocitos": 15000,
            "neutrofilia": True,
        }
        assert calcular_alvarado(caso_baixo)["disclaimer"]
        assert calcular_alvarado(caso_moderado)["disclaimer"]
        assert calcular_alvarado(caso_alto)["disclaimer"]


class TestAlvaradoMotor:
    def test_executar_delega_para_calcular_alvarado(self):
        motor = AlvaradoMotor()
        dados = {k: False for k in CHAVES_ALVARADO}
        dados["temperatura"] = 36.5
        dados["leucocitos"] = 8000
        r = motor.executar(dados)
        assert r["score"] == 0
        assert r["classificacao"] == "baixo"
