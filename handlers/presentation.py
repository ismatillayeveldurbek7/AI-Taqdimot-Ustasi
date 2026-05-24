import io
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message, CallbackQuery
from sqlalchemy import select

from config import PRICE_TEXT_PRESENTATION, PRICE_PPTX_PRESENTATION, PRICE_PREMIUM_PRESENTATION
from database import AsyncSessionLocal
from models import Presentation, User
from keyboards import (
    color_kb, confirm_presentation_kb, language_kb,
    main_menu_kb, output_type_kb, style_kb,
)
from services.ai_service import format_presentation_text, generate_presentation
from services.pptx_service import generate_pptx
from states import PresentationStates
from utils.logger import logger
from utils.validators import is_spam, validate_slides_count, validate_topic

router = Router()

PRICE_MAP = {
    "text": PRICE_TEXT_PRESENTATION,
    "pptx": PRICE_PPTX_PRESENTATION,
    "premium": PRICE_PREMIUM_PRESENTATION,
}

LANGUAGE_LABEL = {"uzbek": "🇺🇿 O'zbek", "russian": "🇷🇺 Русский", "english": "🇬🇧 English"}
STYLE_LABEL = {
    "Academic": "🎓 Akademik", "Business": "💼 Biznes",
    "Creative": "🎨 Ijodiy", "Educational": "📚 Ta'limiy", "Minimal": "⬜ Minimal",
}
COLOR_LABEL = {
    "Blue": "🔵 Ko'k", "Black": "⚫ Qora", "White": "⚪ Oq",
    "Green": "🟢 Yashil", "PremiumDark": "🌑 Premium qora",
}
OUTPUT_LABEL = {"text": "📝 Faqat matn", "pptx": "📊 PPTX fayl", "premium": "⭐ Premium"}


# ─── 1-qadam: Mavzu ──────────────────────────────────────────────────────────

@router.message(F.text == "🎨 Taqdimot yaratish")
async def start_presentation(message: Message, state: FSMContext) -> None:
    if is_spam(message.from_user.id):
        await message.answer("⚠️ Iltimos, biroz kuting.")
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalars().first()
        if not user:
            await message.answer("Iltimos /start bosing.")
            return

    if user.is_blocked:
        await message.answer("❌ Siz bloklangansiz.")
        return

    # Oldingi stateni tozalash
    await state.clear()
    await state.set_state(PresentationStates.topic)

    await message.answer(
        "🎨 <b>Taqdimot yaratish</b>\n\n"
        "<b>1-qadam: Mavzu</b>\n\n"
        "Taqdimotingiz mavzusini kiriting:\n\n"
        "<i>Misol: Sun'iy intellekt va kelajak, Iqlim o'zgarishi, Marketing strategiyasi...</i>\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
    )


# ─── 2-qadam: Slaydlar soni ──────────────────────────────────────────────────

@router.message(StateFilter(PresentationStates.topic))
async def got_topic(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("⚠️ Iltimos matn kiriting.")
        return
    if not validate_topic(message.text):
        await message.answer("⚠️ Mavzu 3-300 ta belgi bo'lishi kerak. Qaytadan kiriting:")
        return

    await state.update_data(topic=message.text.strip())
    await state.set_state(PresentationStates.slides_count)
    await message.answer(
        "🎨 <b>Taqdimot yaratish</b>\n\n"
        "<b>2-qadam: Slaydlar soni</b>\n\n"
        "Nechta slayd kerak? (3 dan 20 gacha)\n\n"
        "<i>Maslahat: Ko'pchilik taqdimotlar 8-12 ta slayddan iborat</i>",
    )


# ─── 3-qadam: Til ────────────────────────────────────────────────────────────

@router.message(StateFilter(PresentationStates.slides_count))
async def got_slides(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("⚠️ Son kiriting.")
        return
    n = validate_slides_count(message.text)
    if n is None:
        await message.answer("⚠️ 3 dan 20 gacha son kiriting:")
        return

    await state.update_data(slides_count=n)
    await state.set_state(PresentationStates.language)
    await message.answer(
        "🎨 <b>Taqdimot yaratish</b>\n\n"
        "<b>3-qadam: Til</b>\n\n"
        "Taqdimot tilini tanlang:",
        reply_markup=language_kb(),
    )


# ─── 4-qadam: Uslub ──────────────────────────────────────────────────────────

@router.callback_query(StateFilter(PresentationStates.language), F.data.startswith("lang:"))
async def got_language(callback: CallbackQuery, state: FSMContext) -> None:
    lang = callback.data.split(":")[1]
    await state.update_data(language=lang)
    await state.set_state(PresentationStates.style)
    await callback.message.edit_text(
        "🎨 <b>Taqdimot yaratish</b>\n\n"
        "<b>4-qadam: Uslub</b>\n\n"
        "Taqdimot uslubini tanlang:",
        reply_markup=style_kb(),
    )
    await callback.answer()


# ─── 5-qadam: Rang ───────────────────────────────────────────────────────────

@router.callback_query(StateFilter(PresentationStates.style), F.data.startswith("style:"))
async def got_style(callback: CallbackQuery, state: FSMContext) -> None:
    style = callback.data.split(":")[1]
    await state.update_data(style=style)
    await state.set_state(PresentationStates.color)
    await callback.message.edit_text(
        "🎨 <b>Taqdimot yaratish</b>\n\n"
        "<b>5-qadam: Rang sxemasi</b>\n\n"
        "Taqdimot rangini tanlang:",
        reply_markup=color_kb(),
    )
    await callback.answer()


# ─── 6-qadam: Chiqish turi ───────────────────────────────────────────────────

@router.callback_query(StateFilter(PresentationStates.color), F.data.startswith("color:"))
async def got_color(callback: CallbackQuery, state: FSMContext) -> None:
    color = callback.data.split(":")[1]
    await state.update_data(color=color)
    await state.set_state(PresentationStates.output_type)
    await callback.message.edit_text(
        "🎨 <b>Taqdimot yaratish</b>\n\n"
        "<b>6-qadam: Chiqish turi</b>\n\n"
        "Taqdimot turini tanlang:",
        reply_markup=output_type_kb(),
    )
    await callback.answer()


# ─── 7-qadam: Tasdiqlash ─────────────────────────────────────────────────────

@router.callback_query(StateFilter(PresentationStates.output_type), F.data.startswith("output:"))
async def got_output(callback: CallbackQuery, state: FSMContext) -> None:
    output_type = callback.data.split(":")[1]
    await state.update_data(output_type=output_type)
    await state.set_state(PresentationStates.confirming)

    data = await state.get_data()
    coins_needed = PRICE_MAP[output_type]

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalars().first()

    balance = user.balance if user else 0
    balance_ok = balance >= coins_needed

    if balance_ok:
        balance_str = f"✅ Yetarli ({balance} coin)"
    else:
        balance_str = f"❌ Yetarli emas ({balance} coin, kerak: {coins_needed})"

    summary = (
        f"🎨 <b>Taqdimot yaratish — Tasdiqlash</b>\n\n"
        f"📋 <b>Mavzu:</b> {data['topic']}\n"
        f"📊 <b>Slaydlar:</b> {data['slides_count']} ta\n"
        f"🌐 <b>Til:</b> {LANGUAGE_LABEL.get(data['language'], data['language'])}\n"
        f"🎨 <b>Uslub:</b> {STYLE_LABEL.get(data['style'], data['style'])}\n"
        f"🎨 <b>Rang:</b> {COLOR_LABEL.get(data['color'], data['color'])}\n"
        f"📁 <b>Turi:</b> {OUTPUT_LABEL.get(output_type, output_type)}\n\n"
        f"💎 <b>Narxi:</b> {coins_needed} coin\n"
        f"👛 <b>Balans:</b> {balance_str}\n"
    )

    if not balance_ok:
        summary += "\n\n⚠️ <b>Balansingiz yetarli emas!</b>\n💰 Coin sotib olish uchun asosiy menyuga qayting."
        await callback.message.edit_text(summary)
        await state.clear()
    else:
        await callback.message.edit_text(summary, reply_markup=confirm_presentation_kb())

    await callback.answer()


# ─── Generatsiya ─────────────────────────────────────────────────────────────

@router.callback_query(StateFilter(PresentationStates.confirming), F.data == "confirm_pres")
async def confirm_and_generate(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    output_type = data.get("output_type")
    if not output_type:
        await callback.message.edit_text("❌ Xatolik. Qaytadan boshlang.")
        await state.clear()
        await callback.answer()
        return

    coins_needed = PRICE_MAP[output_type]

    await callback.message.edit_text(
        "⏳ <b>Taqdimot yaratilmoqda...</b>\n\n"
        "🤖 AI ishlamoqda, biroz kuting...\n"
        "⚡ Bu 15-45 soniya vaqt olishi mumkin.",
    )
    await callback.answer()

    # Balansni tekshirish va ayirish
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalars().first()
        if not user or user.balance < coins_needed:
            await callback.message.edit_text("❌ Balans yetarli emas.")
            await state.clear()
            return

        user.balance -= coins_needed
        await session.commit()
        user_id = user.id

    # AI generatsiya
    presentation_data = await generate_presentation(
        topic=data["topic"],
        slides=data["slides_count"],
        language=data["language"],
        style=data["style"],
        color=data["color"],
        output_type=output_type,
    )

    if not presentation_data:
        # Coinlarni qaytarish
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == callback.from_user.id)
            )
            user = result.scalars().first()
            if user:
                user.balance += coins_needed
                await session.commit()
        await callback.message.answer(
            "❌ <b>Xatolik yuz berdi!</b>\n\n"
            "AI javob bermadi. Coinlaringiz qaytarildi.\n"
            "Iltimos, qaytadan urinib ko'ring.",
        )
        await state.clear()
        return

    # Taqdimotni bazaga saqlash
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalars().first()

        pres_record = Presentation(
            user_id=user.id,
            topic=data["topic"],
            slides_count=data["slides_count"],
            language=data["language"],
            style=data["style"],
            color=data["color"],
            output_type=output_type,
            coins_spent=coins_needed,
        )
        session.add(pres_record)
        await session.commit()
        await session.refresh(pres_record)
        new_balance = user.balance

    # Natijani yuborish
    if output_type in ("text", "premium"):
        is_premium = output_type == "premium"
        text_content = format_presentation_text(presentation_data, is_premium=is_premium)
        chunks = [text_content[i:i+4000] for i in range(0, len(text_content), 4000)]
        for chunk in chunks:
            await callback.message.answer(chunk)
    else:
        # PPTX
        try:
            pptx_bytes = generate_pptx(presentation_data, color_scheme=data["color"])
            safe_name = "".join(c for c in data["topic"][:30] if c.isalnum() or c in " _-").strip()
            file_name = f"{safe_name or 'taqdimot'}.pptx"
            doc = BufferedInputFile(pptx_bytes, filename=file_name)
            sent = await callback.message.answer_document(
                doc,
                caption=(
                    f"📊 <b>{presentation_data.get('title', data['topic'])}</b>\n\n"
                    f"✅ Taqdimot tayyor! {data['slides_count']} ta slayd."
                ),
            )
            # file_id saqlash
            async with AsyncSessionLocal() as session:
                pres = await session.get(Presentation, pres_record.id)
                if pres and sent.document:
                    pres.file_id = sent.document.file_id
                    await session.commit()
        except Exception as e:
            logger.error(f"PPTX generation error: {e}")
            await callback.message.answer("⚠️ PPTX yaratishda xato. Matn versiyasini yuboramiz:")
            text_content = format_presentation_text(presentation_data)
            await callback.message.answer(text_content[:4000])

    await callback.message.answer(
        f"✅ <b>Taqdimot tayyor!</b>\n\n"
        f"💎 Sarflandi: {coins_needed} coin\n"
        f"👛 Qolgan balans: {new_balance} coin\n\n"
        f"🎨 Yangi taqdimot yaratish uchun tugmani bosing!",
        reply_markup=main_menu_kb(),
    )
    await state.clear()


# ─── Bekor qilish ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cancel_pres")
async def cancel_presentation(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "❌ Taqdimot yaratish bekor qilindi.\n\n"
        "Asosiy menyuga qaytish uchun pastdagi tugmalardan foydalaning."
    )
    await callback.answer()
