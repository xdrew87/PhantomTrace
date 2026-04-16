#!/usr/bin/env bash
set -e

echo ""
echo "============================================="
echo " PhantomTrace - Setup"
echo "============================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "Install it with: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

echo "[1/4] Creating virtual environment..."
python3 -m venv .venv

echo "[2/4] Activating virtual environment..."
source .venv/bin/activate

echo "[3/4] Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "[4/4] Setting up config..."
if [ ! -f "config/.env" ]; then
    cp config/.env.example config/.env
    echo "[OK] Created config/.env from template."
    echo "[!]  Edit config/.env to add your API keys (optional)."
else
    echo "[OK] config/.env already exists, skipping."
fi

echo ""
echo "============================================="
echo " Setup complete!"
echo "============================================="
echo ""
echo "To run PhantomTrace:"
echo "  source .venv/bin/activate"
echo "  python main.py"
echo ""
