import json
import re
import asyncio
import google.generativeai as genai
from config import GEMINI_API_KEY

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
    "PremiumDark": "Premium qora premium rang sxemasi",
}

def clean_json(text):
    text = text.strip()
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        return match.group(0)

    return text

async def generate_presentation(
    topic,
    slides,
    language,
    style,
    color,
    output_type,
):

    try:

        lang = LANG_MAP.get(language, "O'zbek tilida")
        style_text = STYLE_MAP.get(style, "professional")
        color_text = COLOR_LABEL.get(color, "Ko'k")

        detail = (
            "Har bir slayd juda batafsil bo'lsin."
            if output_type == "premium"
            else "Har bir slayd professional va qisqa bo'lsin."
        )

        prompt = f"""
Sen professional presentation AI assistantsan.

Mavzu: {topic}

Slaydlar soni: {slides}

Til: {lang}

Uslub: {style_text}

Rang: {color_text}

Talab: {detail}

Faqat JSON format qaytar.

Format:

{{
  "title": "Presentation title",
  "slides": [
    {{
      "number": 1,
      "title": "Slide title",
      "content": "Main content",
      "key_points": ["Point 1", "Point 2"],
      "image_suggestion": "Image description",
      "speaker_notes": "Speaker note"
    }}
  ]
}}
"""

        model = genai.GenerativeModel("gemini-1.5-flash")

        response = await asyncio.to_thread(
            model.generate_content,
            prompt
        )

        raw_text = response.text

        cleaned = clean_json(raw_text)

        try:
            data = json.loads(cleaned)
        except:
            data = {
                "title": topic,
                "slides": [
                    {
                        "number": 1,
                        "title": "AI javobi",
                        "content": raw_text
                    }
                ]
            }

        return data

    except Exception as e:
        return {
            "title": "Xatolik",
            "slides": [
                {
                    "number": 1,
                    "title": "Gemini Error",
                    "content": str(e)
                }
            ]
        }


def format_presentation_text(data: dict, is_premium: bool = False) -> str:
    """
    Presentation ma'lumotlarini HTML formatli matnga o'giradi.
    """
    title = data.get("title", "Taqdimot")
    slides = data.get("slides", [])

    lines = [f"🎨 <b>{title}</b>\n"]

    for slide in slides:
        num = slide.get("number", "")
        stitle = slide.get("title", "")
        content = slide.get("content", "")
        key_points = slide.get("key_points", [])
        speaker_notes = slide.get("speaker_notes", "")

        lines.append(f"\n<b>━━━ Slayd {num}: {stitle} ━━━</b>")
        if content:
            lines.append(f"{content}")
        if key_points:
            lines.append("\n📌 <b>Asosiy fikrlar:</b>")
            for point in key_points:
                lines.append(f"  • {point}")
        if is_premium and speaker_notes:
            lines.append(f"\n🎤 <i>Izoh: {speaker_notes}</i>")

    return "\n".join(lines)
