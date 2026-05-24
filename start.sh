#!/bin/bash
echo "🤖 AI Taqdimot Ustasi Bot ishga tushmoqda..."

# .env faylini tekshirish
if [ ! -f .env ]; then
    echo "❌ .env fayli topilmadi!"
    exit 1
fi

# Virtual environment (agar mavjud bo'lsa)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

python main.py
