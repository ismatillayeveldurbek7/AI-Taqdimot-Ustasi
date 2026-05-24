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
    lang_instruction = LANG_MAP.get(language, "in English")
    style_instruction = STYLE_MAP.get(style, "professional")
    color_instruction = COLOR_LABEL.get(color, "Ko'k")

    detail_note = (
        "Har bir slaydda batafsil matn, kalit fikrlar, statistika/misollar, "
        "tavsiya etilgan rasm/ikonka tavsifini ham yozing."
        if is_premium
        else "Har bir slaydda qisqa, aniq professional matn yozing."
    )

    return f"""Siz professional taqdimot yaratuvchi AI assistantsiz.

Quyidagi ma'lumotlar asosida {slides} ta slayddan iborat yuqori sifatli taqdimot yarating:

- Mavzu: {topic}
- Til: {lang_instruction}
- Uslub: {style_instruction}
- Rang sxemasi: {color_instruction}
- {detail_note}

MUHIM: Faqat JSON formatida javob bering. Boshqa hech narsa yozmang.

JSON tuzilishi:
{{
  "title": "Taqdimot sarlavhasi",
  "slides": [
    {{
      "number": 1,
      "title": "Slayd sarlavhasi",
      "content": "Asosiy matn (3-5 gap)",
      "key_points": ["Kalit fikr 1", "Kalit fikr 2", "Kalit fikr 3"],
      "image_suggestion": "Tavsiya etilgan rasm tavsifi",
      "speaker_notes": "Notiqqa eslatma"
    }}
  ]
}}

Slayd tuzilishi:
- 1-slayd: Sarlavha va kirish
- 2-slayd: Mavzuning ahamiyati
- 3-slayd: Asosiy tushunchalar
- O'rta slaydlar: Batafsil bo'limlar
- Oxirgi slayd: Xulosa va rahmat

Faqat JSON qaytaring, markdown yoki boshqa format bo'lmasin."""


async def generate_presentation(topic, slides, language, style, color, output_type):
    is_premium = output_type == "premium"
    prompt = _build_prompt(topic, slides, language, style, color, is_premium)

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config={
                "temperature": 0.8,
                "max_output_tokens": 4000,
            },
        )

        raw = response.text or ""
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        data = json.loads(raw)
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
