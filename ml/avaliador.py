# ============================================================
#  ml/avaliador.py
#  APPSPEC -- Modulo de Avaliacao do Modelo
#  Tecnologia: sklearn.metrics (ensinada na disciplina)
#  Contrato: SPEC-01 6.2 / SPEC-05
#
#  Referencia: Fawcett T. (2006). An introduction to ROC
#  analysis. Pattern Recognit Lett, 27(8), 861-874.
#  DOI: 10.1016/j.patrec.2005.10.010
# ============================================================

import numpy as np
import os

import matplotlib

matplotlib.use("Agg")  # Backend sem GUI para gerar PNGs
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    roc_curve,
    auc,
    precision_recall_curve,
    average_precision_score,
)


# -----------------------------------------------------------
#  DICIONARIO DE METRICAS DA DISCIPLINA (SPEC-05 6.1)
#  Cada metrica tem formula, descricao, relevancia clinica e DOI
#  Para exibicao na UI com formulas visiveis (SPEC-00 Convencao 8)
# -----------------------------------------------------------

METRICAS = {
    "acuracia": {
        "nome": "Acuracia",
        "formula": "Acuracia = (VP + VN) / Total",
        "formula_curta": "(VP+VN)/Total",
        "descricao": "Proporcao de classificacoes corretas no total",
        "relevancia_clinica": "Indica a taxa geral de acerto do modelo",
        "referencia": "Fawcett, 2006. DOI:10.1016/j.patrec.2005.10.010",
    },
    "sensibilidade": {
        "nome": "Sensibilidade",
        "formula": "Sensibilidade = VP / (VP + FN)",
        "formula_curta": "VP/(VP+FN)",
        "descricao": "Taxa de Verdadeiros Positivos (TPR) -- capacidade de detectar doenca",
        "relevancia_clinica": "Alta sensibilidade = poucos casos de apendicite perdidos",
        "referencia": "Fawcett, 2006. DOI:10.1016/j.patrec.2005.10.010",
    },
    "especificidade": {
        "nome": "Especificidade",
        "formula": "Especificidade = VN / (VN + FP)",
        "formula_curta": "VN/(VN+FP)",
        "descricao": "Taxa de Verdadeiros Negativos (TNR) -- capacidade de excluir doenca",
        "relevancia_clinica": "Alta especificidade = poucos casos normais operados desnecessariamente",
        "referencia": "Fawcett, 2006. DOI:10.1016/j.patrec.2005.10.010",
    },
    "vpp": {
        "nome": "Valor Preditivo Positivo (VPP)",
        "formula": "VPP = VP / (VP + FP)",
        "formula_curta": "VP/(VP+FP)",
        "descricao": "Probabilidade de ter doenca dado teste positivo",
        "relevancia_clinica": "Util para o clinico: se o modelo diz positivo, qual a chance de ser verdade?",
        "referencia": "Fawcett, 2006. DOI:10.1016/j.patrec.2005.10.010",
    },
    "vpn": {
        "nome": "Valor Preditivo Negativo (VPN)",
        "formula": "VPN = VN / (VN + FN)",
        "formula_curta": "VN/(VN+FN)",
        "descricao": "Probabilidade de nao ter doenca dado teste negativo",
        "relevancia_clinica": "Util para o clinico: se o modelo diz negativo, qual a chance de ser verdade?",
        "referencia": "Fawcett, 2006. DOI:10.1016/j.patrec.2005.10.010",
    },
}


def avaliar_modelo(
    y_real: np.ndarray,
    y_pred: np.ndarray,
    output_dir: str | None = None,
    nome_modelo: str = "KNN",
    nome_arquivo: str = "confusion_matrix.png",
) -> dict:
    """
    Avalia o modelo com metricas da disciplina e gera a matriz de confusao.

    Interface publica conforme SPEC-01 6.2 / SPEC-05:
      INPUT:  y_real (array), y_pred (array), output_dir (str, opcional)
      OUTPUT: {
          "vp": int, "fp": int, "fn": int, "vn": int,
          "acuracia": float,
          "sensibilidade": float,
          "especificidade": float,
          "vpp": float,
          "vpn": float,
          "imagem_matrix": str,
          "metricas_detalhadas": list  -- para exibicao na UI
      }

    Tecnologia: sklearn.metrics.confusion_matrix (ensinada na disciplina)
    Referencia: Fawcett, T. (2006). DOI:10.1016/j.patrec.2005.10.010
    """
    y_real = np.asarray(y_real)
    y_pred = np.asarray(y_pred)

    # Matriz de confusao: [[VN, FP], [FN, VP]]
    cm = confusion_matrix(y_real, y_pred)
    vn, fp, fn, vp = cm.ravel()

    # Metricas da disciplina -- com formulas explicitas (SPEC-00 Convencao 8)
    # Sensibilidade (Recall) = VP / (VP + FN)
    # DOI: 10.1016/j.patrec.2005.10.010
    sensibilidade = float(vp / (vp + fn)) if (vp + fn) > 0 else 0.0

    # Especificidade = VN / (VN + FP)
    # DOI: 10.1016/j.patrec.2005.10.010
    especificidade = float(vn / (vn + fp)) if (vn + fp) > 0 else 0.0

    # Valor Preditivo Positivo (Precisao) = VP / (VP + FP)
    # DOI: 10.1016/j.patrec.2005.10.010
    vpp = float(vp / (vp + fp)) if (vp + fp) > 0 else 0.0

    # Valor Preditivo Negativo = VN / (VN + FN)
    # DOI: 10.1016/j.patrec.2005.10.010
    vpn = float(vn / (vn + fn)) if (vn + fn) > 0 else 0.0

    # Acuracia = (VP + VN) / Total
    # DOI: 10.1016/j.patrec.2005.10.010
    acuracia = float(accuracy_score(y_real, y_pred))

    total = int(vp + fp + fn + vn)

    # Montar lista detalhada de metricas para a UI (SPEC-05 G-05)
    valores = {
        "acuracia": acuracia,
        "sensibilidade": sensibilidade,
        "especificidade": especificidade,
        "vpp": vpp,
        "vpn": vpn,
    }
    metricas_detalhadas = []
    for chave, info in METRICAS.items():
        metricas_detalhadas.append(
            {
                "id": chave,
                "nome": info["nome"],
                "formula": info["formula"],
                "formula_curta": info["formula_curta"],
                "descricao": info["descricao"],
                "relevancia_clinica": info["relevancia_clinica"],
                "referencia": info["referencia"],
                "valor": valores[chave],
                "valor_percentual": f"{valores[chave]:.1%}",
            }
        )

    # Gerar imagem da matriz de confusao
    imagem_path = ""
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        imagem_path = os.path.join(output_dir, nome_arquivo)
        try:
            _gerar_imagem_matriz(
                cm,
                imagem_path,
                acuracia,
                sensibilidade,
                especificidade,
                nome_modelo=nome_modelo,
            )
        except Exception as e:
            print(f"       [AVISO] Erro ao gerar imagem da matriz: {e}")
            imagem_path = ""

    return {
        "vp": int(vp),
        "fp": int(fp),
        "fn": int(fn),
        "vn": int(vn),
        "total": total,
        "acuracia": acuracia,
        "sensibilidade": sensibilidade,
        "especificidade": especificidade,
        "vpp": vpp,
        "vpn": vpn,
        "imagem_matrix": imagem_path,
        "metricas_detalhadas": metricas_detalhadas,
    }


def comparar_alvarado_knn(y_real, y_pred_knn, y_pred_alvarado) -> dict:
    """
    Compara as metricas do Alvarado vs KNN no mesmo conjunto de teste (SPEC-05 6.4).

    INPUT:
      y_real: array com diagnostico real (0/1)
      y_pred_knn: array com predicoes do KNN (0/1)
      y_pred_alvarado: array com predicoes do Alvarado (0/1)

    OUTPUT: {
      "alvarado": { metricas... },
      "knn": { metricas... },
      "tabela": [ {metrica, alvarado, knn, formula} ]
    }
    """
    metricas_knn = avaliar_modelo(y_real, y_pred_knn)
    metricas_alvarado = avaliar_modelo(y_real, y_pred_alvarado)

    # Montar tabela comparativa para a UI
    tabela = []
    campos = [
        ("Acuracia", "acuracia", "(VP+VN)/Total"),
        ("Sensibilidade", "sensibilidade", "VP/(VP+FN)"),
        ("Especificidade", "especificidade", "VN/(VN+FP)"),
        ("VPP", "vpp", "VP/(VP+FP)"),
        ("VPN", "vpn", "VN/(VN+FN)"),
    ]

    for nome, chave, formula in campos:
        val_alv = metricas_alvarado[chave]
        val_knn = metricas_knn[chave]
        melhor = (
            "knn"
            if val_knn > val_alv
            else ("alvarado" if val_alv > val_knn else "empate")
        )
        tabela.append(
            {
                "metrica": nome,
                "formula": formula,
                "alvarado_valor": val_alv,
                "alvarado_percentual": f"{val_alv:.1%}",
                "knn_valor": val_knn,
                "knn_percentual": f"{val_knn:.1%}",
                "melhor": melhor,
            }
        )

    return {
        "alvarado": {
            "metricas": metricas_alvarado,
            "metodo": "Regra deterministica (Alvarado, 1986)",
            "referencia": "DOI:10.1016/S0196-0644(86)80468-2",
        },
        "knn": {
            "metricas": metricas_knn,
            "metodo": "KNN -- scikit-learn",
            "referencia": "DOI:10.1109/TIT.1967.1053964",
        },
        "tabela": tabela,
    }


def _gerar_imagem_matriz(
    cm,
    output_path: str,
    acuracia: float,
    sensibilidade: float,
    especificidade: float,
    nome_modelo: str = "KNN",
) -> None:
    """
    Gera imagem PNG da matriz de confusao com metricas visiveis.
    Tecnologia: matplotlib + seaborn (ensinadas na disciplina)
    SPEC-05 RNF-01: PNG, ~800x600px, legivel em tela e projetor
    """
    fig, ax = plt.subplots(figsize=(10, 7))

    # Cores: verde para acertos, vermelho para erros (SPEC-05 RNF-02)
    # Usando paleta customizada
    cores_custom = sns.color_palette(["#d4edda", "#2e7d32", "#f8d7da", "#c62828"])

    # Colormap diferente por modelo para facilitar distincao visual
    cmap_modelo = "Purples" if nome_modelo == "SVM" else "Blues"

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap=cmap_modelo,
        xticklabels=["Sem Apendicite (0)", "Apendicite (1)"],
        yticklabels=["Sem Apendicite (0)", "Apendicite (1)"],
        ax=ax,
        annot_kws={"size": 20, "weight": "bold"},
        linewidths=3,
        linecolor="white",
        cbar_kws={"label": "Quantidade"},
    )

    ax.set_xlabel("Predicao do Modelo", fontsize=13, fontweight="bold", labelpad=10)
    ax.set_ylabel("Diagnostico Real", fontsize=13, fontweight="bold", labelpad=10)
    ax.set_title(
        f"Matriz de Confusao -- {nome_modelo} (scikit-learn)\n"
        "Disciplina: Construção de APIs para Inteligência Artificial, -- UFG",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )

    # Adicionar metricas abaixo do grafico (SPEC-00 Convencao 8: formulas visiveis)
    vn, fp, fn, vp = cm.ravel()
    metricas_texto = (
        f"VP={vp}  FP={fp}  FN={fn}  VN={vn}\n"
        f"Acuracia = (VP+VN)/Total = {acuracia:.1%}  |  "
        f"Sensibilidade = VP/(VP+FN) = {sensibilidade:.1%}  |  "
        f"Especificidade = VN/(VN+FP) = {especificidade:.1%}"
    )
    fig.text(
        0.5,
        0.01,
        metricas_texto,
        ha="center",
        fontsize=9,
        style="italic",
        color="#444444",
        family="monospace",
    )

    # Legenda dos quadrantes
    legenda = (
        "VN = Verdadeiro Negativo  |  FP = Falso Positivo  |  "
        "FN = Falso Negativo  |  VP = Verdadeiro Positivo"
    )
    fig.text(0.5, 0.96, legenda, ha="center", fontsize=8, color="#666666")

    plt.tight_layout(rect=(0, 0.06, 1, 0.95))
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def gerar_orange_ows(dataset_path: str, output_path: str) -> None:
    """
    Gera o arquivo .ows do Orange3 com o pipeline KNN completo.

    Interface publica conforme SPEC-01 6.2:
      INPUT:  dataset_path (str), output_path (str)
      OUTPUT: None (arquivo .ows gerado no output_path)

    Tecnologia: Orange3 (ensinada na disciplina -- validacao visual no-code)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # O arquivo .ows e um XML do Orange3 que define um workflow visual.
    # Pipeline: File -> Select Columns -> Data Sampler -> KNN -> Test and Score -> Confusion Matrix
    ows_content = f"""<?xml version='1.0' encoding='utf-8'?>
<scheme version="2.0"
        title="APPSPEC - Validacao KNN (Apendicite)"
        description="Workflow Orange3 gerado automaticamente pelo setup.py do APPSPEC.
Disciplina: Construção de APIs para Inteligência Artificial, - UFG - Prof. Rogério Rodrigues Carvalho.
Pipeline: Dataset Regensburg -> Pre-processamento -> KNN -> Matriz de Confusao.
Tecnologia: Orange3 (validacao visual no-code, ensinada na disciplina).">
    <nodes>
        <node id="0" name="CSV File Import" qualified_name="Orange.widgets.data.owcsvimport.OWCSVFileImport"
              position="(150, 300)" title="Dataset Regensburg" />
        <node id="1" name="Select Columns" qualified_name="Orange.widgets.data.owselectcolumns.OWSelectAttributes"
              position="(350, 300)" title="Selecionar Features" />
        <node id="2" name="Data Sampler" qualified_name="Orange.widgets.data.owdatasampler.OWDataSampler"
              position="(550, 300)" title="Split 70/30" />
        <node id="3" name="kNN" qualified_name="Orange.widgets.model.owknn.OWKNNLearner"
              position="(550, 150)" title="KNN Learner" />
        <node id="4" name="Test and Score" qualified_name="Orange.widgets.evaluate.owtestandscore.OWTestAndScore"
              position="(750, 300)" title="Avaliacao" />
        <node id="5" name="Confusion Matrix" qualified_name="Orange.widgets.evaluate.owconfusionmatrix.OWConfusionMatrix"
              position="(950, 300)" title="Matriz de Confusao" />
    </nodes>
    <links>
        <link id="0" source_node_id="0" sink_node_id="1" source_channel="Data" sink_channel="Data" />
        <link id="1" source_node_id="1" sink_node_id="2" source_channel="Data" sink_channel="Data" />
        <link id="2" source_node_id="2" sink_node_id="4" source_channel="Data Sample" sink_channel="Data" />
        <link id="3" source_node_id="3" sink_node_id="4" source_channel="Learner" sink_channel="Learner" />
        <link id="4" source_node_id="4" sink_node_id="5" source_channel="Evaluation Results" sink_channel="Evaluation Results" />
    </links>
    <annotations>
        <text id="0" rect="(50, 50, 500, 100)">APPSPEC - Workflow de Validacao Visual
Tecnologia: Orange3 (disciplina de Construção de APIs para Inteligência Artificial,)
Dataset: {os.path.basename(dataset_path)}
Algoritmo: KNN (K-Nearest Neighbors) - Cover and Hart, 1967</text>
    </annotations>
</scheme>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ows_content)


# -----------------------------------------------------------
#  CURVA ROC (Aula 5 -- Slide 21)
#  Referencia: Fawcett T. (2006). DOI:10.1016/j.patrec.2005.10.010
# -----------------------------------------------------------


def gerar_curva_roc(y_real, y_prob, output_path: str, nome_modelo: str = "KNN") -> dict:
    """
    Gera Curva ROC com AUC e ponto otimo de Youden.

    Ensinada na Aula 5 (slide 21, Prof. Rogério Rodrigues Carvalho):
      - Eixo X: Taxa de Falso Positivo (FPR = 1 - Especificidade)
      - Eixo Y: Taxa de Verdadeiro Positivo (TPR = Sensibilidade)
      - AUC: Area sob a curva (quanto maior, melhor)
      - Ponto otimo: Youden's J = max(TPR - FPR)

    INPUT:  y_real (array 0/1), y_prob (array float -- probabilidade da classe 1)
    OUTPUT: {
        "auc_roc": float,
        "limiar_otimo": float,
        "sensibilidade_otima": float,
        "especificidade_otima": float,
        "imagem": str
    }

    Referencia: Fawcett, T. (2006). DOI:10.1016/j.patrec.2005.10.010
    """
    y_real = np.asarray(y_real)
    y_prob = np.asarray(y_prob)

    fpr, tpr, thresholds = roc_curve(y_real, y_prob)
    roc_auc = auc(fpr, tpr)

    # Ponto otimo de Youden: maximiza (Sensibilidade - FPR)
    # Referencia: Youden, W.J. (1950). Cancer, 3(1), 32-35.
    youden_j = tpr - fpr
    idx_otimo = youden_j.argmax()
    limiar_otimo = float(thresholds[idx_otimo])

    # Plotar curva
    fig, ax = plt.subplots(figsize=(8, 6))

    cor_modelo = (
        "#1565c0"
        if nome_modelo == "KNN"
        else ("#6a1b9a" if nome_modelo == "SVM" else "#2e7d32")
    )

    ax.plot(
        fpr,
        tpr,
        color=cor_modelo,
        linewidth=2.5,
        label=f"{nome_modelo} (AUC = {roc_auc:.3f})",
    )
    ax.plot(
        [0, 1], [0, 1], "k--", alpha=0.4, linewidth=1, label="Aleatorio (AUC = 0.500)"
    )
    ax.plot(
        fpr[idx_otimo],
        tpr[idx_otimo],
        "ro",
        markersize=10,
        zorder=5,
        label=f"Limiar otimo = {limiar_otimo:.2f} (Youden's J)",
    )

    ax.set_xlabel(
        "Taxa de Falso Positivo (FPR = 1 - Especificidade)",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_ylabel(
        "Taxa de Verdadeiro Positivo (TPR = Sensibilidade)",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_title(
        f"Curva ROC -- {nome_modelo}\nDisciplina: Construção de APIs para Inteligência Artificial, -- UFG",
        fontsize=12,
        fontweight="bold",
    )
    ax.legend(loc="lower right", fontsize=10)
    ax.set_xlim((-0.02, 1.02))
    ax.set_ylim((-0.02, 1.02))
    ax.grid(True, alpha=0.3)

    # Anotacao do ponto otimo
    ax.annotate(
        f"Sens={tpr[idx_otimo]:.1%}\nEsp={1 - fpr[idx_otimo]:.1%}",
        xy=(fpr[idx_otimo], tpr[idx_otimo]),
        xytext=(fpr[idx_otimo] + 0.15, tpr[idx_otimo] - 0.15),
        fontsize=9,
        color="red",
        arrowprops=dict(arrowstyle="->", color="red", lw=1.5),
    )

    fig.text(
        0.5,
        0.01,
        f"Referencia: Fawcett T. (2006). DOI:10.1016/j.patrec.2005.10.010",
        ha="center",
        fontsize=8,
        color="#888888",
        style="italic",
    )

    plt.tight_layout(rect=(0, 0.04, 1, 1))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    return {
        "auc_roc": float(roc_auc),
        "limiar_otimo": limiar_otimo,
        "sensibilidade_otima": float(tpr[idx_otimo]),
        "especificidade_otima": float(1 - fpr[idx_otimo]),
        "imagem": output_path,
    }


def gerar_curva_pr(y_real, y_prob, output_path: str, nome_modelo: str = "KNN") -> dict:
    """
    Gera Curva Precision-Recall com Average Precision.

    Ensinada na Aula 5 (slides 22-24, Prof. Rogério Rodrigues Carvalho):
      - Eixo X: Recall (Sensibilidade) = VP / (VP + FN)
      - Eixo Y: Precision (VPP) = VP / (VP + FP)
      - AP: Average Precision (area sob a curva PR)

    Mais informativa que ROC quando as classes sao desbalanceadas
    (Regensburg: 59% apendicite vs 41% sem apendicite).

    INPUT:  y_real (array 0/1), y_prob (array float -- probabilidade da classe 1)
    OUTPUT: {
        "average_precision": float,
        "imagem": str
    }

    Referencia: Fawcett, T. (2006). DOI:10.1016/j.patrec.2005.10.010
    """
    y_real = np.asarray(y_real)
    y_prob = np.asarray(y_prob)

    precision, recall, _ = precision_recall_curve(y_real, y_prob)
    ap = average_precision_score(y_real, y_prob)

    # Plotar curva
    fig, ax = plt.subplots(figsize=(8, 6))

    cor_modelo = (
        "#1565c0"
        if nome_modelo == "KNN"
        else ("#6a1b9a" if nome_modelo == "SVM" else "#2e7d32")
    )

    ax.plot(
        recall,
        precision,
        color=cor_modelo,
        linewidth=2.5,
        label=f"{nome_modelo} (AP = {ap:.3f})",
    )

    # Linha de baseline (prevalencia da classe positiva)
    prevalencia = np.mean(y_real)
    ax.axhline(
        y=prevalencia,
        color="k",
        linestyle="--",
        alpha=0.4,
        label=f"Baseline (prevalencia = {prevalencia:.1%})",
    )

    ax.set_xlabel(
        "Recall (Sensibilidade = VP / (VP + FN))", fontsize=11, fontweight="bold"
    )
    ax.set_ylabel("Precision (VPP = VP / (VP + FP))", fontsize=11, fontweight="bold")
    ax.set_title(
        f"Curva Precision-Recall -- {nome_modelo}\n"
        "Disciplina: Construção de APIs para Inteligência Artificial, -- UFG",
        fontsize=12,
        fontweight="bold",
    )
    ax.legend(loc="lower left", fontsize=10)
    ax.set_xlim((-0.02, 1.02))
    ax.set_ylim((-0.02, 1.02))
    ax.grid(True, alpha=0.3)

    fig.text(
        0.5,
        0.01,
        f"Referencia: Fawcett T. (2006). DOI:10.1016/j.patrec.2005.10.010",
        ha="center",
        fontsize=8,
        color="#888888",
        style="italic",
    )

    plt.tight_layout(rect=(0, 0.04, 1, 1))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    return {
        "average_precision": float(ap),
        "imagem": output_path,
    }


def gerar_curvas_comparativas(modelos_dados: list, output_dir: str) -> dict:
    """
    Gera curvas ROC e PR comparativas com todos os modelos sobrepostos.

    Permite visualizar em um unico grafico o desempenho relativo de
    KNN, SVM e Alvarado, conforme ensinado na Aula 5.

    INPUT: modelos_dados = [
        {"nome": str, "y_real": array, "y_prob": array, "cor": str},
        ...
    ]
    OUTPUT: {
        "imagem_roc_comparativa": str,
        "imagem_pr_comparativa": str,
        "resultados": { nome: { auc_roc, average_precision, limiar_otimo, ... } }
    }
    """
    os.makedirs(output_dir, exist_ok=True)
    resultados = {}

    # ---- Curva ROC Comparativa ----
    fig_roc, ax_roc = plt.subplots(figsize=(9, 7))
    ax_roc.plot(
        [0, 1], [0, 1], "k--", alpha=0.4, linewidth=1, label="Aleatorio (AUC = 0.500)"
    )

    for m in modelos_dados:
        nome = m["nome"]
        y_real = np.asarray(m["y_real"])
        y_prob = np.asarray(m["y_prob"])
        cor = m.get("cor", "#333333")

        fpr, tpr, thresholds = roc_curve(y_real, y_prob)
        roc_auc = auc(fpr, tpr)

        youden_j = tpr - fpr
        idx_otimo = youden_j.argmax()
        limiar_otimo = float(thresholds[idx_otimo])

        ax_roc.plot(
            fpr, tpr, color=cor, linewidth=2.5, label=f"{nome} (AUC = {roc_auc:.3f})"
        )
        ax_roc.plot(
            fpr[idx_otimo], tpr[idx_otimo], "o", color=cor, markersize=8, zorder=5
        )

        # Precision-Recall
        ap = average_precision_score(y_real, y_prob)

        resultados[nome] = {
            "auc_roc": float(roc_auc),
            "average_precision": float(ap),
            "limiar_otimo": limiar_otimo,
            "sensibilidade_otima": float(tpr[idx_otimo]),
            "especificidade_otima": float(1 - fpr[idx_otimo]),
        }

    ax_roc.set_xlabel("Taxa de Falso Positivo (FPR)", fontsize=12, fontweight="bold")
    ax_roc.set_ylabel(
        "Taxa de Verdadeiro Positivo (TPR)", fontsize=12, fontweight="bold"
    )
    ax_roc.set_title(
        "Curva ROC Comparativa -- Alvarado vs KNN vs SVM\n"
        "Disciplina: Construção de APIs para Inteligência Artificial, -- UFG",
        fontsize=13,
        fontweight="bold",
    )
    ax_roc.legend(loc="lower right", fontsize=10)
    ax_roc.set_xlim((-0.02, 1.02))
    ax_roc.set_ylim((-0.02, 1.02))
    ax_roc.grid(True, alpha=0.3)

    fig_roc.text(
        0.5,
        0.01,
        "Referencia: Fawcett T. (2006). DOI:10.1016/j.patrec.2005.10.010",
        ha="center",
        fontsize=8,
        color="#888888",
        style="italic",
    )

    plt.tight_layout(rect=(0, 0.04, 1, 1))
    roc_path = os.path.join(output_dir, "roc_comparativa.png")
    plt.savefig(roc_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig_roc)

    # ---- Curva PR Comparativa ----
    fig_pr, ax_pr = plt.subplots(figsize=(9, 7))

    # Linha de baseline (prevalencia)
    if modelos_dados:
        prevalencia = np.mean(np.asarray(modelos_dados[0]["y_real"]))
        ax_pr.axhline(
            y=prevalencia,
            color="k",
            linestyle="--",
            alpha=0.4,
            label=f"Baseline (prevalencia = {prevalencia:.1%})",
        )

    for m in modelos_dados:
        nome = m["nome"]
        y_real = np.asarray(m["y_real"])
        y_prob = np.asarray(m["y_prob"])
        cor = m.get("cor", "#333333")

        precision, recall, _ = precision_recall_curve(y_real, y_prob)
        ap = average_precision_score(y_real, y_prob)

        ax_pr.plot(
            recall, precision, color=cor, linewidth=2.5, label=f"{nome} (AP = {ap:.3f})"
        )

    ax_pr.set_xlabel("Recall (Sensibilidade)", fontsize=12, fontweight="bold")
    ax_pr.set_ylabel("Precision (VPP)", fontsize=12, fontweight="bold")
    ax_pr.set_title(
        "Curva Precision-Recall Comparativa -- Alvarado vs KNN vs SVM\n"
        "Disciplina: Construção de APIs para Inteligência Artificial, -- UFG",
        fontsize=13,
        fontweight="bold",
    )
    ax_pr.legend(loc="lower left", fontsize=10)
    ax_pr.set_xlim((-0.02, 1.02))
    ax_pr.set_ylim((-0.02, 1.02))
    ax_pr.grid(True, alpha=0.3)

    fig_pr.text(
        0.5,
        0.01,
        "Referencia: Fawcett T. (2006). DOI:10.1016/j.patrec.2005.10.010",
        ha="center",
        fontsize=8,
        color="#888888",
        style="italic",
    )

    plt.tight_layout(rect=(0, 0.04, 1, 1))
    pr_path = os.path.join(output_dir, "pr_comparativa.png")
    plt.savefig(pr_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig_pr)

    return {
        "imagem_roc_comparativa": roc_path,
        "imagem_pr_comparativa": pr_path,
        "resultados": resultados,
    }


# -----------------------------------------------------------
#  FUNCAO DE TESTE (SPEC-05 13)
# -----------------------------------------------------------


def testar_avaliador():
    """
    Testa o modulo avaliador com cenarios conhecidos.
    Deve ser chamado para validacao antes de prosseguir para SPEC-06.
    """
    print("=" * 50)
    print("  TESTE DO MODULO DE AVALIACAO")
    print("=" * 50)

    # Caso 1: Cenario perfeito (100% acuracia)
    y_real = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    y_pred = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    r = avaliar_modelo(y_real, y_pred)
    assert r["acuracia"] == 1.0, f"Esperado 1.0, obteve {r['acuracia']}"
    assert r["sensibilidade"] == 1.0
    assert r["especificidade"] == 1.0
    assert r["vpp"] == 1.0
    assert r["vpn"] == 1.0
    assert r["vp"] == 5
    assert r["vn"] == 5
    assert r["fp"] == 0
    assert r["fn"] == 0
    print("  [OK] Caso perfeito: todas metricas = 100%")

    # Caso 2: Cenario pessimo (0% acuracia)
    y_pred_inv = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
    r_inv = avaliar_modelo(y_real, y_pred_inv)
    assert r_inv["acuracia"] == 0.0
    assert r_inv["sensibilidade"] == 0.0
    assert r_inv["especificidade"] == 0.0
    print("  [OK] Caso pessimo: acuracia/sensibilidade/especificidade = 0%")

    # Caso 3: Cenario misto conhecido
    y_real_m = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    y_pred_m = np.array([1, 1, 0, 0, 0, 0, 1, 0])
    r_m = avaliar_modelo(y_real_m, y_pred_m)
    assert r_m["vp"] == 2, f"VP esperado 2, obteve {r_m['vp']}"
    assert r_m["fn"] == 2, f"FN esperado 2, obteve {r_m['fn']}"
    assert r_m["fp"] == 1, f"FP esperado 1, obteve {r_m['fp']}"
    assert r_m["vn"] == 3, f"VN esperado 3, obteve {r_m['vn']}"
    # Sensibilidade = 2/(2+2) = 0.5
    assert abs(r_m["sensibilidade"] - 0.5) < 0.01
    # Especificidade = 3/(3+1) = 0.75
    assert abs(r_m["especificidade"] - 0.75) < 0.01
    print(
        f"  [OK] Caso misto: VP={r_m['vp']} FP={r_m['fp']} "
        f"FN={r_m['fn']} VN={r_m['vn']}"
    )
    print(
        f"       Sensibilidade={r_m['sensibilidade']:.1%} "
        f"Especificidade={r_m['especificidade']:.1%}"
    )

    # Caso 4: Verificar metricas_detalhadas
    assert "metricas_detalhadas" in r, "metricas_detalhadas ausente no output"
    assert len(r["metricas_detalhadas"]) == 5, (
        f"Esperado 5 metricas, obteve {len(r['metricas_detalhadas'])}"
    )
    for m in r["metricas_detalhadas"]:
        assert "formula" in m, f"Formula ausente em {m['id']}"
        assert "referencia" in m, f"Referencia ausente em {m['id']}"
        assert "DOI" in m["referencia"], f"DOI ausente em {m['id']}"
        assert "valor_percentual" in m, f"Valor percentual ausente em {m['id']}"
    print("  [OK] 5 metricas detalhadas com formula e DOI")

    # Caso 5: Divisao por zero (todos positivos, VN+FP=0)
    y_real_pos = np.array([1, 1, 1, 1])
    y_pred_pos = np.array([1, 1, 1, 0])
    r_pos = avaliar_modelo(y_real_pos, y_pred_pos)
    # Especificidade nao pode ser calculada (VN+FP=0)
    assert r_pos["especificidade"] == 0.0, "Especificidade deveria ser 0 quando VN+FP=0"
    print("  [OK] Divisao por zero tratada corretamente")

    # Caso 6: Gerar imagem (se output_dir fornecido)
    import tempfile

    tmp_dir = tempfile.mkdtemp()
    r_img = avaliar_modelo(y_real, y_pred, output_dir=tmp_dir)
    assert r_img["imagem_matrix"], "Imagem deveria ter sido gerada"
    assert os.path.exists(r_img["imagem_matrix"]), (
        f"Imagem nao encontrada: {r_img['imagem_matrix']}"
    )
    print(f"  [OK] Imagem da matriz gerada: {r_img['imagem_matrix']}")
    # Limpar
    os.remove(r_img["imagem_matrix"])
    os.rmdir(tmp_dir)

    # Caso 7: Comparacao Alvarado vs KNN
    y_pred_alv = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
    comp = comparar_alvarado_knn(y_real, y_pred, y_pred_alv)
    assert "tabela" in comp, "Tabela comparativa ausente"
    assert len(comp["tabela"]) == 5, "Tabela deveria ter 5 metricas"
    for linha in comp["tabela"]:
        assert "melhor" in linha, f"Campo 'melhor' ausente na linha {linha['metrica']}"
    print("  [OK] Comparacao Alvarado vs KNN: 5 metricas comparadas")

    # Caso 8: Gerar Orange .ows
    import tempfile

    tmp_ows = os.path.join(tempfile.mkdtemp(), "teste.ows")
    gerar_orange_ows("data/regensburg_processed.csv", tmp_ows)
    assert os.path.exists(tmp_ows), "Arquivo .ows nao gerado"
    with open(tmp_ows, "r", encoding="utf-8") as f:
        conteudo = f.read()
    assert "KNN" in conteudo, "KNN nao encontrado no .ows"
    assert "Confusion Matrix" in conteudo, "Confusion Matrix nao encontrada no .ows"
    print("  [OK] Workflow Orange .ows gerado corretamente")
    # Limpar
    os.remove(tmp_ows)
    os.rmdir(os.path.dirname(tmp_ows))

    print()
    print("  TODOS OS TESTES PASSARAM!")
    print("=" * 50)


if __name__ == "__main__":
    testar_avaliador()
