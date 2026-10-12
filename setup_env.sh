#!/bin/bash
# Creates the Python venv in goinfre and installs all required packages.
# Run this after cloning the repo or after goinfre gets wiped.

VENV_PATH="$HOME/goinfre/pyenv"

if [ ! -d "$VENV_PATH" ]; then
    echo "==> Creating venv at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
else
    echo "==> venv already exists at $VENV_PATH"
fi

echo "==> Installing packages..."
source "$VENV_PATH/bin/activate"
pip install pandas matplotlib seaborn sqlalchemy psycopg2-binary scikit-learn

echo ""
echo "Done. To activate: source $VENV_PATH/bin/activate"
echo "Or add this line to your ~/.zshrc to activate automatically:"
echo "  source $VENV_PATH/bin/activate"
