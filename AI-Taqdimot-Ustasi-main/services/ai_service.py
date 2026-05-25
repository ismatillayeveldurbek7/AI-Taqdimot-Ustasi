
import random

DESIGNS = [
    "Modern Blue",
    "Premium Dark",
    "Minimal White",
    "Gradient Purple",
    "Business Clean",
    "Creative Neon",
    "Elegant Gold",
]

SLIDE_STRUCTURES = [
    "Kirish",
    "Asosiy tushuncha",
    "Muhim faktlar",
    "Amaliy qo'llanilishi",
    "Statistika va tahlil",
    "Afzalliklari",
    "Kamchiliklari",
    "Xulosa"
]

IMAGE_STYLES = [
    "professional illustration",
    "cinematic scene",
    "modern infographic",
    "business presentation style",
    "3D render",
    "high quality educational image",
]

async def generate_presentation(
    topic,
    slides,
    language,
    style,
    color,
    output_type,
):

    selected_design = random.choice(DESIGNS)

    generated_slides = []

    for i in range(1, slides + 1):

        section = SLIDE_STRUCTURES[(i - 1) % len(SLIDE_STRUCTURES)]

        paragraph = f"""
{topic} mavzusining {section.lower()} qismi.

Bu slaydda {topic} bo‘yicha muhim ma’lumotlar, zamonaviy yondashuvlar,
amaliy misollar va professional tushuntirishlar beriladi.

{topic} bugungi kunda ta’lim, texnologiya va biznes sohalarida keng
qo‘llanilmoqda. Ushbu mavzu zamonaviy rivojlanishning muhim qismlaridan biridir.
"""

        generated_slides.append({
            "number": i,
            "title": f"{section}: {topic}",
            "content": paragraph,
            "key_points": [
                f"{topic} asoslari",
                f"{topic} bo‘yicha professional ma’lumot",
                f"{topic} amaliy qo‘llanilishi",
                f"{topic} zamonaviy texnologiyalar bilan bog‘liqligi"
            ],
            "image_suggestion": f"{topic} {random.choice(IMAGE_STYLES)}",
            "speaker_notes": f"{topic} haqida professional tushuntirish.",
            "design": selected_design
        })

    return {
        "title": topic,
        "design": selected_design,
        "slides": generated_slides
    }

async def format_presentation_text(data):
    return data
