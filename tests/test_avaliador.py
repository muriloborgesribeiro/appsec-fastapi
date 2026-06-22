import os
import numpy as np
from ml.avaliador import (
    avaliar_modelo,
    comparar_alvarado_knn,
    gerar_orange_ows,
)


class TestAvaliarModelo:
    def test_cenario_perfeito(self):
        y_real = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        y_pred = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        r = avaliar_modelo(y_real, y_pred)
        assert r["acuracia"] == 1.0
        assert r["sensibilidade"] == 1.0
        assert r["especificidade"] == 1.0
        assert r["vpp"] == 1.0
        assert r["vpn"] == 1.0
        assert r["vp"] == 5
        assert r["vn"] == 5
        assert r["fp"] == 0
        assert r["fn"] == 0

    def test_cenario_pessimo(self):
        y_real = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        y_pred = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
        r = avaliar_modelo(y_real, y_pred)
        assert r["acuracia"] == 0.0
        assert r["sensibilidade"] == 0.0
        assert r["especificidade"] == 0.0

    def test_cenario_misto(self):
        y_real = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        y_pred = np.array([1, 1, 0, 0, 0, 0, 1, 0])
        r = avaliar_modelo(y_real, y_pred)
        assert r["vp"] == 2
        assert r["fn"] == 2
        assert r["fp"] == 1
        assert r["vn"] == 3
        assert abs(r["sensibilidade"] - 0.5) < 0.01
        assert abs(r["especificidade"] - 0.75) < 0.01

    def test_metricas_detalhadas(self):
        y_real = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        y_pred = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        r = avaliar_modelo(y_real, y_pred)
        assert "metricas_detalhadas" in r
        assert len(r["metricas_detalhadas"]) == 5
        for m in r["metricas_detalhadas"]:
            assert "formula" in m
            assert "referencia" in m
            assert "DOI" in m["referencia"]
            assert "valor_percentual" in m

    def test_divisao_por_zero_especificidade(self):
        y_real = np.array([1, 1, 1, 1])
        y_pred = np.array([1, 1, 1, 0])
        r = avaliar_modelo(y_real, y_pred)
        assert r["especificidade"] == 0.0

    def test_gerar_imagem(self, tmp_path):
        y_real = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        y_pred = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        r = avaliar_modelo(y_real, y_pred, output_dir=str(tmp_path))
        assert r["imagem_matrix"]
        assert os.path.exists(r["imagem_matrix"])


class TestCompararAlvaradoKnn:
    def test_comparacao_retorna_tabela(self):
        y_real = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        y_pred_knn = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        y_pred_alv = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
        comp = comparar_alvarado_knn(y_real, y_pred_knn, y_pred_alv)
        assert "tabela" in comp
        assert len(comp["tabela"]) == 5
        for linha in comp["tabela"]:
            assert "melhor" in linha


class TestGerarOrangeOws:
    def test_ows_gerado(self, tmp_path):
        csv_path = "data/regensburg_processed.csv"
        if not os.path.exists(csv_path):
            return
        ows_path = os.path.join(str(tmp_path), "teste.ows")
        gerar_orange_ows(csv_path, ows_path)
        assert os.path.exists(ows_path)
        with open(ows_path, encoding="utf-8") as f:
            conteudo = f.read()
        assert "KNN" in conteudo
        assert "Confusion Matrix" in conteudo
