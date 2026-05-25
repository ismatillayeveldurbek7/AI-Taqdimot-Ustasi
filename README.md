# 🤖 AI Taqdimot Ustasi — Groq + Google Images

Professional AI taqdimot generator Telegram bot.

## ✨ Xususiyatlar

- 🚀 **Groq AI** (LLaMA 3 70B) — tez va bepul
- 🖼 **Google Images** — har bir slaydga avtomatik rasm
- 📊 **PPTX** — professional PowerPoint fayl
- 🌐 **3 til** — O'zbek, Rus, Ingliz
- 🎨 **5 uslub, 5 rang sxemasi**
- 💰 **Coin tizimi** + to'lov

---

## 🛠 O'rnatish

### 1. Fayllarni yuklab oling va papkaga kiring

```bash
cd AI-Taqdimot-Ustasi
```

### 2. Python paketlarini o'rnating

```bash
pip install -r requirements.txt
```

### 3. Node.js paketlarini o'rnating (PPTX uchun)

```bash
cd services
npm install pptxgenjs react react-dom react-icons sharp
cd ..
```

### 4. `.env` faylini sozlang

```bash
cp .env.example .env
nano .env
```

`.env` ga quyidagilarni kiriting:

| Kalit | Qayerdan olish |
|-------|---------------|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) — bepul |
| `GOOGLE_API_KEY` | [console.cloud.google.com](https://console.cloud.google.com) → Custom Search API |
| `GOOGLE_CX` | [cse.google.com](https://cse.google.com) → yangi engine → ID |

> **Eslatma:** `GOOGLE_API_KEY` va `GOOGLE_CX` ixtiyoriy. Ular bo'lmasa, bot rasimsiz ishlaydi.

### 5. Botni ishga tushiring

```bash
bash start.sh
# yoki
python main.py
```

---

## 🔑 API kalitlarni olish

### Groq API (bepul, tez)
1. [console.groq.com](https://console.groq.com) ga kiring
2. "API Keys" → "Create API Key"
3. Kalitni `.env` ga yozing

### Google Custom Search (rasmlar uchun)
1. [console.cloud.google.com](https://console.cloud.google.com) → yangi loyiha
2. "Custom Search JSON API" ni yoqing
3. "Credentials" → "API Key" yarating
4. [cse.google.com](https://cse.google.com) → "Add" → yangi search engine
5. "Search the entire web" ni yoqing → CX ID ni oling

---

## 📁 Fayl tuzilishi

```
├── main.py               # Bot ishga tushiruvchi
├── config.py             # Sozlamalar
├── database.py           # DB ulanish
├── models.py             # SQLAlchemy modellari
├── keyboards.py          # Telegram klaviaturalar
├── states.py             # FSM holatlari
├── .env.example          # Namuna .env
├── requirements.txt      # Python paketlar
├── start.sh              # Ishga tushirish skripti
├── handlers/
│   ├── user.py           # Foydalanuvchi handlerlar
│   ├── presentation.py   # Taqdimot yaratish
│   ├── payment.py        # To'lov tizimi
│   └── admin.py          # Admin panel
├── services/
│   ├── ai_service.py     # Groq AI + Google Images
│   ├── pptx_service.py   # PPTX generator (Python)
│   └── generate_pptx.js  # PPTX generator (Node.js)
└── utils/
    ├── logger.py
    └── validators.py
```
