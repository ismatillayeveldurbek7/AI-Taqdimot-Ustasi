import json
import re
from groq import AsyncGroq
from config import GROQ_API_KEY, GROQ_MODEL
from utils.logger import logger

# Groq async client — bir marta yaratiladi
_client = AsyncGroq(api_key=GROQ_API_KEY)

LANG_MAP = {
    "uzbek":   "O'zbek tilida",
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
    "PremiumDark": "Premium qo'ng'ir-qora rang sxemasi",
}


def _build_prompt(topic, slides, language, style, color, is_premium):
    lang_instruction  = LANG_MAP.get(language, "O'zbek tilida")
    style_instruction = STYLE_MAP.get(style, "professional")
    color_instruction = COLOR_LABEL.get(color, "Ko'k rang sxemasi")

    detail_note = (
        "Har bir slaydda batafsil matn, kalit fikrlar, misollar, "
        "tavsiya etilgan rasm/ikonka tavsifi va notiq eslatmasini yozing."
        if is_premium
        else "Har bir slaydda qisqa, aniq va professional matn yozing."
    )

    return f"""Siz professional taqdimot yaratuvchi AI assistantsiz.

Quyidagi ma'lumotlar asosida {slides} ta slayddan iborat taqdimot yarating:

Mavzu: {topic}
Til: {lang_instruction}
Uslub: {style_instruction}
Rang sxemasi: {color_instruction}
Qo'shimcha talab: {detail_note}

FAQAT TOZA JSON QAYTARING. Markdown, izoh, ```json belgilarini yozmang.

JSON strukturasi (aynan shu formatda):
{{
  "title": "Taqdimot sarlavhasi",
  "slides": [
    {{
      "number": 1,
      "title": "Slayd sarlavhasi",
      "content": "Asosiy matn 3-5 gapdan iborat.",
      "key_points": ["Kalit fikr 1", "Kalit fikr 2", "Kalit fikr 3"],
      "image_suggestion": "Rasm yoki ikonka tavsifi",
      "speaker_notes": "Notiq uchun qisqa eslatma"
    }}
  ]
}}

Slaydlar soni aynan {slides} ta bo'lsin. Faqat JSON, boshqa hech narsa yozma."""


def _clean_json(raw: str) -> str:
    raw = raw.strip()
    # ```json ... ``` yoki ``` ... ``` orasini olish
    raw = re.sub(r"```json\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```\s*", "", raw)
    raw = raw.strip()
    # { ... } ni topish
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    return match.group(0) if match else raw


async def generate_presentation(topic, slides, language, style, color, output_type):
    is_premium = output_type == "premium"
    prompt = _build_prompt(topic, slides, language, style, color, is_premium)

    try:
        response = await _client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Siz faqat JSON formatida javob beradigan taqdimot yaratuvchi AI assistantsiz. "
                        "Hech qachon JSON dan tashqari matn yozma."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
            response_format={"type": "json_object"},  # Groq JSON mode
        )

        raw = response.choices[0].message.content or ""
        logger.info(f"Groq raw response length: {len(raw)}")

        cleaned = _clean_json(raw)
        data = json.loads(cleaned)

        if "title" not in data:
            data["title"] = topic

        if "slides" not in data or not isinstance(data["slides"], list):
            logger.error("Groq response: 'slides' maydoni yo'q")
            return None

        # Slayd sonini tekshirish
        if len(data["slides"]) == 0:
            logger.error("Groq response: slaydlar bo'sh")
            return None

        logger.info(f"Taqdimot yaratildi: {len(data['slides'])} slayd")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse xatosi: {e}\nRaw: {raw[:500]}")
        return None
    except Exception as e:
        logger.error(f"Groq API xatosi: {e}")
        return None


def format_presentation_text(data, is_premium=False):
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
