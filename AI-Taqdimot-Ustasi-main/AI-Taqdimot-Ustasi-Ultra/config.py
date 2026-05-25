import os
from dotenv import load_dotenv

load_dotenv()

# ─── Bot ───────────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]

# ─── AI ────────────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "PASTE_YOUR_GEMINI_API_KEY")

# ─── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")

# ─── Payment ───────────────────────────────────────────────────────────────────
CARD_NUMBER: str = os.getenv("CARD_NUMBER", "0000 0000 0000 0000")
CARD_OWNER:  str = os.getenv("CARD_OWNER",  "Bot Admin")

# ─── Anti-spam ─────────────────────────────────────────────────────────────────
SPAM_LIMIT:  int = int(os.getenv("SPAM_LIMIT",  "5"))
SPAM_WINDOW: int = int(os.getenv("SPAM_WINDOW", "60"))

# ─── Coin prices ───────────────────────────────────────────────────────────────
PRICE_TEXT_PRESENTATION:    int = 5
PRICE_PPTX_PRESENTATION:    int = 10
PRICE_PREMIUM_PRESENTATION: int = 15

# ─── Presentation limits ───────────────────────────────────────────────────────
MIN_SLIDES: int = 3
MAX_SLIDES: int = 20


