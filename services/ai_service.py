"""
AI Taqdimot Ustasi — AI Service (Gemini + fallback)
Mustahkam xato boshqaruvi: retry, timeout, fallback model, aniq log.
"""

import json
import re
import asyncio
import time
from typing import Optional
import google.generativeai as genai
from config import GEMINI_API_KEY
from utils.logger import logger

# API kalitini sozlash
genai.configure(api_key=GEMINI_API_KEY)

# ─── Model nomlari (birinchisidan boshlab sinab ko'riladi) ──────────────────────
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
]

# ─── Xarita ─────────────────────────────────────────────────────────────────────
LANG_MAP = {
    "uzbek": "O'zbek tilida",
    "russian": "на русском языке",
    "english": "in English",
}

STYLE_MAP = {
    "Academic":    "akademik uslubda, rasmiy va ilmiy",
    "Business":    "biznes uslubda, professional va aniq",
    "Creative":    "ijodiy uslubda, qiziqarli va innovatsion",
    "Educational": "ta'limiy uslubda, tushuntiruvchi va oddiy",
    "Minimal":     "minimal uslubda, qisqa va lo'nda",
}

COLOR_LABEL = {
    "Blue":        "Ko'k rang sxemasi",
    "Black":       "Qora rang sxemasi",
    "White":       "Oq rang sxemasi",
    "Green":       "Yashil rang sxemasi",
    "PremiumDark": "Premium qoʻngʻir-qora rang sxemasi",
}


# ─── Prompt yaratuvchi ──────────────────────────────────────────────────────────
def _build_prompt(topic: str, slides: int, language: str,
                  style: str, color: str, is_premium: bool) -> str:
    lang   = LANG_MAP.get(language, "O'zbek tilida")
    styl   = STYLE_MAP.get(style,   "professional")
    clr    = COLOR_LABEL.get(color, "Ko'k rang sxemasi")

    detail = (
        "Har bir slaydda batafsil matn, kalit fikrlar, misollar, "
        "tavsiya etilgan rasm/ikonka tavsifi va notiq eslatmasini yozing."
        if is_premium else
        "Har bir slaydda qisqa, aniq va professional matn yozing."
    )

    return f"""Siz professional taqdimot yaratuvchi AI assistantsiz.

Quyidagi ma'lumotlar asosida {slides} ta slayddan iborat taqdimot yarating:

Mavzu: {topic}
Til: {lang}
Uslub: {styl}
Rang sxemasi: {clr}
Qo'shimcha talab: {detail}

FAQAT TOZA JSON qaytaring. Markdown, izoh, ```json belgilarini YOZMANG.

JSON formati (aynan shu tuzilmada):
{{
  "title": "Taqdimot sarlavhasi",
  "slides": [
    {{
      "number": 1,
      "title": "Slayd sarlavhasi",
      "content": "Asosiy matn 3-5 gapdan iborat.",
      "key_points": ["Kalit fikr 1", "Kalit fikr 2", "Kalit fikr 3"],
      "image_suggestion": "Rasm tavsifi",
      "speaker_notes": "Notiq eslatmasi"
    }}
  ]
}}

Slaydlar soni AYNAN {slides} ta bo'lsin. Birinchi slayd — kirish/muqova."""


# ─── JSON tozalovchi ────────────────────────────────────────────────────────────
def _clean_json(raw: str) -> str:
    raw = raw.strip()
    # Markdown kod bloklarini olib tashlash
    raw = re.sub(r"```json\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```\s*", "", raw)
    raw = raw.strip()
    # Eng katta JSON ob'ektni topish
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return raw


# ─── Asosiy generator: retry + fallback modellar ────────────────────────────────
async def generate_presentation(
    topic: str,
    slides: int,
    language: str,
    style: str,
    color: str,
    output_type: str,
) -> Optional[dict]:
    """
    Taqdimot ma'lumotlarini Gemini orqali yaratadi.
    Xatolik bo'lsa, boshqa modelni sinaydi (3 ta urinish).
    """
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY topilmadi! .env faylini tekshiring.")
        return None

    is_premium = output_type == "premium"
    prompt = _build_prompt(topic, slides, language, style, color, is_premium)

    last_error = None

    for model_name in GEMINI_MODELS:
        for attempt in range(2):  # Har model uchun 2 urinish
            try:
                logger.info(f"AI urinish: model={model_name}, attempt={attempt+1}")
                t0 = time.time()

                model = genai.GenerativeModel(model_name)

                # Sinxron chaqiruvni async threadda ishlatish
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        model.generate_content,
                        prompt,
                        generation_config={
                            "temperature": 0.7,
                            "max_output_tokens": 4096,
                            "response_mime_type": "application/json",
                        },
                    ),
                    timeout=60.0,  # 60 soniya timeout
                )

                elapsed = time.time() - t0
                raw = (response.text or "").strip()
                logger.info(f"Gemini javob ({elapsed:.1f}s, {len(raw)} belgi): {raw[:200]}")

                if not raw:
                    logger.warning(f"{model_name}: bo'sh javob")
                    last_error = "Bo'sh javob"
                    continue

                cleaned = _clean_json(raw)
                data = json.loads(cleaned)

                # Majburiy tekshiruv
                if "title" not in data:
                    data["title"] = topic
                if "slides" not in data or not isinstance(data["slides"], list):
                    logger.error(f"{model_name}: 'slides' yo'q yoki noto'g'ri format")
                    last_error = "slides yo'q"
                    continue
                if len(data["slides"]) == 0:
                    logger.error(f"{model_name}: bo'sh slides massivi")
                    last_error = "Bo'sh slides"
                    continue

                # Har bir slaydda kerakli maydonlarni to'ldirish
                for i, s in enumerate(data["slides"]):
                    s.setdefault("number", i + 1)
                    s.setdefault("title", f"Slayd {i+1}")
                    s.setdefault("content", "")
                    s.setdefault("key_points", [])
                    s.setdefault("image_suggestion", "")
                    s.setdefault("speaker_notes", "")

                logger.info(f"✅ AI muvaffaqiyatli: {len(data['slides'])} slayd, model={model_name}")
                return data

            except asyncio.TimeoutError:
                elapsed = time.time() - t0
                logger.warning(f"{model_name} attempt {attempt+1}: TIMEOUT ({elapsed:.0f}s)")
                last_error = f"Timeout ({elapsed:.0f}s)"

            except json.JSONDecodeError as e:
                logger.warning(f"{model_name} attempt {attempt+1}: JSON xatosi: {e}")
                last_error = f"JSON xatosi: {e}"

            except Exception as e:
                err_str = str(e)
                logger.warning(f"{model_name} attempt {attempt+1}: {err_str}")
                last_error = err_str

                # Model topilmasa yoki API key noto'g'ri — keyingi modelga o'tish
                if any(k in err_str.lower() for k in [
                    "not found", "invalid", "api_key", "quota", "permission",
                    "404", "403", "401", "deprecated"
                ]):
                    logger.warning(f"{model_name} ishlatib bo'lmaydi, keyingiga o'tmoqda...")
                    break  # Bu model uchun retry qilma

            # Retry oldidan biroz kutish
            if attempt == 0:
                await asyncio.sleep(1.5)

        # Modellar o'rtasida kutish
        await asyncio.sleep(0.5)

    logger.error(f"❌ Barcha modellar xato berdi. Oxirgi xato: {last_error}")
    return None


# ─── Matn formatlash ─────────────────────────────────────────────────────────────
def format_presentation_text(data: dict, is_premium: bool = False) -> str:
    lines = [f"✨ <b>{data.get('title', 'Taqdimot')}</b>\n"]

    for slide in data.get("slides", []):
        num        = slide.get("number", "")
        title      = slide.get("title", "")
        content    = slide.get("content", "")
        key_points = slide.get("key_points", [])
        image      = slide.get("image_suggestion", "")
        notes      = slide.get("speaker_notes", "")

        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"📌 <b>Slayd {num}: {title}</b>")
        lines.append(f"\n{content}")

        if key_points:
            lines.append("\n🔹 <b>Kalit fikrlar:</b>")
            for kp in key_points:
                lines.append(f"  • {kp}")

        if is_premium:
            if image:
                lines.append(f"\n🖼 <i>Rasm tavsiyasi: {image}</i>")
            if notes:
                lines.append(f"🎤 <i>Notiq eslatmasi: {notes}</i>")

        lines.append("")

    return "\n".join(lines)
