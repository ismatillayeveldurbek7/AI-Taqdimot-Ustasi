from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, get_setting
from models import User, Presentation
from keyboards import main_menu_kb
from utils.logger import logger
from utils.validators import is_spam

router = Router()


async def get_or_create_user(session: AsyncSession, message: Message) -> User:
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalars().first()
    if not user:
        user = User(
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
            balance=0,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"New user registered: {user.telegram_id} ({user.full_name})")
    else:
        user.full_name = message.from_user.full_name
        user.username = message.from_user.username
        await session.commit()
    return user


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    # Agar state bo'lsa, tozalab tashlash
    await state.clear()

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message)
        if user.is_blocked:
            await message.answer("❌ Siz bloklangansiz. Murojaat: @admin")
            return

    await message.answer(
        f"👋 Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
        "🤖 <b>AI Taqdimot Generator</b> botiga xush kelibsiz!\n\n"
        "✨ Bu bot yordamida professional AI taqdimotlar yaratishingiz mumkin.\n"
        "💰 Avval coin sotib oling, keyin taqdimot yarating!\n\n"
        "Quyidagi menyudan tanlang:",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
    else:
        await message.answer("Hozir hech qanday jarayon yo'q.", reply_markup=main_menu_kb())


@router.message(F.text == "👛 Balansim")
async def balance_handler(message: Message) -> None:
    if is_spam(message.from_user.id):
        await message.answer("⚠️ Iltimos, biroz kuting.")
        return
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalars().first()
        if not user:
            await cmd_start.__wrapped__(message) if hasattr(cmd_start, '__wrapped__') else await message.answer("Iltimos /start bosing.")
            return

    await message.answer(
        f"👛 <b>Balansingiz</b>\n\n"
        f"🪙 Coinlar: <b>{user.balance} coin</b>\n\n"
        f"💰 Coin sotib olish uchun <b>«💰 Coin sotib olish»</b> tugmasini bosing.",
    )


@router.message(F.text == "📂 Taqdimotlarim")
async def my_presentations(message: Message) -> None:
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

        pres_result = await session.execute(
            select(Presentation)
            .where(Presentation.user_id == user.id)
            .order_by(Presentation.created_at.desc())
            .limit(10)
        )
        presentations = pres_result.scalars().all()

    if not presentations:
        await message.answer(
            "📂 <b>Taqdimotlarim</b>\n\n"
            "Hozircha hech qanday taqdimot yaratmadingiz.\n"
            "🎨 Yangi taqdimot yaratish uchun «🎨 Taqdimot yaratish» tugmasini bosing.",
        )
        return

    lines = ["📂 <b>So'nggi 10 ta taqdimotingiz:</b>\n"]
    for i, p in enumerate(presentations, 1):
        type_emoji = {"text": "📝", "pptx": "📊", "premium": "⭐"}.get(p.output_type, "📄")
        date_str = p.created_at.strftime("%d.%m.%Y %H:%M")
        lines.append(
            f"{i}. {type_emoji} <b>{p.topic[:40]}</b>\n"
            f"   🗂 {p.slides_count} slayd • {p.coins_spent} coin • {date_str}"
        )

    await message.answer("\n".join(lines))


@router.message(F.text == "ℹ️ Bot haqida")
async def about_bot(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        about_text = await get_setting(session, "about_text", "AI Taqdimot Generator boti.")

    await message.answer(
        f"ℹ️ <b>Bot haqida</b>\n\n{about_text}\n\n"
        "🤖 <b>Xususiyatlar:</b>\n"
        "• 🎨 AI yordamida professional taqdimotlar\n"
        "• 📊 PPTX format (PowerPoint)\n"
        "• 🌐 3 tilda: O'zbek, Rus, Ingliz\n"
        "• 🎨 5 uslub va 5 rang sxemasi\n"
        "• ⚡ Tez va sifatli natija\n\n"
        "💡 <b>Narxlar:</b>\n"
        "• 📝 Matn taqdimoti: 5 coin\n"
        "• 📊 PPTX fayl: 10 coin\n"
        "• ⭐ Premium batafsil: 15 coin",
    )


@router.message(F.text == "📞 Aloqa")
async def support_handler(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        support = await get_setting(session, "support_username", "@admin")

    await message.answer(
        f"📞 <b>Aloqa</b>\n\n"
        f"Muammo yoki savollaringiz bo'lsa, adminga murojaat qiling:\n\n"
        f"👤 Admin: {support}\n\n"
        f"⏰ Ish vaqti: Har kuni 9:00 - 22:00",
    )


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("🏠 Asosiy menyu:", reply_markup=main_menu_kb())
    await callback.answer()
