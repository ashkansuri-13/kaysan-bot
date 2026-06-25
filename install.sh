#!/usr/bin/env bash
set -e
echo "Kaysan AI Bot Installer"
echo "======================="
INSTALL_DIR="${KAYSAN_DIR:-$HOME/kaysan-bot}"
echo "[1/5] Installing dependencies..."
sudo apt-get update -qq >/dev/null 2>&1
sudo apt-get install -y -qq python3 python3-venv python3-pip git >/dev/null 2>&1
echo "[2/5] Cloning repository..."
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR" && git pull >/dev/null 2>&1
else
    git clone https://github.com/ashkansuri-13/kaysan-bot.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi
echo "[3/5] Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "[4/5] Installing Python packages..."
pip install --upgrade pip -q >/dev/null 2>&1
pip install -r requirements.txt -q >/dev/null 2>&1
echo "[5/5] Configuring..."
if [ ! -f .env ]; then cp .env.example .env; fi
if [ -f kaysan-bot.service ]; then sudo cp kaysan-bot.service /etc/systemd/system/ && sudo systemctl daemon-reload; fi
echo ""
echo "Done! Next steps:"
echo "  1. nano $INSTALL_DIR/.env"
echo "  2. cd $INSTALL_DIR && source venv/bin/activate && python run.py"
echo "  Docs: https://github.com/ashkansuri-13/kaysan-bot"
