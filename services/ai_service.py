import json
import re
import asyncio
import google.generativeai as genai
from config import GEMINI_API_KEY
from utils.logger import logger

genai.configure(api_key=GEMINI_API_KEY)

LANG_MAP = {
    "uzbek": "O'zbek tilida",
    "russian": "на русском языке",
    "english": "in English",
}

STYLE_MAP = {
    "Academic": "akademik uslubda, rasmiy va ilmiy",
    "Business": "biznes uslubda, professional va aniq",
    "Creative": "ijodiy uslubda, qiziqarli va innovatsion",
    "Educational": "ta'limiy uslubda, tushuntiruvchi va oddiy",
    "Minimal": "minimal uslubda, qisqa va lo'nda",
}

COLOR_LABEL = {
    "Blue": "Ko'k rang sxemasi",
    "Black": "Qora rang sxemasi",
    "White": "Oq rang sxemasi",
    "Green": "Yashil rang sxemasi",
    "PremiumDark": "Premium qoʻngʻir-qora rang sxemasi",
}


def _build_prompt(topic, slides, language, style, color, is_premium):
    lang_instruction = LANG_MAP.get(language, "O'zbek tilida")
    style_instruction = STYLE_MAP.get(style, "professional")
    color_instruction = COLOR_LABEL.get(color, "Ko'k rang sxemasi")

    detail_note = (
        "Har bir slaydda batafsil matn, kalit fikrlar, misollar, "
        "tavsiya etilgan rasm/ikonka tavsifi va notiq eslatmasini yozing."
        if is_premium
        else "Har bir slaydda qisqa, aniq va professional matn yozing."
    )

    return f"""
Siz professional taqdimot yaratuvchi AI assistantsiz.

Quyidagi ma'lumotlar asosida {slides} ta slayddan iborat taqdimot yarating:

Mavzu: {topic}
Til: {lang_instruction}
Uslub: {style_instruction}
Rang sxemasi: {color_instruction}
Qo'shimcha talab: {detail_note}

FAQAT TOZA JSON QAYTARING.
Markdown, izoh, ```json belgilarini yozmang.

JSON namunasi:

{{
  "title": "Taqdimot sarlavhasi",
  "slides": [
    {{
      "number": 1,
      "title": "Slayd sarlavhasi",
      "content": "Asosiy matn 3-5 gapdan iborat bo'lsin.",
      "key_points": [
        "Kalit fikr 1",
        "Kalit fikr 2",
        "Kalit fikr 3"
      ],
      "image_suggestion": "Rasm yoki ikonka tavsifi",
      "speaker_notes": "Notiq uchun qisqa eslatma"
    }}
  ]
}}

Slaydlar soni aynan {slides} ta bo'lsin.
"""


def _clean_json_text(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"```json", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```", "", raw)
    raw = raw.strip()

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)

    return raw


async def generate_presentation(topic, slides, language, style, color, output_type):
    is_premium = output_type == "premium"
    prompt = _build_prompt(topic, slides, language, style, color, is_premium)

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 4000,
                "response_mime_type": "application/json",
            },
        )

        raw = response.text or ""
        logger.info(f"Gemini raw response: {raw}")

        cleaned = _clean_json_text(raw)
        data = json.loads(cleaned)

        if "title" not in data:
            data["title"] = topic

        if "slides" not in data or not isinstance(data["slides"], list):
            logger.error("Gemini response does not contain slides list")
            return None

        return data

    except json.JSONDecodeError as e:
        logger.error(f"AI JSON parse error: {e}")
        return None

    except Exception as e:
        logger.error(f"AI generation error: {e}")
        return None


def format_presentation_text(data, is_premium=False):
    lines = [f"✨ <b>{data.get('title', 'Taqdimot')}</b>\n"]

    for slide in data.get("slides", []):
        num = slide.get("number", "")
        title = slide.get("title", "")
        content = slide.get("content", "")
        key_points = slide.get("key_points", [])
        image = slide.get("image_suggestion", "")
        notes = slide.get("speaker_notes", "")

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
