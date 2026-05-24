# 🤖 AI Taqdimot Generator Bot

Professional AI-powered Telegram bot for generating presentations with coin-based payments.

---

## 📁 Project Structure

```
bot/
├── main.py                  # Entry point
├── config.py                # All config & env vars
├── database.py              # DB engine, session, seed data
├── models.py                # SQLAlchemy ORM models
├── keyboards.py             # All keyboards (inline + reply)
├── states.py                # FSM states
├── handlers/
│   ├── user.py              # /start, balance, history
│   ├── payment.py           # Buy coins, receipt, approve/reject
│   ├── presentation.py      # Full 6-step wizard + AI generation
│   └── admin.py             # Full admin panel
├── services/
│   ├── ai_service.py        # OpenAI integration
│   ├── pptx_service.py      # python-pptx PPTX generator
│   └── payment_service.py   # Payment logic + future provider stubs
├── utils/
│   ├── logger.py            # Logging setup
│   └── validators.py        # Anti-spam + input validation
├── requirements.txt
└── .env.example
```

---

## ⚙️ Setup (Local)

### 1. Clone and enter the directory
```bash
cd bot/
```

### 2. Create virtual environment
```bash
python3.11 -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
```
Edit `.env` with your values:

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `ADMIN_IDS` | Your Telegram ID(s), comma-separated |
| `OPENAI_API_KEY` | From [platform.openai.com](https://platform.openai.com) |
| `CARD_NUMBER` | Your payment card number |
| `CARD_OWNER` | Card holder name |

### 5. Run the bot
```bash
python main.py
```

---

## 🚀 Deploy to Railway

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Create Railway project
1. Go to [railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your repo

### 3. Add environment variables
In Railway dashboard → **Variables** tab, add all from `.env`

### 4. Add start command
In Railway → **Settings** → **Start Command**:
```
python main.py
```

### 5. Deploy
Railway auto-deploys on push. Check **Logs** tab.

---

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Register and open main menu |
| `/admin` | Open admin panel (admins only) |
| `/cancel` | Cancel current operation |

---

## 💎 Features

### Users
- 🎨 **AI Presentation Wizard** — 6-step guided flow (topic → slides → language → style → color → output type)
- 💰 **Coin System** — buy packages via manual card payment
- 📊 **PPTX Export** — professionally designed slides with 5 color themes
- 📝 **Text Export** — formatted Telegram message
- ⭐ **Premium** — detailed with image suggestions & speaker notes
- 📂 **History** — last 10 presentations

### Admin Panel (`/admin`)
- 👥 User count & blocked stats
- 💰 Payment history & pending approvals
- ✅ One-click approve/reject with auto coin credit
- 🪙 Manually add/remove coins for any user
- 📢 Broadcast message to all users
- 🚫 Block/unblock users
- 📊 Full statistics (revenue, presentations, etc.)
- ⚙️ Change card number/owner live
- 🧾 Add/edit/disable coin packages

### Security
- Anti-spam rate limiting
- Admin-only routes
- Balance validation before generation
- Duplicate payment prevention
- Environment variable secrets

---

## 🎨 Presentation Output Types

| Type | Cost | Format |
|------|------|--------|
| 📝 Text only | 5 coins | Telegram message |
| 📊 PPTX file | 10 coins | .pptx download |
| ⭐ Premium | 15 coins | Text + image hints + speaker notes |

### PPTX Color Themes
- 🔵 Blue (Corporate)
- ⚫ Black (Elegant)
- ⚪ White (Clean)
- 🟢 Green (Nature)
- 🌑 Premium Dark (Luxury)

---

## 🔮 Future Payment Integrations

Stubs are ready in `services/payment_service.py`:
- **Click** (`ClickPaymentProvider`)
- **Payme** (`PaymePaymentProvider`)
- **Stripe** (`StripePaymentProvider`)
- **Telegram Payments** — add via `LabeledPrice` in aiogram

---

## 📦 Dependencies

```
aiogram==3.13.1      # Telegram bot framework
sqlalchemy==2.0.36   # ORM
aiosqlite==0.20.0    # Async SQLite
python-dotenv==1.0.1 # .env loading
openai==1.57.0       # AI generation
python-pptx==1.0.2   # PPTX creation
aiofiles==24.1.0     # Async file ops
Pillow==11.0.0       # Image processing
```

---

## 🛡️ Architecture Notes

- **Async everywhere** — `async/await` throughout
- **SQLite → PostgreSQL ready** — change `DATABASE_URL` to `postgresql+asyncpg://...`
- **Modular routers** — each handler file is an independent `aiogram.Router`
- **FSM states** — clean wizard flow using `aiogram.fsm`
- **Scalable** — ready for webhook mode, Redis FSM storage, and PostgreSQL
