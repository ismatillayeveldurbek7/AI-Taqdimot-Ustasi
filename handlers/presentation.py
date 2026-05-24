import io
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


# ─── Step 1: Topic ────────────────────────────────────────────────────────────

@router.message(F.text == "🎨 Taqdimot yaratish")
async def start_presentation(message: Message, state: FSMContext) -> None:
    if is_spam(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalars().first()
        if not user:
            return

    if user.is_blocked:
        await message.answer("❌ Siz bloklangansiz.")
        return

    await state.set_state(PresentationStates.topic)
    await message.answer(
        "🎨 <b>Taqdimot yaratish</b>\n\n"
        "<b>1-qadam: Mavzu</b>\n\n"
        "Taqdimotingiz mavzusini kiriting:\n\n"
        "<i>Misol: Sun'iy intellekt va kelajak, Iqlim o'zgarishi, Marketing strategiyasi...</i>\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )


# ─── Step 2: Slide count ──────────────────────────────────────────────────────

@router.message(PresentationStates.topic)
async def got_topic(message: Message, state: FSMContext) -> None:
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
        parse_mode="HTML",
    )


# ─── Step 3: Language ─────────────────────────────────────────────────────────

@router.message(PresentationStates.slides_count)
async def got_slides(message: Message, state: FSMContext) -> None:
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
        parse_mode="HTML",
    )


# ─── Step 4: Style ────────────────────────────────────────────────────────────

@router.callback_query(PresentationStates.language, F.data.startswith("lang:"))
async def got_language(callback: CallbackQuery, state: FSMContext) -> None:
    lang = callback.data.split(":")[1]
    await state.update_data(language=lang)
    await state.set_state(PresentationStates.style)
    await callback.message.edit_text(
        "🎨 <b>Taqdimot yaratish</b>\n\n"
        "<b>4-qadam: Uslub</b>\n\n"
        "Taqdimot uslubini tanlang:",
        reply_markup=style_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Step 5: Color ────────────────────────────────────────────────────────────

@router.callback_query(PresentationStates.style, F.data.startswith("style:"))
async def got_style(callback: CallbackQuery, state: FSMContext) -> None:
    style = callback.data.split(":")[1]
    await state.update_data(style=style)
    await state.set_state(PresentationStates.color)
    await callback.message.edit_text(
        "🎨 <b>Taqdimot yaratish</b>\n\n"
        "<b>5-qadam: Rang sxemasi</b>\n\n"
        "Taqdimot rangini tanlang:",
        reply_markup=color_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Step 6: Output type ──────────────────────────────────────────────────────

@router.callback_query(PresentationStates.color, F.data.startswith("color:"))
async def got_color(callback: CallbackQuery, state: FSMContext) -> None:
    color = callback.data.split(":")[1]
    await state.update_data(color=color)
    await state.set_state(PresentationStates.output_type)
    await callback.message.edit_text(
        "🎨 <b>Taqdimot yaratish</b>\n\n"
        "<b>6-qadam: Chiqish turi</b>\n\n"
        "Taqdimot turini tanlang:",
        reply_markup=output_type_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Step 7: Confirm ──────────────────────────────────────────────────────────

@router.callback_query(PresentationStates.output_type, F.data.startswith("output:"))
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

    balance_ok = user and user.balance >= coins_needed
    balance_str = f"✅ Yetarli ({user.balance} coin)" if balance_ok else f"❌ Yetarli emas ({user.balance if user else 0} coin)"

    summary = (
        f"🎨 <b>Taqdimot yaratish — Tasdiqlash</b>\n\n"
        f"📋 <b>Mavzu:</b> {data['topic']}\n"
        f"📊 <b>Slaydlar:</b> {data['slides_count']} ta\n"
        f"🌐 <b>Til:</b> {LANGUAGE_LABEL[data['language']]}\n"
        f"🎨 <b>Uslub:</b> {STYLE_LABEL[data['style']]}\n"
        f"🎨 <b>Rang:</b> {COLOR_LABEL[data['color']]}\n"
        f"📁 <b>Turi:</b> {OUTPUT_LABEL[output_type]}\n\n"
        f"💎 <b>Narxi:</b> {coins_needed} coin\n"
        f"👛 <b>Balans:</b> {balance_str}\n"
    )

    if not balance_ok:
        summary += "\n\n⚠️ <b>Balansingiz yetarli emas!</b>\n💰 Coin sotib olish uchun asosiy menyuga qayting."

    await callback.message.edit_text(
        summary,
        reply_markup=confirm_presentation_kb() if balance_ok else None,
        parse_mode="HTML",
    )
    if not balance_ok:
        await state.clear()
    await callback.answer()


# ─── Generate ─────────────────────────────────────────────────────────────────

@router.callback_query(PresentationStates.confirming, F.data == "confirm_pres")
async def confirm_and_generate(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    output_type = data["output_type"]
    coins_needed = PRICE_MAP[output_type]

    await callback.message.edit_text(
        "⏳ <b>Taqdimot yaratilmoqda...</b>\n\n"
        "🤖 AI ishlamoqda, biroz kuting...\n"
        "⚡ Bu 15-45 soniya vaqt olishi mumkin.",
        parse_mode="HTML",
    )
    await callback.answer()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalars().first()
        if not user or user.balance < coins_needed:
            await callback.message.edit_text("❌ Balans yetarli emas.")
            await state.clear()
            return

        # Deduct coins
        user.balance -= coins_needed
        await session.commit()

    # Call AI
    presentation_data = await generate_presentation(
        topic=data["topic"],
        slides=data["slides_count"],
        language=data["language"],
        style=data["style"],
        color=data["color"],
        output_type=output_type,
    )

    if not presentation_data:
        # Refund on failure
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
            parse_mode="HTML",
        )
        await state.clear()
        return

    # Save presentation record
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

    # ── Send result ───────────────────────────────────────────────────────────
    if output_type in ("text", "premium"):
        is_premium = output_type == "premium"
        text_content = format_presentation_text(presentation_data, is_premium=is_premium)
        # Telegram message limit: 4096 chars
        chunks = [text_content[i:i+4000] for i in range(0, len(text_content), 4000)]
        for chunk in chunks:
            await callback.message.answer(chunk, parse_mode="HTML")
    else:
        # PPTX
        try:
            pptx_bytes = generate_pptx(presentation_data, color_scheme=data["color"])
            file_name = f"{data['topic'][:30].replace(' ', '_')}.pptx"
            doc = BufferedInputFile(pptx_bytes, filename=file_name)
            sent = await callback.message.answer_document(
                doc,
                caption=f"📊 <b>{presentation_data.get('title', data['topic'])}</b>\n\n"
                        f"✅ Taqdimot tayyor! {data['slides_count']} ta slayd.",
                parse_mode="HTML",
            )
            # Save file_id
            async with AsyncSessionLocal() as session:
                pres = await session.get(Presentation, pres_record.id)
                if pres and sent.document:
                    pres.file_id = sent.document.file_id
                    await session.commit()
        except Exception as e:
            logger.error(f"PPTX generation error: {e}")
            await callback.message.answer(
                "⚠️ PPTX yaratishda xato. Matn versiyasini yuboramiz:\n",
                parse_mode="HTML",
            )
            text_content = format_presentation_text(presentation_data)
            await callback.message.answer(text_content[:4000], parse_mode="HTML")

    await callback.message.answer(
        f"✅ <b>Taqdimot tayyor!</b>\n\n"
        f"💎 Sarflandi: {coins_needed} coin\n"
        f"👛 Qolgan balans: {new_balance} coin\n\n"
        f"🎨 Yangi taqdimot yaratish uchun tugmani bosing!",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )
    await state.clear()


# ─── Cancel ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cancel_pres")
async def cancel_presentation(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Taqdimot yaratish bekor qilindi.")
    await callback.answer()


@router.message(F.text == "/cancel")
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
    else:
        await message.answer("Hech narsa bekor qilish uchun yo'q.", reply_markup=main_menu_kb())
