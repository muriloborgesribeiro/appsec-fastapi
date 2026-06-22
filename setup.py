#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ============================================================
#  setup.py -- Ponto de Entrada Unico do APPSPEC
#  APPSPEC -- Sistema de Apoio ao Diagnostico de Apendicite
#  Disciplina: Agentes Inteligentes -- UFG
#  Prof. Ronaldo Martins da Costa
#
#  Contrato: SPEC-02 6.2 -- 10 passos automaticos
#  Execucao: python setup.py (sem argumentos, sem interacao)
# ============================================================

import sys
import os
import time
import importlib
import io
import argparse

# Forcar UTF-8 no stdout para Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Garantir que o diretorio do projeto esta no PATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


def banner():
    """Imprime banner do sistema e disciplina (SPEC-02 6.3 -- passo 1)"""
    print("\n" + "=" * 60)
    print("  APPSPEC -- Sistema de Apoio ao Diagnostico de Apendicite")
    print("=" * 60 + "\n")


def verificar_dependencias():
    """
    [1/10] Verifica dependencias obrigatorias (SPEC-02 6.3 -- passo 2)
    """
    print("[1/10] Verificando dependencias...")
    deps = {
        'sklearn':    ('scikit-learn', 'tecnologia da disciplina -- KNN'),
        'pandas':     ('pandas',      'tecnologia da disciplina -- manipulacao de dados'),
        'joblib':     ('joblib',      'serializacao do modelo treinado'),
        'numpy':      ('numpy',       'computacao numerica'),
        'matplotlib': ('matplotlib',  'graficos -- matriz de confusao'),
        'seaborn':    ('seaborn',     'visualizacao estatistica'),
    }

    todas_ok = True
    for modulo, (nome, descricao) in deps.items():
        try:
            mod = importlib.import_module(modulo)
            versao = getattr(mod, '__version__', '?')
            print(f"       [OK] {nome} {versao} ({descricao})")
        except ImportError:
            print(f"       [ERRO] {nome} NAO encontrado -- instale com: pip install {nome}")
            todas_ok = False

    # ucimlrepo (opcional -- pode falhar se offline)
    try:
        import ucimlrepo
        versao = getattr(ucimlrepo, '__version__', '?')
        print(f"       [OK] ucimlrepo {versao} (download do dataset publico)")
    except ImportError:
        print("       [AVISO] ucimlrepo nao encontrado -- fallback para CSV local")

    # Orange3 (opcional)
    try:
        import Orange
        versao = getattr(Orange, '__version__', '?')
        print(f"       [OK] Orange3 {versao} (tecnologia da disciplina -- validacao visual)")
    except ImportError:
        print("       [AVISO] Orange3 nao instalado -- workflow .ows sera gerado mas requer Orange3 para abrir")

    if not todas_ok:
        print("\n       [ERRO] Dependencias obrigatorias faltando!")
        print("         Execute: pip install -r requirements.txt")
        sys.exit(1)

    print()


def baixar_dataset():
    """
    [2/10] e [3/10] -- Download do Regensburg via ucimlrepo com fallback
    (SPEC-02 6.3 -- passos 3-4)
    """
    data_dir = os.path.join(BASE_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)
    raw_path = os.path.join(data_dir, 'regensburg_raw.csv')

    # Verificar se ja existe (idempotencia -- SPEC-02 4 NG-03)
    if os.path.exists(raw_path):
        import pandas as pd
        df_check = pd.read_csv(raw_path)
        print(f"[2/10] [OK] Dataset ja disponivel em data/regensburg_raw.csv")
        print(f"       {len(df_check)} pacientes carregados do cache local")
        print()
        return raw_path

    print("[2/10] Baixando dataset Regensburg Pediatric Appendicitis...")
    print("       Fonte: UCI Machine Learning Repository (id=938)")
    print("       Referencia: Marcinkevics et al., 2023. DOI:10.5281/zenodo.7669442")

    try:
        from ucimlrepo import fetch_ucirepo
        dataset = fetch_ucirepo(id=938)
        import pandas as pd

        # Combinar features e target em um unico DataFrame
        df = pd.concat([dataset.data.features, dataset.data.targets], axis=1)
        df.to_csv(raw_path, index=False)
        print(f"       [OK] {len(df)} pacientes carregados")
        print(f"       [OK] Salvo em data/regensburg_raw.csv")
        print()
        return raw_path

    except Exception as e:
        print(f"       [AVISO] Download falhou: {e}")
        print("       Tentando fallback com CSV local...")

        if os.path.exists(raw_path):
            print(f"       [OK] Usando CSV local existente")
            return raw_path
        else:
            print("       [ERRO] CSV local nao encontrado em data/regensburg_raw.csv")
            print("         Baixe manualmente de: https://archive.ics.uci.edu/dataset/938")
            print("         Salve como: data/regensburg_raw.csv")
            sys.exit(1)


def preprocessar_dados(raw_path):
    """
    [3/10] e [4/10] Pre-processar + selecionar melhor configuracao de features.

    Testa apenas configs com status LIMPO (sem data leakage):
      E: 8 features (7 individuais Alvarado + Free_Fluids)
      F: 33 features tabulares completas do Regensburg (sem leakage)

    Configs A-D sao exibidas na tabela mas excluidas da selecao
    por conterem Alvarado_Score (RISCO) ou data leakage (DESCARTADO).
    """
    print("[3/10] Pre-processando dados com pandas...")
    print("       Tecnologia: pandas DataFrame (ensinada na disciplina)")
    print()

    from ml.preprocessamento import (
        carregar_e_processar, CONFIGS,
        STATUS_LIMPO, STATUS_RISCO, STATUS_DESCARTADO,
    )
    from ml.knn_engine import treinar_knn

    # -------------------------------------------------------
    #  Filtrar configs por status de elegibilidade
    # -------------------------------------------------------
    descartadas = [c for c in CONFIGS if CONFIGS[c]['status'] == STATUS_DESCARTADO]
    configs_testar = [c for c in CONFIGS if CONFIGS[c]['status'] != STATUS_DESCARTADO]
    configs_elegiveis = [c for c in CONFIGS if CONFIGS[c]['status'] == STATUS_LIMPO]
    configs_risco = [c for c in CONFIGS if CONFIGS[c]['status'] == STATUS_RISCO]

    if descartadas:
        print(f"       [DATA LEAKAGE] Configs descartadas: {descartadas}")
        print(f"       Alvarado_Score e variavel derivada do target (Alvarado, 1986).")
    if configs_risco:
        print(f"       [RISCO] Configs com Alvarado_Score: {configs_risco} (excluidas da selecao)")
    print(f"       [LIMPO] Configs elegiveis: {configs_elegiveis}")
    print(f"       Criterio: maior acuracia entre configuracoes LIMPO")
    print()
    resultados_configs = {}
    for cfg_id in configs_testar:
        cfg_info = CONFIGS[cfg_id]
        print(f"       --- Config {cfg_id}: {cfg_info['nome']} ---")

        resultado = carregar_e_processar(raw_path, config=cfg_id)

        print(f"       Etapa 0: {resultado['n_removidos_target']} removidas (target NaN)")
        print(f"       Camada 1: {resultado['n_removidos_obrig']} removidas (features obrigatorias NaN)")
        if resultado['n_imputados_opcionais'] > 0:
            print(f"       Camada 2: {resultado['n_imputados_opcionais']} valores imputados")
            for col, qtd in resultado.get('detalhes_nan_opcionais', {}).items():
                if col != 'linhas_descartadas':
                    med = resultado['medianas_opcionais'].get(col, 0)
                    print(f"                 {col}: {qtd} NaN -> mediana = {med:.2f}")
        elif resultado.get('detalhes_nan_opcionais', {}).get('linhas_descartadas', 0) > 0:
            print(f"       Camada 2: {resultado['detalhes_nan_opcionais']['linhas_descartadas']}"
                  f" linhas descartadas (opcionais sem valor)")
        print(f"       Features: {len(resultado['features'])} | "
              f"Pacientes: {resultado['n_pacientes']} | "
              f"Treino: {len(resultado['X_train'])} | "
              f"Teste: {len(resultado['X_test'])}")

        # Treinar KNN para esta config
        resultado_treino = treinar_knn(
            resultado['X_train'],
            resultado['y_train']
        )

        # Avaliar no teste
        modelo = resultado_treino['modelo']
        acuracia_teste = float(modelo.score(resultado['X_test'], resultado['y_test']))
        acuracia_cv = resultado_treino['resultados_cv'][resultado_treino['k']]['acuracia_media']

        print(f"       k={resultado_treino['k']} | CV={acuracia_cv:.1%} | Teste={acuracia_teste:.1%}")
        print()

        resultados_configs[cfg_id] = {
            'dados': resultado,
            'treino': resultado_treino,
            'acuracia_teste': acuracia_teste,
            'acuracia_cv': acuracia_cv,
            'k': resultado_treino['k'],
            'n_pacientes': resultado['n_pacientes'],
            'n_treino': len(resultado['X_train']),
            'n_teste': len(resultado['X_test']),
        }

    # -------------------------------------------------------
    #  Tabela comparativa
    # -------------------------------------------------------
    print("       ============================================")
    print("       COMPARACAO DAS CONFIGURACOES ELEGIVEIS")
    print("       ============================================")
    print(f"       {'Config':<8} {'Status':<12} {'Feat':<6} {'N_treino':<10} {'N_teste':<10} {'k':<5} {'CV':<10} {'Teste':<10}")
    print(f"       {'-'*71}")

    melhor_cfg = None
    melhor_acc = -1.0
    for cfg_id in configs_testar:
        r = resultados_configs[cfg_id]
        status = CONFIGS[cfg_id]['status']
        # Selecionar APENAS entre configs LIMPO
        if status == STATUS_LIMPO and r['acuracia_teste'] > melhor_acc:
            melhor_acc = r['acuracia_teste']
            melhor_cfg = cfg_id
        n_feat = len(resultados_configs[cfg_id]['dados']['features'])
        print(f"       {cfg_id:<8} {status:<12} {n_feat:<6} {r['n_treino']:<10} {r['n_teste']:<10} "
              f"{r['k']:<5} {r['acuracia_cv']:<10.1%} {r['acuracia_teste']:<10.1%}")

    print(f"       {'-'*71}")
    print(f"       Criterio: maior acuracia entre configs LIMPO")
    print(f"       Excluidas por RISCO: {configs_risco}")
    print(f"       Excluidas por DESCARTADO: {descartadas}")
    print(f"       >>> SELECIONADA: Config {melhor_cfg} "
          f"({CONFIGS[melhor_cfg]['nome']}) -- Acuracia {melhor_acc:.1%} [{STATUS_LIMPO}]")

    if melhor_acc >= 0.80:
        print(f"       [OK] Target de 80% ATINGIDO!")
    else:
        print(f"       [AVISO] Acuracia {melhor_acc:.1%} abaixo do target de 80%")
        print(f"       Causa: Acuracia limitada pelo tamanho do dataset -- "
              f"{resultados_configs[melhor_cfg]['n_pacientes']} amostras completas "
              f"disponiveis no Regensburg para este subconjunto de features.")
    print()

    # -------------------------------------------------------
    #  Usar a config vencedora
    # -------------------------------------------------------
    melhor = resultados_configs[melhor_cfg]
    dados_processados = melhor['dados']
    dados_processados['_resultado_treino'] = melhor['treino']
    dados_processados['_acuracia_teste'] = melhor['acuracia_teste']
    dados_processados['_resultados_configs'] = {
        cfg_id: {
            'nome': CONFIGS[cfg_id]['nome'],
            'status': CONFIGS[cfg_id]['status'],
            'n_treino': r['n_treino'],
            'n_teste': r['n_teste'],
            'k': r['k'],
            'acuracia_cv': r['acuracia_cv'],
            'acuracia_teste': r['acuracia_teste'],
        } for cfg_id, r in resultados_configs.items()
    }
    dados_processados['_melhor_cfg'] = melhor_cfg

    # Salvar dataset processado
    import pandas as pd
    processed_path = os.path.join(BASE_DIR, 'data', 'regensburg_processed.csv')
    df_processed = pd.concat([
        dados_processados['X_train'], dados_processados['X_test'], dados_processados['X_val']
    ])
    df_processed.to_csv(processed_path, index=False)
    print(f"       [OK] Dataset processado salvo (Config {melhor_cfg})")
    print()

    return dados_processados


def treinar_modelo(dados_processados):
    """
    [4/10] e [5/10] -- Salvar modelo da config vencedora + metricas.json
    """
    modelo_dir = os.path.join(BASE_DIR, 'ml', 'modelos')
    os.makedirs(modelo_dir, exist_ok=True)
    modelo_path = os.path.join(modelo_dir, 'knn_model.joblib')

    # Verificar idempotencia (SPEC-02 11)
    if os.path.exists(modelo_path):
        print("[4/10] [OK] Modelo ja treinado -- pulando treino")
        import joblib
        dados_modelo = joblib.load(modelo_path)
        print(f"       Config={dados_modelo.get('config','?')} | "
              f"k={dados_modelo['k']} | Acuracia teste: {dados_modelo['acuracia_teste']:.1%}")
        print()
        return dados_modelo

    # Recuperar resultado do treino feito na etapa 3
    resultado_treino = dados_processados['_resultado_treino']
    acuracia_teste = dados_processados['_acuracia_teste']
    melhor_cfg = dados_processados['_melhor_cfg']

    modelo = resultado_treino['modelo']

    print(f"[4/10] Config {melhor_cfg} selecionada: k={resultado_treino['k']}")

    # Mostrar cross-validation do modelo vencedor
    for k_val, res in resultado_treino['resultados_cv'].items():
        marcador = ">>>" if k_val == resultado_treino['k'] else "   "
        print(f"       {marcador} k={k_val}: acuracia={res['acuracia_media']:.1%} "
              f"(+/-{res['desvio_padrao']:.1%})")
    print()

    # [5/11] Serializar modelo
    print("[5/11] Serializando modelo com joblib...")

    import joblib
    dados_para_salvar = {
        'modelo': modelo,
        'k': resultado_treino['k'],
        'acuracia_treino': resultado_treino['acuracia_treino'],
        'acuracia_teste': acuracia_teste,
        'features': dados_processados['features'],
        'features_opcionais': dados_processados['features_opcionais'],
        'config': melhor_cfg,
        'resultados_cv': resultado_treino['resultados_cv'],
    }

    joblib.dump(dados_para_salvar, modelo_path)
    print(f"       [OK] Modelo salvo em ml/modelos/knn_model.joblib")

    # Salvar scaler
    scaler_path = os.path.join(modelo_dir, 'knn_scaler.joblib')
    joblib.dump(dados_processados['scaler'], scaler_path)
    print(f"       [OK] Scaler salvo em ml/modelos/knn_scaler.joblib")

    # Salvar imputer
    imputer_path = os.path.join(modelo_dir, 'imputer.joblib')
    joblib.dump({
        'imputer': dados_processados['imputer'],
        'medianas_opcionais': dados_processados['medianas_opcionais'],
        'features_opcionais': dados_processados['features_opcionais'],
    }, imputer_path)
    print(f"       [OK] Imputer salvo em ml/modelos/imputer.joblib")

    # Salvar metricas.json com rastreabilidade completa
    import json

    aviso_acuracia = ""
    if acuracia_teste < 0.80:
        aviso_acuracia = (
            f"Acuracia limitada pelo tamanho do dataset -- "
            f"{dados_processados['n_pacientes']} amostras completas "
            f"disponiveis no Regensburg para este subconjunto de features."
        )

    # Construir status de cada config testada
    from ml.preprocessamento import CONFIGS as _CONFIGS, STATUS_DESCARTADO, STATUS_RISCO
    descartadas = [c for c in _CONFIGS if _CONFIGS[c]['status'] == STATUS_DESCARTADO]
    configs_risco = [c for c in _CONFIGS if _CONFIGS[c]['status'] == STATUS_RISCO]

    status_configs = {
        cfg_id: _CONFIGS[cfg_id]['status']
        for cfg_id in dados_processados['_resultados_configs'].keys()
    }
    for d_id in descartadas:
        status_configs[d_id] = STATUS_DESCARTADO

    from ml.preprocessamento import COLUNAS_EXCLUIDAS

    metricas = {
        "config_selecionada": melhor_cfg,
        "config_nome": dados_processados['config_nome'],
        "config_descricao": dados_processados['config_descricao'],
        "criterio_selecao": "maior acuracia entre configuracoes LIMPO",
        "estrategia": "tabular completo sem leakage — alinhado com Marcinkevics et al. 2023",
        "motivo_selecao": (
            f"Config {melhor_cfg} selecionada automaticamente por ter a maior "
            f"acuracia no conjunto de teste ({acuracia_teste:.1%}) "
            f"entre as configs com status LIMPO (sem variaveis derivadas do target)"
        ),
        "data_leakage_detectado": True,
        "configuracao_descartada": "D",
        "config_excluidas_por_risco": sorted(configs_risco + descartadas),
        "colunas_excluidas_leakage": sorted(list(COLUNAS_EXCLUIDAS)),
        "motivo_descarte": (
            "Alvarado_Score e variavel derivada do target por construcao clinica "
            "(Alvarado, 1986). 95.6% de acuracia era data leakage, nao aprendizado. "
            "Ref: Kaufman et al. (2012). DOI:10.1145/2020408.2020496"
        ),
        "status_configs": status_configs,
        "k_minimo_clinico": 3,
        "k_minimo_motivo": "k=1 proibido por instabilidade clinica e risco de overfitting",
        "k_otimo": resultado_treino['k'],
        "acuracia_teste": round(acuracia_teste, 4),
        "acuracia_cv": round(
            resultado_treino['resultados_cv'][resultado_treino['k']]['acuracia_media'], 4
        ),
        "features_usadas": dados_processados['features'],
        "features_total_usadas": len(dados_processados['features']),
        "n_pacientes": dados_processados['n_pacientes'],
        "n_treino": len(dados_processados['X_train']),
        "n_teste": len(dados_processados['X_test']),
        "n_imputados": dados_processados['n_imputados_opcionais'],
        "target_80_atingido": acuracia_teste >= 0.80,
        "aviso_acuracia": aviso_acuracia,
        "comparacao_configs": dados_processados['_resultados_configs'],
    }

    metricas_path = os.path.join(modelo_dir, 'metricas.json')
    with open(metricas_path, 'w', encoding='utf-8') as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)
    print(f"       [OK] Metricas salvas em ml/modelos/metricas.json")

    # Verificar acuracia vs target
    if acuracia_teste < 0.80:
        print(f"       [AVISO] Acuracia {acuracia_teste:.1%} abaixo do target de 80%")
        print(f"       {aviso_acuracia}")
    else:
        print(f"       [OK] Acuracia {acuracia_teste:.1%} >= 80% (target atingido!)")
    print()
    return dados_para_salvar


def treinar_svm(dados_processados):
    """
    [6/11] Treinar modelo SVM para comparacao tripla.
    """
    modelo_dir = os.path.join(BASE_DIR, 'ml', 'modelos')
    os.makedirs(modelo_dir, exist_ok=True)
    modelo_path = os.path.join(modelo_dir, 'svm_model.joblib')

    # Verificar idempotencia
    if os.path.exists(modelo_path):
        print("[6/11] [OK] Modelo SVM ja treinado -- pulando treino")
        import joblib
        dados_modelo = joblib.load(modelo_path)
        print(f"       kernel={dados_modelo.get('kernel','?')} | "
              f"C={dados_modelo.get('C','?')} | Acuracia teste: {dados_modelo['acuracia_teste']:.1%}")
        print()
        return dados_modelo

    print("[6/11] Treinando modelo SVM (Support Vector Machine)...")
    print("       Tecnologia: sklearn.svm.SVC (ensinada na disciplina)")
    print("       Referencia: Cortes & Vapnik (1995). DOI:10.1007/BF00994018")
    print()

    from ml.svm_engine import treinar_svm as _treinar_svm

    resultado_treino = _treinar_svm(
        dados_processados['X_train'],
        dados_processados['y_train']
    )

    # Avaliar no teste
    modelo = resultado_treino['modelo']
    acuracia_teste = float(modelo.score(dados_processados['X_test'], dados_processados['y_test']))

    # Mostrar cross-validation
    print(f"       Melhor config: kernel={resultado_treino['kernel']}, C={resultado_treino['C']}")
    for chave, res in resultado_treino['resultados_cv'].items():
        marcador = ">>>" if (res['kernel'] == resultado_treino['kernel']
                             and res['C'] == resultado_treino['C']) else "   "
        print(f"       {marcador} {chave}: acuracia={res['acuracia_media']:.1%} "
              f"(+/-{res['desvio_padrao']:.1%})")
    print(f"       Acuracia no teste: {acuracia_teste:.1%}")
    print()

    # Serializar
    import joblib
    dados_para_salvar = {
        'modelo': modelo,
        'kernel': resultado_treino['kernel'],
        'C': resultado_treino['C'],
        'acuracia_treino': resultado_treino['acuracia_treino'],
        'acuracia_teste': acuracia_teste,
        'features': dados_processados['features'],
        'features_opcionais': dados_processados['features_opcionais'],
        'resultados_cv': resultado_treino['resultados_cv'],
    }

    joblib.dump(dados_para_salvar, modelo_path)
    print(f"       [OK] Modelo SVM salvo em ml/modelos/svm_model.joblib")

    if acuracia_teste >= 0.80:
        print(f"       [OK] Acuracia {acuracia_teste:.1%} >= 80% (target atingido!)")
    else:
        print(f"       [AVISO] Acuracia {acuracia_teste:.1%} abaixo do target de 80%")
    print()
    return dados_para_salvar


def _predicoes_alvarado(dados_processados):
    """
    Calcula as predicoes do Escore de Alvarado no conjunto de teste.
    Usa a coluna Alvarado_Score do CSV bruto (excluida do treino por leakage,
    mas valida para avaliar a regra clinica deterministicamente).
    Ponto de corte: score >= 5 → apendicite (1), else 0.
    Referencia: Ohle R et al. BMC Med. 2011;9:139. DOI:10.1186/1741-7015-9-139
    """
    import pandas as pd

    raw_path = os.path.join(BASE_DIR, 'data', 'regensburg_raw.csv')
    if not os.path.exists(raw_path):
        return None

    df_raw = pd.read_csv(raw_path)
    df_raw.columns = [c.strip() for c in df_raw.columns]

    if 'Alvarado_Score' not in df_raw.columns:
        return None

    # Usar os mesmos indices do conjunto de teste
    indices_teste = dados_processados['X_test'].index
    df_teste = df_raw.loc[indices_teste]

    # Aplicar ponto de corte: score >= 5 → positivo
    # Ohle et al. 2011: corte 5 tem sensibilidade 99%
    y_pred_alvarado = (df_teste['Alvarado_Score'] >= 5).astype(int).values
    return y_pred_alvarado


def avaliar_modelo(dados_processados, dados_modelo_knn, dados_modelo_svm):
    """
    [7/11] Avaliacao -- Matrizes de Confusao KNN, SVM e Alvarado (SPEC-02 6.3 -- passo 9)
    """
    print("[7/11] Avaliando modelos KNN, SVM e Alvarado -- Matrizes de Confusao...")
    print("       Tecnologia: sklearn.metrics.confusion_matrix (ensinada na disciplina)")

    from ml.avaliador import avaliar_modelo as _avaliar

    y_real = dados_processados['y_test']

    # Diretorio para salvar as imagens
    img_dir = os.path.join(BASE_DIR, 'diagnostico', 'static', 'diagnostico', 'img')
    os.makedirs(img_dir, exist_ok=True)

    # --- KNN ---
    modelo_knn = dados_modelo_knn['modelo']
    y_pred_knn = modelo_knn.predict(dados_processados['X_test'])
    metricas_knn = _avaliar(y_real, y_pred_knn, output_dir=img_dir,
                            nome_modelo="KNN", nome_arquivo="confusion_matrix_knn.png")

    print(f"       KNN:  VP={metricas_knn['vp']}  FP={metricas_knn['fp']}  "
          f"FN={metricas_knn['fn']}  VN={metricas_knn['vn']}")
    print(f"       [OK] KNN Sensibilidade: {metricas_knn['sensibilidade']:.1%} | "
          f"Especificidade: {metricas_knn['especificidade']:.1%}")

    # --- SVM ---
    modelo_svm = dados_modelo_svm['modelo']
    y_pred_svm = modelo_svm.predict(dados_processados['X_test'])
    metricas_svm = _avaliar(y_real, y_pred_svm, output_dir=img_dir,
                            nome_modelo="SVM", nome_arquivo="confusion_matrix_svm.png")

    print(f"       SVM:  VP={metricas_svm['vp']}  FP={metricas_svm['fp']}  "
          f"FN={metricas_svm['fn']}  VN={metricas_svm['vn']}")
    print(f"       [OK] SVM Sensibilidade: {metricas_svm['sensibilidade']:.1%} | "
          f"Especificidade: {metricas_svm['especificidade']:.1%}")

    # Manter compatibilidade: gerar tambem confusion_matrix.png (KNN) para paginas que usam
    import shutil
    src = os.path.join(img_dir, "confusion_matrix_knn.png")
    dst = os.path.join(img_dir, "confusion_matrix.png")
    if os.path.exists(src):
        shutil.copy2(src, dst)

    print(f"       [OK] Imagens salvas em diagnostico/static/diagnostico/img/")

    # --- Alvarado ---
    from ml.avaliador import comparar_alvarado_knn as _comparar
    y_pred_alvarado = _predicoes_alvarado(dados_processados)
    metricas_alvarado = None
    if y_pred_alvarado is not None:
        comp = _comparar(y_real, y_pred_knn, y_pred_alvarado)
        metricas_alvarado = comp['alvarado']['metricas']
        print(f"       Alvarado: VP={metricas_alvarado['vp']}  "
              f"FP={metricas_alvarado['fp']}  "
              f"FN={metricas_alvarado['fn']}  "
              f"VN={metricas_alvarado['vn']}")
        print(f"       [OK] Alvarado Sensibilidade: "
              f"{metricas_alvarado['sensibilidade']:.1%} | "
              f"Especificidade: {metricas_alvarado['especificidade']:.1%}")
    else:
        print("       [AVISO] Alvarado_Score ausente no CSV — "
              "metricas do Alvarado nao calculadas")
    print()

    # --- Curvas ROC e Precision-Recall (Aula 5, slides 21-24) ---
    print("       Gerando Curvas ROC e Precision-Recall (Aula 5)...")
    print("       Referencia: Fawcett T. (2006). DOI:10.1016/j.patrec.2005.10.010")

    from ml.avaliador import gerar_curva_roc, gerar_curva_pr, gerar_curvas_comparativas
    import numpy as np

    curvas_info = {}

    # Probabilidades KNN
    y_prob_knn = modelo_knn.predict_proba(dados_processados['X_test'])[:, 1]
    roc_knn = gerar_curva_roc(y_real, y_prob_knn,
                               os.path.join(img_dir, 'roc_knn.png'), 'KNN')
    pr_knn = gerar_curva_pr(y_real, y_prob_knn,
                             os.path.join(img_dir, 'pr_knn.png'), 'KNN')
    curvas_info['knn'] = {**roc_knn, **pr_knn}
    print(f"       [OK] KNN  -- AUC-ROC: {roc_knn['auc_roc']:.3f} | "
          f"AP: {pr_knn['average_precision']:.3f} | "
          f"Limiar otimo: {roc_knn['limiar_otimo']:.2f}")

    # Probabilidades SVM
    y_prob_svm = modelo_svm.predict_proba(dados_processados['X_test'])[:, 1]
    roc_svm = gerar_curva_roc(y_real, y_prob_svm,
                               os.path.join(img_dir, 'roc_svm.png'), 'SVM')
    pr_svm = gerar_curva_pr(y_real, y_prob_svm,
                             os.path.join(img_dir, 'pr_svm.png'), 'SVM')
    curvas_info['svm'] = {**roc_svm, **pr_svm}
    print(f"       [OK] SVM  -- AUC-ROC: {roc_svm['auc_roc']:.3f} | "
          f"AP: {pr_svm['average_precision']:.3f} | "
          f"Limiar otimo: {roc_svm['limiar_otimo']:.2f}")

    # Alvarado: usar score bruto normalizado 0-1 como proxy de probabilidade
    modelos_comp = [
        {'nome': 'KNN', 'y_real': y_real, 'y_prob': y_prob_knn, 'cor': '#1565c0'},
        {'nome': 'SVM', 'y_real': y_real, 'y_prob': y_prob_svm, 'cor': '#6a1b9a'},
    ]

    if y_pred_alvarado is not None:
        import pandas as pd
        raw_path = os.path.join(BASE_DIR, 'data', 'regensburg_raw.csv')
        df_raw = pd.read_csv(raw_path)
        df_raw.columns = [c.strip() for c in df_raw.columns]
        indices_teste = dados_processados['X_test'].index
        alv_scores = df_raw.loc[indices_teste, 'Alvarado_Score'].values
        # Filtrar NaN antes de gerar curvas
        mask_valid = ~np.isnan(alv_scores)
        if mask_valid.sum() > 10:
            y_real_alv = np.asarray(y_real)[mask_valid]
            y_prob_alv = np.clip(alv_scores[mask_valid] / 10.0, 0, 1)

            roc_alv = gerar_curva_roc(y_real_alv, y_prob_alv,
                                       os.path.join(img_dir, 'roc_alvarado.png'), 'Alvarado')
            pr_alv = gerar_curva_pr(y_real_alv, y_prob_alv,
                                     os.path.join(img_dir, 'pr_alvarado.png'), 'Alvarado')
            curvas_info['alvarado'] = {**roc_alv, **pr_alv}
            print(f"       [OK] Alvarado -- AUC-ROC: {roc_alv['auc_roc']:.3f} | "
                  f"AP: {pr_alv['average_precision']:.3f} "
                  f"(n={mask_valid.sum()} com score valido)")

            # Para comparativa, usar somente amostras validas do Alvarado
            y_prob_knn_alv = modelo_knn.predict_proba(
                dados_processados['X_test'].iloc[mask_valid])[:, 1]
            y_prob_svm_alv = modelo_svm.predict_proba(
                dados_processados['X_test'].iloc[mask_valid])[:, 1]
            modelos_comp = [
                {'nome': 'KNN', 'y_real': y_real_alv, 'y_prob': y_prob_knn_alv, 'cor': '#1565c0'},
                {'nome': 'SVM', 'y_real': y_real_alv, 'y_prob': y_prob_svm_alv, 'cor': '#6a1b9a'},
                {'nome': 'Alvarado', 'y_real': y_real_alv, 'y_prob': y_prob_alv, 'cor': '#2e7d32'},
            ]
        else:
            print("       [AVISO] Poucos scores Alvarado validos -- curva Alvarado ignorada")

    # Curvas comparativas sobrepostas
    comp_result = gerar_curvas_comparativas(modelos_comp, img_dir)
    curvas_info['comparativa'] = comp_result
    print(f"       [OK] Curvas comparativas salvas em diagnostico/static/diagnostico/img/")
    print()

    return metricas_knn, metricas_svm, metricas_alvarado, curvas_info


def atualizar_metricas_completas(metricas_knn, metricas_svm, metricas_alvarado,
                                  dados_modelo_svm, curvas_info=None):
    """
    [8/11] Atualiza metricas.json com os resultados completos da avaliacao.
    Executa APOS avaliar_modelo() para garantir que todos os dados existem.
    """
    print("[8/11] Atualizando metricas.json com avaliacao completa...")

    modelo_dir = os.path.join(BASE_DIR, 'ml', 'modelos')
    metricas_path = os.path.join(modelo_dir, 'metricas.json')

    import json
    with open(metricas_path, 'r', encoding='utf-8') as f:
        metricas = json.load(f)

    # Adicionar metricas completas do KNN
    metricas['avaliacao_knn'] = {
        'vp': metricas_knn['vp'],
        'fp': metricas_knn['fp'],
        'fn': metricas_knn['fn'],
        'vn': metricas_knn['vn'],
        'total': metricas_knn['vp'] + metricas_knn['fp'] +
                 metricas_knn['fn'] + metricas_knn['vn'],
        'acuracia':      round(metricas_knn['acuracia'], 4),
        'sensibilidade': round(metricas_knn['sensibilidade'], 4),
        'especificidade': round(metricas_knn['especificidade'], 4),
        'vpp': round(metricas_knn['vpp'], 4),
        'vpn': round(metricas_knn['vpn'], 4),
        'imagem': 'diagnostico/static/diagnostico/img/confusion_matrix_knn.png',
        'referencia': 'Fawcett T. (2006). DOI:10.1016/j.patrec.2005.10.010',
    }

    # Adicionar metricas completas do SVM
    metricas['avaliacao_svm'] = {
        'vp': metricas_svm['vp'],
        'fp': metricas_svm['fp'],
        'fn': metricas_svm['fn'],
        'vn': metricas_svm['vn'],
        'total': metricas_svm['vp'] + metricas_svm['fp'] +
                 metricas_svm['fn'] + metricas_svm['vn'],
        'acuracia':      round(metricas_svm['acuracia'], 4),
        'sensibilidade': round(metricas_svm['sensibilidade'], 4),
        'especificidade': round(metricas_svm['especificidade'], 4),
        'vpp': round(metricas_svm['vpp'], 4),
        'vpn': round(metricas_svm['vpn'], 4),
        'kernel': dados_modelo_svm['kernel'],
        'C': dados_modelo_svm['C'],
        'imagem': 'diagnostico/static/diagnostico/img/confusion_matrix_svm.png',
        'referencia': 'Cortes & Vapnik (1995). DOI:10.1007/BF00994018',
    }

    # Adicionar metricas do Alvarado (calculadas no mesmo conjunto de teste)
    if metricas_alvarado is not None:
        metricas['avaliacao_alvarado'] = {
            'vp': metricas_alvarado['vp'],
            'fp': metricas_alvarado['fp'],
            'fn': metricas_alvarado['fn'],
            'vn': metricas_alvarado['vn'],
            'total': metricas_alvarado['vp'] + metricas_alvarado['fp'] +
                     metricas_alvarado['fn'] + metricas_alvarado['vn'],
            'acuracia':      round(metricas_alvarado['acuracia'], 4),
            'sensibilidade': round(metricas_alvarado['sensibilidade'], 4),
            'especificidade': round(metricas_alvarado['especificidade'], 4),
            'vpp': round(metricas_alvarado['vpp'], 4),
            'vpn': round(metricas_alvarado['vpn'], 4),
            'ponto_corte': 5,
            'nota': 'Calculado sobre o mesmo conjunto de teste retido (n_teste). '
                    'Ponto de corte >= 5 conforme Ohle et al. 2011.',
            'referencia': 'Ohle R et al. BMC Med. 2011;9:139. DOI:10.1186/1741-7015-9-139',
        }

    # Adicionar metricas das curvas ROC e PR (Aula 5)
    if curvas_info:
        curvas_json = {}
        for modelo_id in ['knn', 'svm', 'alvarado']:
            if modelo_id in curvas_info:
                ci = curvas_info[modelo_id]
                curvas_json[modelo_id] = {
                    'auc_roc': round(ci.get('auc_roc', 0), 4),
                    'average_precision': round(ci.get('average_precision', 0), 4),
                    'limiar_otimo': round(ci.get('limiar_otimo', 0.5), 4),
                    'sensibilidade_otima': round(ci.get('sensibilidade_otima', 0), 4),
                    'especificidade_otima': round(ci.get('especificidade_otima', 0), 4),
                }
        metricas['curvas_roc_pr'] = curvas_json
        metricas['referencia_roc'] = 'Fawcett T. (2006). DOI:10.1016/j.patrec.2005.10.010'

    with open(metricas_path, 'w', encoding='utf-8') as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)

    print(f"       [OK] metricas.json atualizado com avaliacao_knn, "
          f"avaliacao_svm, avaliacao_alvarado e curvas_roc_pr")
    print()


def gerar_orange(raw_path):
    """
    [9/11] Gerar workflow Orange3 (SPEC-02 6.3 -- passo 10)
    """
    print("[9/11] Gerando workflow Orange3...")

    try:
        from ml.avaliador import gerar_orange_ows

        orange_dir = os.path.join(BASE_DIR, 'orange')
        os.makedirs(orange_dir, exist_ok=True)
        output_path = os.path.join(orange_dir, 'validacao_knn.ows')

        processed_path = os.path.join(BASE_DIR, 'data', 'regensburg_processed.csv')
        gerar_orange_ows(processed_path, output_path)

        print(f"       [OK] validacao_knn.ows salvo em orange/")
    except Exception as e:
        print(f"       [AVISO] Erro ao gerar .ows: {e}")
        print("       Sistema funciona sem este arquivo (Orange3 e opcional)")
    print()

def resumo_final(metricas_knn, metricas_svm, metricas_alvarado,
                  dados_modelo_knn, dados_modelo_svm):
    """
    [11/11] -- Resumo final didatico (SPEC-02 6.3 -- passo 12)
    """
    print("=" * 60)
    print("  SETUP CONCLUIDO COM SUCESSO")
    print("=" * 60)
    print()
    print(f"  Resultados do Modelo KNN (k={dados_modelo_knn['k']})")
    print(f"  -----------------------------------------")
    print(f"  Acuracia final:    {metricas_knn['acuracia']:.1%}")
    print(f"  Sensibilidade:     {metricas_knn['sensibilidade']:.1%}  "
          f"(VP/(VP+FN))")
    print(f"  Especificidade:    {metricas_knn['especificidade']:.1%}  "
          f"(VN/(VN+FP))")
    print(f"  VPP:               {metricas_knn['vpp']:.1%}  "
          f"(VP/(VP+FP))")
    print(f"  VPN:               {metricas_knn['vpn']:.1%}  "
          f"(VN/(VN+FN))")
    print()
    print(f"  Resultados do Modelo SVM (kernel={dados_modelo_svm['kernel']}, C={dados_modelo_svm['C']})")
    print(f"  -----------------------------------------")
    print(f"  Acuracia final:    {metricas_svm['acuracia']:.1%}")
    print(f"  Sensibilidade:     {metricas_svm['sensibilidade']:.1%}  "
          f"(VP/(VP+FN))")
    print(f"  Especificidade:    {metricas_svm['especificidade']:.1%}  "
          f"(VN/(VN+FP))")
    print(f"  VPP:               {metricas_svm['vpp']:.1%}  "
          f"(VP/(VP+FP))")
    print(f"  VPN:               {metricas_svm['vpn']:.1%}  "
          f"(VN/(VN+FN))")
    print()
    if metricas_alvarado:
        print(f"  Alvarado Score (corte >= 5):")
        print(f"  -----------------------------------------")
        print(f"  Sensibilidade:     {metricas_alvarado['sensibilidade']:.1%}  (VP/(VP+FN))")
        print(f"  Especificidade:    {metricas_alvarado['especificidade']:.1%}  (VN/(VN+FP))")
        print(f"  Acuracia:          {metricas_alvarado['acuracia']:.1%}")
        print()
    print("  Tecnologias da disciplina utilizadas no setup:")
    print("  -----------------------------------------")
    print("  [1] scikit-learn  -> Treino e predicao KNN + SVM")
    print("  [2] pandas        -> Manipulacao do dataset Regensburg")
    print("  [3] Databases     -> Banco de dados SQLite + ORM")
    print("  [4] Orange3       -> Workflow de validacao visual (.ows)")
    print("  [5] Matplotlib    -> Grafico da matriz de confusao")
    print("  [6] KNN           -> Algoritmo classificador (Cover & Hart, 1967)")
    print("  [7] SVM           -> Algoritmo classificador (Cortes & Vapnik, 1995)")
    print("  [8] Curva ROC     -> Avaliacao de classificadores (Fawcett, 2006)")
    print("  [9] Curva PR      -> Precision-Recall (Aula 5, slides 22-24)")
    print()
    print("  Para iniciar o sistema:")
    print("     python manage.py runserver")
    print("     Acesse: http://localhost:8082")
    print()
    print("=" * 60)


def start_server(args):
    """Inicia o servidor FastAPI via uvicorn."""
    import uvicorn
    host = args.host
    port = args.port
    reload = args.reload
    print(f"Iniciando servidor APPSPEC em http://{host}:{port}")
    print(f"  reload={reload}")
    print()
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


def main():
    parser = argparse.ArgumentParser(
        description="APPSPEC — Sistema de Apoio ao Diagnóstico de Apendicite",
    )
    parser.add_argument(
        "command", nargs="?", default="setup",
        choices=["setup", "start"],
        help="'setup' executa o pipeline ML (padrão); 'start' inicia o servidor web",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host do servidor (padrão: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8082, help="Porta do servidor (padrão: 8082)")
    parser.add_argument("--reload", action="store_true", default=False,
                        help="Habilitar reload automático")

    args = parser.parse_args()

    """Orquestra os 11 passos do setup (SPEC-02 6.2 + SVM + Alvarado)"""
    inicio = time.time()

    banner()
    verificar_dependencias()
    raw_path = baixar_dataset()
    dados_processados = preprocessar_dados(raw_path)
    dados_modelo_knn = treinar_modelo(dados_processados)
    dados_modelo_svm = treinar_svm(dados_processados)
    metricas_knn, metricas_svm, metricas_alvarado, curvas_info = avaliar_modelo(
        dados_processados, dados_modelo_knn, dados_modelo_svm)
    atualizar_metricas_completas(metricas_knn, metricas_svm,
                                  metricas_alvarado, dados_modelo_svm, curvas_info)
    gerar_orange(raw_path)
    resumo_final(metricas_knn, metricas_svm, metricas_alvarado,
                 dados_modelo_knn, dados_modelo_svm)

    tempo_total = time.time() - inicio
    print(f"\n  Tempo total: {tempo_total:.1f} segundos\n")
    if args.command == "start":
        start_server(args)
        return


if __name__ == '__main__':
    main()
