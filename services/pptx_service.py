import io
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ─── Color schemes ────────────────────────────────────────────────────────────

THEMES: dict[str, dict] = {
    "Blue": {
        "bg": RGBColor(0x1A, 0x37, 0x6C),
        "accent": RGBColor(0x4A, 0x90, 0xD9),
        "text": RGBColor(0xFF, 0xFF, 0xFF),
        "subtitle": RGBColor(0xCC, 0xDD, 0xFF),
        "slide_bg": RGBColor(0xF0, 0xF4, 0xFF),
        "slide_text": RGBColor(0x1A, 0x37, 0x6C),
    },
    "Black": {
        "bg": RGBColor(0x1C, 0x1C, 0x1C),
        "accent": RGBColor(0xE0, 0xA8, 0x00),
        "text": RGBColor(0xFF, 0xFF, 0xFF),
        "subtitle": RGBColor(0xCC, 0xCC, 0xCC),
        "slide_bg": RGBColor(0xF5, 0xF5, 0xF5),
        "slide_text": RGBColor(0x1C, 0x1C, 0x1C),
    },
    "White": {
        "bg": RGBColor(0xFF, 0xFF, 0xFF),
        "accent": RGBColor(0x2E, 0x86, 0xAB),
        "text": RGBColor(0x1C, 0x1C, 0x1C),
        "subtitle": RGBColor(0x55, 0x55, 0x55),
        "slide_bg": RGBColor(0xFF, 0xFF, 0xFF),
        "slide_text": RGBColor(0x1C, 0x1C, 0x1C),
    },
    "Green": {
        "bg": RGBColor(0x10, 0x47, 0x2F),
        "accent": RGBColor(0x2D, 0xB8, 0x6A),
        "text": RGBColor(0xFF, 0xFF, 0xFF),
        "subtitle": RGBColor(0xBB, 0xEE, 0xCC),
        "slide_bg": RGBColor(0xF0, 0xFD, 0xF4),
        "slide_text": RGBColor(0x10, 0x47, 0x2F),
    },
    "PremiumDark": {
        "bg": RGBColor(0x0D, 0x0D, 0x1A),
        "accent": RGBColor(0x9B, 0x59, 0xB6),
        "text": RGBColor(0xFF, 0xFF, 0xFF),
        "subtitle": RGBColor(0xCC, 0xAA, 0xFF),
        "slide_bg": RGBColor(0x12, 0x12, 0x24),
        "slide_text": RGBColor(0xEE, 0xEE, 0xFF),
    },
}


def _set_bg(slide, color: RGBColor) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_textbox(slide, text: str, left, top, width, height,
                 font_size=18, bold=False, color=None, align=PP_ALIGN.LEFT, wrap=True):
    txb = slide.shapes.add_textbox(left, top, width, height)
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    return txb


def _add_rect(slide, left, top, width, height, color: RGBColor):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def generate_pptx(data: dict, color_scheme: str = "Blue") -> bytes:
    """Generate a .pptx file from presentation data and return as bytes."""
    theme = THEMES.get(color_scheme, THEMES["Blue"])
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]  # Completely blank

    slides_data = data.get("slides", [])

    for idx, slide_data in enumerate(slides_data):
        slide = prs.slides.add_slide(blank_layout)
        is_title_slide = idx == 0

        W = prs.slide_width
        H = prs.slide_height

        if is_title_slide:
            # Full background
            _set_bg(slide, theme["bg"])
            # Accent bar at bottom
            _add_rect(slide, 0, H - Inches(0.8), W, Inches(0.8), theme["accent"])
            # Title
            _add_textbox(
                slide, slide_data.get("title", ""),
                Inches(1), Inches(2), W - Inches(2), Inches(1.5),
                font_size=40, bold=True, color=theme["text"], align=PP_ALIGN.CENTER
            )
            # Content as subtitle
            content = slide_data.get("content", "")
            _add_textbox(
                slide, content,
                Inches(1.5), Inches(3.8), W - Inches(3), Inches(1.2),
                font_size=20, color=theme["subtitle"], align=PP_ALIGN.CENTER
            )
            # Slide number bar
            _add_textbox(
                slide, f"1 / {len(slides_data)}",
                W - Inches(1.5), H - Inches(0.7), Inches(1.2), Inches(0.5),
                font_size=11, color=theme["text"], align=PP_ALIGN.RIGHT
            )
        else:
            # Slide background
            _set_bg(slide, theme["slide_bg"])
            # Header bar
            _add_rect(slide, 0, 0, W, Inches(1.1), theme["bg"])
            # Accent left strip
            _add_rect(slide, 0, 0, Inches(0.07), H, theme["accent"])
            # Title in header
            _add_textbox(
                slide, slide_data.get("title", ""),
                Inches(0.3), Inches(0.15), W - Inches(1.5), Inches(0.8),
                font_size=26, bold=True, color=theme["text"]
            )
            # Slide number in header
            _add_textbox(
                slide, f"{slide_data.get('number', idx+1)} / {len(slides_data)}",
                W - Inches(1.3), Inches(0.3), Inches(1.1), Inches(0.5),
                font_size=12, color=theme["subtitle"], align=PP_ALIGN.RIGHT
            )
            # Content area
            content = slide_data.get("content", "")
            _add_textbox(
                slide, content,
                Inches(0.4), Inches(1.3), W - Inches(0.8), Inches(2.2),
                font_size=16, color=theme["slide_text"]
            )
            # Key points
            key_points = slide_data.get("key_points", [])
            if key_points:
                y_start = Inches(3.7)
                _add_textbox(
                    slide, "● Kalit fikrlar",
                    Inches(0.4), y_start, Inches(3), Inches(0.4),
                    font_size=14, bold=True, color=theme["accent"]
                )
                for i, kp in enumerate(key_points[:4]):
                    _add_textbox(
                        slide, f"  ✓  {kp}",
                        Inches(0.4), y_start + Inches(0.45 * (i + 1)), W - Inches(1), Inches(0.4),
                        font_size=13, color=theme["slide_text"]
                    )
            # Speaker notes
            notes_text = slide_data.get("speaker_notes", "")
            if notes_text:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = notes_text

    # Save to bytes
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.read()
