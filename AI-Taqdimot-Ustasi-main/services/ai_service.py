
import json
import aiohttp

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

async def generate_presentation(
    topic,
    slides,
    language,
    style,
    color,
    output_type,
):

    headers = {
        "Authorization": "Bearer YOUR_GROQ_API_KEY",
        "Content-Type": "application/json"
    }

    prompt = f"""
Create a professional PowerPoint presentation.

Topic: {topic}

Slides count: {slides}

Requirements:
- professional text
- educational structure
- premium slide titles
- image suggestions
- detailed content
- modern presentation style

Return ONLY valid JSON.

Format:

{{
  "title": "Presentation title",
  "slides": [
    {{
      "number": 1,
      "title": "Slide title",
      "content": "Slide content",
      "key_points": ["Point 1", "Point 2"],
      "image_suggestion": "Professional image idea",
      "speaker_notes": "Speaker notes"
    }}
  ]
}}
"""

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7
    }

    try:

        async with aiohttp.ClientSession() as session:
            async with session.post(
                GROQ_API_URL,
                headers=headers,
                json=payload
            ) as response:

                data = await response.json()

                content = data["choices"][0]["message"]["content"]

                try:
                    parsed = json.loads(content)
                    return parsed

                except:
                    return {
                        "title": topic,
                        "slides": [
                            {
                                "number": 1,
                                "title": "AI Response",
                                "content": content
                            }
                        ]
                    }

    except Exception as e:
        return {
            "title": "Error",
            "slides": [
                {
                    "number": 1,
                    "title": "Groq Error",
                    "content": str(e)
                }
            ]
        }

async def format_presentation_text(data):
    return data
