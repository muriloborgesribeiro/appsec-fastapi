# ================================================================
# PREPROCESSAMENTO — A Esterilização dos Dados
# Tecnologia: pandas + scikit-learn (MinMaxScaler)
# Por que existe: Antes de entregar os dados para a IA, precisamos
# limpá-los e organizá-los. Dados sujos (com erros ou faltantes)
# geram diagnósticos errados.
# Analogia médica: É como lavar e esterilizar os instrumentos
# cirúrgicos antes da operação. Se o instrumento estiver sujo,
# a cirurgia falha.
# ================================================================

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.impute import SimpleImputer
import os
import warnings

from app.config import PREPROC_TEST_SIZE, PREPROC_VAL_FRAC, PREPROC_RANDOM_STATE

# -----------------------------------------------------------
#  COLUNAS DO DATASET REGENSBURG (56 colunas, UCI id=938)
#  Inspecionadas via: pd.read_csv('data/regensburg_raw.csv').columns
# -----------------------------------------------------------

COLUNA_TARGET = "Diagnosis"

# Excluidas por leakage ou por serem targets alternativos
COLUNAS_EXCLUIDAS = {
    "Alvarado_Score",  # Leakage: variavel derivada do target
    "Paedriatic_Appendicitis_Score",  # Leakage: idem
    "Management",  # Target alternativo (decisao pos-diagnostico)
    "Severity",  # Target alternativo (gravidade pos-diagnostico)
    "Diagnosis",  # Target principal (nao e feature)
    "Length_of_Stay",  # Leakage pos-desfecho (tempo de internacao)
    "Segmented_Neutrophils",  # 93% NaN -- ruido excessivo para imputacao
}

# -----------------------------------------------------------
#  COMPOSICAO DAS FEATURES POR CATEGORIA
#  (derivada da inspecao real do dataset)
# -----------------------------------------------------------

# Demograficas (float + Sex como categorica binaria)
FEATURES_DEMOGRAFICAS = [
    "Age",  # float64, 0% NaN
    "BMI",  # float64, 3% NaN
    "Sex",  # object (male/female), 0% NaN
    "Height",  # float64, 3% NaN
    "Weight",  # float64, 0% NaN
]

# Sinais e sintomas clinicos
FEATURES_CLINICAS = [
    "Migratory_Pain",  # object (yes/no), 1% NaN
    "Lower_Right_Abd_Pain",  # object (yes/no), 1% NaN
    "Contralateral_Rebound_Tenderness",  # object (yes/no), 2% NaN
    "Coughing_Pain",  # object (yes/no), 2% NaN
    "Nausea",  # object (yes/no), 1% NaN
    "Loss_of_Appetite",  # object (yes/no), 1% NaN
    "Body_Temperature",  # float64, 1% NaN
    "Dysuria",  # object (yes/no), 4% NaN
    "Stool",  # object (normal/diarrhea/constipation), 2% NaN
    "Peritonitis",  # object (no/local/generalized), 1% NaN
    "Psoas_Sign",  # object (yes/no), 5% NaN
    "Ipsilateral_Rebound_Tenderness",  # object (yes/no), 21% NaN
]

# Achados laboratoriais
FEATURES_LABORATORIAIS = [
    "WBC_Count",  # float64, 1% NaN
    "Neutrophil_Percentage",  # float64, 13% NaN
    "Neutrophilia",  # object (yes/no), 6% NaN
    "RBC_Count",  # float64, 2% NaN
    "Hemoglobin",  # float64, 2% NaN
    "RDW",  # float64, 3% NaN
    "Thrombocyte_Count",  # float64, 2% NaN
    "Ketones_in_Urine",  # object (none/+/++/+++), 26% NaN
    "RBC_in_Urine",  # object (none/+/++/+++), 26% NaN
    "WBC_in_Urine",  # object (none/+/++/+++), 25% NaN
    "CRP",  # float64, 1% NaN
]

# Achados ultrassonograficos
FEATURES_ULTRASSOM = [
    "US_Performed",  # object (yes/no), 1% NaN
    "Appendix_on_US",  # object (yes/no), 1% NaN
    "Appendix_Diameter",  # float64, 36% NaN
    "Free_Fluids",  # object (yes/no), 8% NaN
    "Appendix_Wall_Layers",  # object (intact/raised/partially raised/upset), 72% NaN
    "Target_Sign",  # object (yes/no), 82% NaN
    "Appendicolith",  # object (yes/no/not excluded), 91% NaN
    "Perfusion",  # object (yes/no/increased/not assessed), 92% NaN
    "Perforation",  # object (yes/no/not excluded/suspected), 90% NaN
    "Surrounding_Tissue_Reaction",  # object (yes/no), 68% NaN
    "Appendicular_Abscess",  # object (yes/no/not excluded), 89% NaN
    "Pathological_Lymph_Nodes",  # object (yes/no), 74% NaN
    "Bowel_Wall_Thickening",  # object (yes/no), 87% NaN
    "Conglomerate_of_Bowel_Loops",  # object (yes/no), 95% NaN
    "Ileus",  # object (yes/no), 92% NaN
    "Coprostasis",  # object (yes/no), 91% NaN
    "Meteorism",  # object (yes/no), 82% NaN
    "Enteritis",  # object (yes/no), 92% NaN
]

# Colunas com NaN excessivo descartadas por Config F_core (>70%)
COLUNAS_NAN_EXCESSIVO = {
    "Appendix_Wall_Layers",
    "Target_Sign",
    "Appendicolith",
    "Perfusion",
    "Perforation",
    "Surrounding_Tissue_Reaction",
    "Appendicular_Abscess",
    "Pathological_Lymph_Nodes",
    "Bowel_Wall_Thickening",
    "Conglomerate_of_Bowel_Loops",
    "Ileus",
    "Coprostasis",
    "Meteorism",
    "Enteritis",
    "Abscess_Location",
    "Lymph_Nodes_Location",
    "Gynecological_Findings",
}

# Features tabulares LIMPAS = todas exceto leakage, targets e NaN >70%
FEATURES_TABULARES_LIMPAS = (
    FEATURES_DEMOGRAFICAS
    + FEATURES_CLINICAS
    + FEATURES_LABORATORIAIS
    + [f for f in FEATURES_ULTRASSOM if f not in COLUNAS_NAN_EXCESSIVO]
)

# 7 criterios clinicos individuais do Alvarado (SEM o score composto)
FEATURES_INDIVIDUAIS_ALVARADO = [
    "WBC_Count",
    "Neutrophilia",
    "Ipsilateral_Rebound_Tenderness",
    "Migratory_Pain",
    "Loss_of_Appetite",
    "Nausea",
    "Body_Temperature",
]

# -----------------------------------------------------------
#  MAPEAMENTOS CATEGORICOS
# -----------------------------------------------------------

# Binarios simples
MAPEAMENTO_BINARIO = {
    "yes": 1,
    "no": 0,
    "Yes": 1,
    "No": 0,
    "male": 1,
    "female": 0,
    "Male": 1,
    "Female": 0,
}

# Ordinais (escala clinica crescente)
MAPEAMENTO_ORDINAL = {
    # Peritonitis: severidade crescente
    "Peritonitis": {"no": 0, "local": 1, "generalized": 2},
    # Stool: tipo
    "Stool": {
        "normal": 0,
        "constipation": 1,
        "diarrhea": 2,
        "constipation, diarrhea": 3,
    },
    # Urina: concentracao crescente
    "Ketones_in_Urine": {"none": 0, "+": 1, "++": 2, "+++": 3},
    "RBC_in_Urine": {"none": 0, "+": 1, "++": 2, "+++": 3},
    "WBC_in_Urine": {"none": 0, "+": 1, "++": 2, "+++": 3},
    # Achados de ultrassom complexos
    "Appendix_Wall_Layers": {
        "intact": 0,
        "partially raised": 1,
        "raised": 2,
        "upset": 3,
    },
    "Perfusion": {"no": 0, "not assessed": 1, "yes": 2, "increased": 3},
    "Perforation": {"no": 0, "not excluded": 1, "suspected": 2, "yes": 3},
    "Appendicolith": {"no": 0, "not excluded": 1, "yes": 2},
    "Appendicular_Abscess": {"no": 0, "not excluded": 1, "yes": 2},
}

# Mapeamento semantico: nome da SPEC/formulario -> nome real no dataset
MAPEAMENTO_SPEC_PARA_DATASET = {
    "dor_migratoria": "Migratory_Pain",
    "anorexia": "Loss_of_Appetite",
    "nauseas_vomitos": "Nausea",
    "dor_fid": "Lower_Right_Abd_Pain",
    "descompressao_dolorosa": "Ipsilateral_Rebound_Tenderness",
    "temperatura": "Body_Temperature",
    "leucocitos": "WBC_Count",
    "neutrofilia": "Neutrophilia",
    "alvarado_score": "Alvarado_Score",
    "appendix_diameter": "Appendix_Diameter",
    "free_fluids": "Free_Fluids",
    "age": "Age",
    "bmi": "BMI",
    "sex": "Sex",
    "weight": "Weight",
}

# -----------------------------------------------------------
#  STATUS DE ELEGIBILIDADE
# -----------------------------------------------------------
STATUS_LIMPO = "LIMPO"
STATUS_RISCO = "RISCO"
STATUS_DESCARTADO = "DESCARTADO"

# -----------------------------------------------------------
#  CONFIGURACOES DE FEATURES
# -----------------------------------------------------------
CONFIGS = {
    "E": {
        "nome": "7 individuais + Free_Fluids (sem score)",
        "features_obrig": FEATURES_INDIVIDUAIS_ALVARADO + ["Free_Fluids"],
        "features_imputar": [],
        "status": STATUS_LIMPO,
        "descricao": "Features brutas sem variavel derivada: 7 criterios clinicos "
        "individuais + Free_Fluids. Sem data leakage.",
    },
    "F": {
        "nome": "Tabular completo Regensburg (sem leakage)",
        "features_obrig": [
            # Demograficas com NaN minimo (<1%)
            "Age",
            "Sex",
            "Weight",
            # Clinicas com NaN minimo (<3%)
            "Migratory_Pain",
            "Lower_Right_Abd_Pain",
            "Contralateral_Rebound_Tenderness",
            "Coughing_Pain",
            "Nausea",
            "Loss_of_Appetite",
            "Body_Temperature",
            # Laboratoriais com NaN minimo (<3%)
            "WBC_Count",
            "CRP",
            # US basico
            "US_Performed",
        ],
        "features_imputar": [
            # Demograficas com NaN moderado
            "BMI",
            "Height",
            # Clinicas com NaN moderado
            "Dysuria",
            "Stool",
            "Peritonitis",
            "Psoas_Sign",
            "Ipsilateral_Rebound_Tenderness",
            # Laboratoriais com NaN moderado
            "Neutrophil_Percentage",
            "Neutrophilia",
            "RBC_Count",
            "Hemoglobin",
            "RDW",
            "Thrombocyte_Count",
            "Ketones_in_Urine",
            "RBC_in_Urine",
            "WBC_in_Urine",
            # US com NaN alto (imputacao por mediana)
            "Appendix_on_US",
            "Appendix_Diameter",
            "Free_Fluids",
        ],
        "status": STATUS_LIMPO,
        "descricao": "Todas features tabulares limpas do Regensburg (sem leakage). "
        "33 features: demograficas + clinicas + laboratoriais + US. "
        "Imputacao por mediana para NaN. Alinhado com Marcinkevics et al. 2023.",
    },
    # Configs historicas mantidas para rastreabilidade
    "A": {
        "nome": "8 Alvarado completo (score + individuais)",
        "features_obrig": ["Alvarado_Score"] + FEATURES_INDIVIDUAIS_ALVARADO,
        "features_imputar": [],
        "status": STATUS_RISCO,
        "descricao": "RISCO: Alvarado_Score e variavel derivada do target.",
    },
    "B": {
        "nome": "8 Alvarado + Free_Fluids (imputado)",
        "features_obrig": ["Alvarado_Score"] + FEATURES_INDIVIDUAIS_ALVARADO,
        "features_imputar": ["Free_Fluids"],
        "status": STATUS_RISCO,
        "descricao": "RISCO: Alvarado_Score e variavel derivada do target.",
    },
    "C": {
        "nome": "10 features completas (sem imputacao)",
        "features_obrig": ["Alvarado_Score"]
        + FEATURES_INDIVIDUAIS_ALVARADO
        + ["Appendix_Diameter", "Free_Fluids"],
        "features_imputar": [],
        "status": STATUS_RISCO,
        "descricao": "RISCO: Alvarado_Score e variavel derivada do target.",
    },
    "D": {
        "nome": "DESCARTADA -- Data Leakage confirmado",
        "features_obrig": ["Alvarado_Score", "Appendix_Diameter", "Free_Fluids"],
        "features_imputar": [],
        "status": STATUS_DESCARTADO,
        "descricao": "DESCARTADA: 95.6% era data leakage, nao aprendizado.",
    },
}

CONFIG_PADRAO = "F"

# Features opcionais para runtime (campos que o usuario pode omitir no formulario)
# Features que o formulario web SEMPRE coleta (8 Alvarado):
FEATURES_FORM_ALVARADO = [
    "Migratory_Pain",
    "Loss_of_Appetite",
    "Nausea",
    "Lower_Right_Abd_Pain",
    "Contralateral_Rebound_Tenderness",
    "Body_Temperature",
    "WBC_Count",
    "Neutrophilia",
]

# Em RUNTIME (predicao via formulario web), todas as features que
# o formulario NAO coleta sao opcionais e recebem imputacao por mediana.
# Isso e DIFERENTE do treino onde as features obrigatorias descartam a linha.
FEATURES_OPCIONAIS_RUNTIME = [
    f
    for f in list(CONFIGS["F"]["features_obrig"])
    + list(CONFIGS["F"]["features_imputar"])
    if f not in FEATURES_FORM_ALVARADO
]

# ================================================================
# O PERIGO DO DATA LEAKAGE (Vazamento de Dados)
# Por que existe: Ocorre quando o modelo tem acesso a informações
# que ele não deveria saber no momento do diagnóstico.
# Analogia médica: É como um aluno que faz a prova de residência
# espiando o gabarito. Ele tira nota 10, mas na hora de atender
# o paciente de verdade, ele não sabe o que fazer.
# No nosso caso: O Alvarado_Score é calculado a partir do diagnóstico.
# Se entregarmos o Score para a IA prever o diagnóstico, ela só vai
# "copiar" o resultado, sem aprender a medicina por trás.
# ================================================================
DATA_LEAKAGE_EXPLICACAO = {
    "titulo": "Data Leakage Detectado e Corrigido",
    "definicao": (
        "Data leakage (vazamento de dados) ocorre quando informacao do target "
        "(variavel que se quer prever) vaza para as features de treino, "
        "inflando artificialmente a acuracia do modelo."
    ),
    "caso_detectado": (
        "O Alvarado Score e uma variavel DERIVADA dos sintomas clinicos que "
        "compoe o proprio diagnostico de apendicite. Ele foi criado por "
        "Alvarado (1986) como um sistema de pontuacao para prever apendicite. "
        "Usar o Alvarado Score como feature para prever apendicite e circular: "
        "o modelo nao esta 'aprendendo' — esta copiando a resposta."
    ),
    "evidencia": (
        "Config D (Alvarado_Score + ultrassom) obteve 95.6% de acuracia, "
        "enquanto Config E (7 features individuais + Free_Fluids) obteve ~69%. "
        "A diferenca de 26 pontos percentuais nao e aprendizado real — "
        "e a correlacao intrinseca entre o score e o diagnostico."
    ),
    "colunas_excluidas": sorted(list(COLUNAS_EXCLUIDAS)),
    "motivos_exclusao": {
        "Alvarado_Score": "Variavel derivada do target (score preditivo = leakage)",
        "Paedriatic_Appendicitis_Score": "Idem Alvarado — score preditivo derivado",
        "Management": "Target alternativo (decisao clinica pos-diagnostico)",
        "Severity": "Target alternativo (gravidade determinada pos-diagnostico)",
        "Length_of_Stay": "Leakage pos-desfecho (tempo de internacao revela gravidade)",
        "Segmented_Neutrophils": "93% NaN — ruido excessivo para imputacao",
    },
    "referencia": "Kaufman et al. (2012). Leakage in Data Mining. DOI:10.1145/2020408.2020496",
}

# -----------------------------------------------------------
#  CONTEUDO PEDAGOGICO: SELECAO DE MODELO
# -----------------------------------------------------------
SELECAO_MODELO_EXPLICACAO = {
    "titulo": "Criterio de Selecao: Integridade Metodologica antes de Acuracia",
    "principio": (
        "A selecao de modelo considera integridade metodologica ANTES de acuracia. "
        "Acuracia alta em modelo contaminado vale menos que acuracia honesta "
        "em modelo limpo."
    ),
    "criterio": (
        "Apenas configuracoes com status LIMPO (sem variaveis derivadas do target) "
        "sao elegiveis para selecao automatica. Entre as elegiveis, seleciona-se "
        "a de maior acuracia no conjunto de teste."
    ),
    "status_possiveis": {
        "LIMPO": "Sem variaveis derivadas do target. Elegivel para selecao.",
        "RISCO": "Contem variavel derivada (ex: Alvarado_Score). Excluida da selecao.",
        "DESCARTADO": "Data leakage confirmado experimentalmente. Excluida da selecao.",
    },
    "referencia": "Kaufman et al. (2012). Leakage in Data Mining. DOI:10.1145/2020408.2020496",
}


# ============================================================
#  FUNCOES DE PRE-PROCESSAMENTO
# ============================================================


def _normalizar_nomes_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nomes de colunas do dataset (remove espacos extras)."""
    df.columns = [col.strip() for col in df.columns]
    return df


def _validar_colunas(df: pd.DataFrame, colunas_necessarias: list) -> None:
    """Valida que as colunas necessarias estao presentes no dataset."""
    colunas_presentes = set(df.columns)
    colunas_faltando = [c for c in colunas_necessarias if c not in colunas_presentes]
    if colunas_faltando:
        raise ValueError(
            f"Dataset corrompido -- colunas ausentes: {colunas_faltando}\n"
            f"Colunas encontradas: {sorted(colunas_presentes)}"
        )


def _converter_categoricas(df: pd.DataFrame, features: list) -> pd.DataFrame:
    """
    Converte colunas categoricas (object) para numerico.

    Estrategia:
      1. Colunas com mapeamento ordinal definido -> usa MAPEAMENTO_ORDINAL
      2. Colunas binarias (yes/no, male/female) -> usa MAPEAMENTO_BINARIO
      3. Colunas com outros valores string -> tenta binario, senao NaN
    """
    df = df.copy()
    for col in features:
        if col not in df.columns:
            continue
        if df[col].dtype != object:
            continue

        if col in MAPEAMENTO_ORDINAL:
            # Mapeamento ordinal especifico
            df[col] = df[col].map(MAPEAMENTO_ORDINAL[col])
        else:
            # Tentar mapeamento binario generico
            df[col] = df[col].map(MAPEAMENTO_BINARIO)

    return df


def carregar_e_processar(raw_path: str, config: str = "F") -> dict:
    """
    Carrega o dataset bruto, limpa, normaliza e faz o split.

    Parametro config define qual conjunto de features usar.

    Estrategia de NaN em tres etapas rastreadas:
      Etapa 0: Target NaN -> descarte (nao negociavel)
      Camada 1: Features obrigatorias NaN -> descarte
      Camada 2: Features a imputar -> mediana (se config define)
    """
    if config not in CONFIGS:
        raise ValueError(f"Config invalida: {config}. Use: {list(CONFIGS.keys())}")

    cfg = CONFIGS[config]
    features_obrig = list(cfg["features_obrig"])
    features_imputar = list(cfg["features_imputar"])
    features_usadas = features_obrig + features_imputar
    # Remover duplicatas mantendo ordem
    features_usadas = list(dict.fromkeys(features_usadas))

    # --- Carregar CSV bruto ---
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Dataset nao encontrado em: {raw_path}")

    df = pd.read_csv(raw_path)
    n_original = len(df)

    # --- Normalizar nomes de colunas ---
    df = _normalizar_nomes_colunas(df)

    # --- Validar colunas ---
    _validar_colunas(df, features_usadas + [COLUNA_TARGET])

    # --- Selecionar colunas ---
    df = df[features_usadas + [COLUNA_TARGET]].copy()

    # =========================================================
    # ESTRATÉGIA DE LIMPEZA — O Protocolo de Higiene
    # =========================================================

    # ETAPA 0: Se o diagnóstico final (Diagnosis) falta, descartamos a linha.
    # Técnico: O comando .dropna() joga fora (apaga da tabela) as linhas onde a resposta final está faltando.
    # Clínico: Não podemos ensinar a IA com casos onde não sabemos a resposta real.
    n_antes_target = len(df)
    # Converter features categoricas para numericas ANTES de limpar NaNs
    df = _converter_categoricas(df, features_usadas)

    # Target deve ser numerico (0 e 1)
    df[COLUNA_TARGET] = df[COLUNA_TARGET].map({"appendicitis": 1, "no appendicitis": 0})
    df.dropna(subset=[COLUNA_TARGET], inplace=True)
    n_removidos_target = n_antes_target - len(df)

    # CAMADA 1: Se faltam dados obrigatórios (ex: temperatura), descartamos.
    # Técnico: Remove pacientes que não tenham algum dos dados vitais exigidos.
    # Clínico: Um prontuário sem sinais vitais é inútil para estudo.
    n_antes_obrig = len(df)
    df.dropna(subset=features_obrig, inplace=True)
    n_removidos_obrig = n_antes_obrig - len(df)

    if len(df) == 0:
        raise ValueError(
            "Todas as linhas removidas apos limpeza das features obrigatorias."
        )

    # =========================================================
    # CAMADA 2: Divisao ANTES de imputar/normalizar (evitar leakage duplo)
    # =========================================================
    X = df[features_usadas].copy().astype(float)
    y = df[COLUNA_TARGET].copy()
    n_pacientes_final = len(X)

    # --- Divisão em Grupos de Estudo (Split) ---
    # Técnico: O train_test_split corta a tabela. Fazemos isso PRIMEIRO.
    X_train_raw, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=PREPROC_TEST_SIZE, random_state=PREPROC_RANDOM_STATE, stratify=y
    )
    X_test_raw, X_val_raw, y_test, y_val = train_test_split(
        X_temp,
        y_temp,
        test_size=PREPROC_VAL_FRAC,
        random_state=PREPROC_RANDOM_STATE,
        stratify=y_temp,
    )

    n_imputados = 0
    detalhes_nan = {}
    medianas_opcionais = {}

    if features_imputar:
        n_imputados = int(X[features_imputar].isna().sum().sum())
        detalhes_nan = {col: int(X[col].isna().sum()) for col in features_imputar}

    imputer = SimpleImputer(strategy="median")
    imputer.fit(X_train_raw)

    X_train_imp = pd.DataFrame(
        imputer.transform(X_train_raw), columns=features_usadas, index=X_train_raw.index
    )
    X_test_imp = pd.DataFrame(
        imputer.transform(X_test_raw), columns=features_usadas, index=X_test_raw.index
    )
    X_val_imp = pd.DataFrame(
        imputer.transform(X_val_raw), columns=features_usadas, index=X_val_raw.index
    )

    medianas_opcionais = {
        col: float(imputer.statistics_[features_usadas.index(col)])
        for col in features_usadas
        if col in FEATURES_OPCIONAIS_RUNTIME
    }

    # --- Normalizacao Min-Max (SPEC-02 6.3) ajustada SÓ NO TREINO ---
    scaler = MinMaxScaler()
    X_train = pd.DataFrame(
        scaler.fit_transform(X_train_imp),
        columns=features_usadas,
        index=X_train_imp.index,
    )
    X_test = pd.DataFrame(
        scaler.transform(X_test_imp), columns=features_usadas, index=X_test_imp.index
    )
    X_val = pd.DataFrame(
        scaler.transform(X_val_imp), columns=features_usadas, index=X_val_imp.index
    )

    # Identificar quais features sao opcionais em runtime para esta config
    features_opcionais_nesta_config = [
        f for f in features_usadas if f in FEATURES_OPCIONAIS_RUNTIME
    ]

    return {
        "X_train": X_train,
        "X_test": X_test,
        "X_val": X_val,
        "y_train": y_train,
        "y_test": y_test,
        "y_val": y_val,
        "features": features_usadas,
        "features_obrigatorias": [
            f for f in features_usadas if f not in FEATURES_OPCIONAIS_RUNTIME
        ],
        "features_opcionais": features_opcionais_nesta_config,
        "config": config,
        "config_nome": cfg["nome"],
        "config_descricao": cfg["descricao"],
        "n_original": n_original,
        "n_pacientes": n_pacientes_final,
        "n_removidos_target": n_removidos_target,
        "n_removidos_obrig": n_removidos_obrig,
        "n_removidos": n_removidos_target + n_removidos_obrig,
        "n_imputados_opcionais": n_imputados,
        "detalhes_nan_opcionais": detalhes_nan,
        "scaler": scaler,
        "imputer": imputer,
        "medianas_opcionais": medianas_opcionais,
    }
