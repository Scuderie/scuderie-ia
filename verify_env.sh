#!/bin/bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

cd ~/progetti/scuderie-ia || exit 1

# Fix missing README issue
touch README.md

echo "Finalizing Poetry install..."
poetry install

echo "Verifying Torch..."
poetry run python -c 'import torch; print(f"Torch: {torch.__version__}")'
