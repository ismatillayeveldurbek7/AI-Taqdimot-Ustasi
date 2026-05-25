"""
AI Taqdimot Ustasi — AI Service (OpenAI ChatGPT)
Modellar: gpt-4o-mini (asosiy) → gpt-3.5-turbo (fallback)
Retry, timeout, fallback, aniq log.
"""

import json
import re
import asyncio
import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)


# Modellar (birinchisidan boshlab sinab ko'riladi)
OPENAI_MODELS = [
    "gpt-4o-mini",
    "gpt-3.5-turbo",
]

LANG_MAP = {
    "uzbek":   "O'zbek tilida yoz",
    "russian": "Пиши на русском языке",
    "english": "Write in English",
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


def _build_messages(topic: str, slides: int, language: str,
                    style: str, color: str, is_premium: bool) -> list:
    lang  = LANG_MAP.get(language, "O'zbek tilida yoz")
    styl  = STYLE_MAP.get(style,   "professional")
    clr   = COLOR_LABEL.get(color, "Ko'k rang sxemasi")

    detail = (
        "Har bir slaydda batafsil matn (5-7 gap), 4 ta kalit fikr, "
        "rasm tavsifi va notiq eslatmasini yozing."
        if is_premium else
        "Har bir slaydda qisqa, aniq va professional matn (3-4 gap), 3 ta kalit fikr."
    )

    system_prompt = (
        "Sen professional taqdimot yaratuvchi AI assistantsan. "
        "FAQAT toza JSON qaytarasan — markdown, izoh, ``` belgilar YO'Q. "
        f"Til: {lang}."
    )

    user_prompt = f"""Quyidagi ma'lumotlar asosida {slides} ta slayddan iborat taqdimot yaratamiz:

Mavzu: {topic}
Uslub: {styl}
Rang sxemasi: {clr}
Talab: {detail}

FAQAT bu JSON tuzilmasida qaytaras (boshqa hech narsa yozma):
{{
  "title": "Taqdimot sarlavhasi",
  "slides": [
    {{
      "number": 1,
      "title": "Slayd sarlavhasi",
      "content": "Asosiy matn.",
      "key_points": ["Kalit fikr 1", "Kalit fikr 2", "Kalit fikr 3"],
      "image_suggestion": "Rasm tavsifi",
      "speaker_notes": "Notiq eslatmasi"
    }}
  ]
}}

Slaydlar soni AYNAN {slides} ta. Birinchi slayd — kirish/muqova."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]


def _clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"```json\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```\s*",    "", raw)
    raw = raw.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return raw


async def generate_presentation(
    topic: str, slides: int, language: str,
    style: str, color: str, output_type: str,
) -> Optional[dict]:
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY topilmadi! .env faylini tekshiring.")
        return None

    is_premium = output_type == "premium"
    messages   = _build_messages(topic, slides, language, style, color, is_premium)
    last_error = None

    for model_name in OPENAI_MODELS:
        for attempt in range(2):
            try:
                logger.info(f"OpenAI urinish: model={model_name}, attempt={attempt+1}")
                t0 = time.time()

                response = await client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4096,
                    response_format={"type": "json_object"},
                )

                elapsed = time.time() - t0
                raw     = (response.choices[0].message.content or "").strip()
                logger.info(f"OpenAI javob ({elapsed:.1f}s, {len(raw)} belgi): {raw[:200]}")

                if not raw:
                    last_error = "Bo'sh javob"
                    continue

                data = json.loads(_clean_json(raw))

                data.setdefault("title", topic)
                if "slides" not in data or not isinstance(data["slides"], list) or len(data["slides"]) == 0:
                    last_error = "slides yo'q yoki bo'sh"
                    continue

                for i, s in enumerate(data["slides"]):
                    s.setdefault("number",           i + 1)
                    s.setdefault("title",            f"Slayd {i+1}")
                    s.setdefault("content",          "")
                    s.setdefault("key_points",       [])
                    s.setdefault("image_suggestion", "")
                    s.setdefault("speaker_notes",    "")

                logger.info(f"✅ AI muvaffaqiyatli: {len(data['slides'])} slayd ({model_name})")
                return data

            except RateLimitError:
                logger.warning(f"{model_name}: Rate limit — keyingi modelga o'tmoqda")
                last_error = "Rate limit"
                break

            except APITimeoutError:
                logger.warning(f"{model_name} attempt {attempt+1}: Timeout")
                last_error = "Timeout"

            except json.JSONDecodeError as e:
                logger.warning(f"{model_name} attempt {attempt+1}: JSON xatosi: {e}")
                last_error = f"JSON xatosi: {e}"

            except APIError as e:
                logger.warning(f"{model_name} attempt {attempt+1}: APIError: {e}")
                last_error = str(e)
                if e.status_code in (401, 403, 404):
                    break  # API key noto'g'ri yoki model yo'q — retry qilma

            except Exception as e:
                logger.warning(f"{model_name} attempt {attempt+1}: {e}")
                last_error = str(e)

            if attempt == 0:
                await asyncio.sleep(1.5)
        await asyncio.sleep(0.5)

    logger.error(f"❌ Barcha modellar xato berdi. Oxirgi xato: {last_error}")
    return None


def format_presentation_text(data: dict, is_premium: bool = False) -> str:
    lines = [f"✨ <b>{data.get('title', 'Taqdimot')}</b>\n"]
    for slide in data.get("slides", []):
        num        = slide.get("number", "")
        title      = slide.get("title",  "")
        content    = slide.get("content","")
        key_points = slide.get("key_points", [])
        image      = slide.get("image_suggestion", "")
        notes      = slide.get("speaker_notes",    "")

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
