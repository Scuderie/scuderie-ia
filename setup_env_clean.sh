#!/bin/bash
set -e

# Configuration
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"

echo "Initializing setup..."

# Check/Install Pyenv
if ! command -v pyenv &> /dev/null; then
    echo "Pyenv not found in PATH."
    if [ -d "$PYENV_ROOT/bin" ]; then
         echo "Adding Pyenv to PATH..."
         export PATH="$PYENV_ROOT/bin:$PATH"
    else
         echo "Installing Pyenv..."
         curl https://pyenv.run | bash
         export PATH="$PYENV_ROOT/bin:$PATH"
    fi
fi

# Initialize Pyenv
eval "$(pyenv init -)"

# Install Python
echo "Ensuring Python 3.10.13 is installed..."
if ! pyenv versions | grep "3.10.13" > /dev/null; then
    pyenv install 3.10.13 -s
fi
pyenv global 3.10.13
python --version

# Install Poetry
echo "Installing Poetry..."
pip install poetry

# Install Project dependencies
echo "Installing project dependencies..."
cd ~/progetti/scuderie-ia || exit 1
poetry install

echo "Setup Complete!"
