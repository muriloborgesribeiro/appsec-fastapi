#!/bin/bash

# Detecta comando Python disponível
if command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v py >/dev/null 2>&1; then
    PYTHON_CMD="py"
else
    echo "Python não foi encontrado no sistema."
    exit 1
fi

echo "Usando interpretador: $PYTHON_CMD"

# Verifica se existe venv ou .venv
if [ -d "venv" ]; then
    VENV_PATH="venv"
elif [ -d ".venv" ]; then
    VENV_PATH=".venv"
else
    echo "Ambiente virtual não encontrado. Criando venv..."

    $PYTHON_CMD -m venv venv || {
        echo "Erro ao criar ambiente virtual"
        exit 1
    }

    VENV_PATH="venv"
fi

# Detecta script de ativação
if [ -f "$VENV_PATH/bin/activate" ]; then
    ACTIVATE_SCRIPT="$VENV_PATH/bin/activate"
elif [ -f "$VENV_PATH/Scripts/activate" ]; then
    ACTIVATE_SCRIPT="$VENV_PATH/Scripts/activate"
else
    echo "Script de ativação do venv não encontrado."
    exit 1
fi

# Ativa ambiente virtual
source "$ACTIVATE_SCRIPT" || {
    echo "Erro ao ativar ambiente virtual"
    exit 1
}

# Atualiza pip
python -m pip install --upgrade pip || {
    echo "Erro ao atualizar pip"
    exit 1
}

# Diretório do projeto
cd appspec || {
    echo "Diretório appspec não encontrado"
    exit 1
}

# Instala dependências se existir requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Instalando dependências do requirements.txt..."

    python -m pip install -r requirements.txt || {
        echo "Erro ao instalar dependências"
        exit 1
    }
fi

# Executa setup.py se existir
if [ -f "setup.py" ]; then
    echo "Executando setup.py..."

    python setup.py || {
        echo "Erro ao executar setup.py"
        exit 1
    }
fi


# Inicializa servidor
echo "Inicializando servidor..."

python app/main.py || {
    echo "Erro ao iniciar o servidor"
    exit 1
}