"""
AI Taqdimot Ustasi — Groq AI + Google Image Search servisi
"""

import json
import re
import asyncio
import aiohttp
from config import GROQ_API_KEY, GROQ_MODEL, GOOGLE_API_KEY, GOOGLE_CX

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

LANG_MAP = {
    "uzbek": "O'zbek tilida yoz",
    "russian": "Напиши на русском языке",
    "english": "Write in English",
}

STYLE_MAP = {
    "Academic": "akademik uslubda, rasmiy va ilmiy tilda",
    "Business": "biznes uslubda, professional va aniq tilda",
    "Creative": "ijodiy uslubda, qiziqarli va innovatsion tilda",
    "Educational": "ta'limiy uslubda, tushuntiruvchi va oddiy tilda",
    "Minimal": "minimal uslubda, qisqa va lo'nda tilda",
}

COLOR_LABEL = {
    "Blue": "Ko'k rang sxemasi",
    "Black": "Qora rang sxemasi",
    "White": "Oq rang sxemasi",
    "Green": "Yashil rang sxemasi",
    "PremiumDark": "Premium qora rang sxemasi",
}


def clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text


async def search_image(query: str) -> str | None:
    """
    Google Custom Search API orqali rasm URL qaytaradi.
    GOOGLE_API_KEY va GOOGLE_CX .env da bo'lishi kerak.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return None
    try:
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "q": query,
            "searchType": "image",
            "num": 1,
            "safe": "active",
            "imgType": "photo",
            "imgSize": "large",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                GOOGLE_SEARCH_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("items", [])
                    if items:
                        return items[0].get("link")
    except Exception:
        pass
    return None


async def fetch_slide_images(slides: list, topic: str) -> list:
    """Har bir slayd uchun Google dan rasm topadi."""
    tasks = []
    for slide in slides:
        suggestion = slide.get("image_suggestion", "")
        query = f"{suggestion} {topic}" if suggestion else f"{slide.get('title', topic)} professional"
        tasks.append(search_image(query))

    urls = await asyncio.gather(*tasks, return_exceptions=True)

    for slide, url in zip(slides, urls):
        if isinstance(url, str):
            slide["image_url"] = url
        else:
            slide["image_url"] = None

    return slides


async def generate_presentation(
    topic: str,
    slides: int,
    language: str,
    style: str,
    color: str,
    output_type: str,
) -> dict | None:

    lang_instruction = LANG_MAP.get(language, "O'zbek tilida yoz")
    style_text = STYLE_MAP.get(style, "professional uslubda")
    color_text = COLOR_LABEL.get(color, "Ko'k")

    detail = (
        "Har bir slayd juda batafsil, keng qamrovli va chuqur bo'lsin. "
        "speaker_notes da to'liq nutq matni bo'lsin."
        if output_type == "premium"
        else "Har bir slayd professional, aniq va qisqa bo'lsin."
    )

    system_prompt = (
        "Sen professional presentation yaratuvchi AI assistantsan. "
        "Faqat valid JSON qaytarasan, boshqa hech narsa yozma."
    )

    user_prompt = f"""
{lang_instruction}.

Mavzu: {topic}
Slaydlar soni: {slides}
Uslub: {style_text}
Rang sxemasi: {color_text}

Talab: {detail}

Faqat quyidagi JSON formatda qaytargin:

{{
  "title": "Taqdimot sarlavhasi",
  "slides": [
    {{
      "number": 1,
      "title": "Slayd sarlavhasi",
      "content": "Asosiy kontent (2-4 gap)",
      "key_points": ["Nuqta 1", "Nuqta 2", "Nuqta 3"],
      "image_suggestion": "Rasm uchun qidiruv so'zi (inglizcha)",
      "speaker_notes": "Nutq matni"
    }}
  ]
}}
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    return {
                        "title": "Xatolik",
                        "slides": [{"number": 1, "title": "Groq API xato",
                                    "content": f"Status {resp.status}: {error_text[:300]}"}]
                    }

                data = await resp.json()
                content = data["choices"][0]["message"]["content"]

        cleaned = clean_json(content)

        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            result = {
                "title": topic,
                "slides": [{"number": 1, "title": "AI javobi", "content": content}],
            }

        # Google rasmlarni qo'shish
        if GOOGLE_API_KEY and GOOGLE_CX:
            result["slides"] = await fetch_slide_images(result.get("slides", []), topic)

        return result

    except asyncio.TimeoutError:
        return {
            "title": "Xatolik",
            "slides": [{"number": 1, "title": "Timeout", "content": "Groq API javob bermadi (60s). Qaytadan urining."}]
        }
    except Exception as e:
        return {
            "title": "Xatolik",
            "slides": [{"number": 1, "title": "Xato", "content": str(e)}]
        }


def format_presentation_text(data: dict, is_premium: bool = False) -> str:
    """Presentation dict ni HTML formatli matnga o'giradi."""
    title = data.get("title", "Taqdimot")
    slides = data.get("slides", [])

    lines = [f"🎨 <b>{title}</b>\n"]

    for slide in slides:
        num = slide.get("number", "")
        stitle = slide.get("title", "")
        content = slide.get("content", "")
        key_points = slide.get("key_points", [])
        speaker_notes = slide.get("speaker_notes", "")
        image_url = slide.get("image_url")

        lines.append(f"\n<b>━━━ Slayd {num}: {stitle} ━━━</b>")
        if content:
            lines.append(content)
        if key_points:
            lines.append("\n📌 <b>Asosiy fikrlar:</b>")
            for point in key_points:
                lines.append(f"  • {point}")
        if image_url:
            lines.append(f'\n🖼 <a href="{image_url}">Rasm ko\'rish</a>')
        if is_premium and speaker_notes:
            lines.append(f"\n🎤 <i>Nutq matni: {speaker_notes}</i>")

    return "\n".join(lines)
