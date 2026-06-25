#!/usr/bin/env bash
# ============================================================
#  Kaysan AI 🧠  —  نصب روی Ubuntu
# ============================================================
set -e
echo "🧠 Kaysan installer"

sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ نصب تمام شد."
echo "👉 فایل .env را ویرایش کن (OWNER_ID و کلیدها)، بعد اجرا کن:"
echo "   source venv/bin/activate && python run.py"
