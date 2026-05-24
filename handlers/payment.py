from aiogram import Bot, Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from config import ADMIN_IDS
from database import AsyncSessionLocal, get_setting
from models import CoinPackage, Payment, User
from keyboards import admin_payment_kb, main_menu_kb, packages_kb, paid_kb
from services.payment_service import approve_payment, reject_payment, create_payment
from states import PaymentStates
from utils.logger import logger
from utils.validators import is_spam

router = Router()


# ─── Coin sotib olish menyusi ─────────────────────────────────────────────────

@router.message(F.text == "💰 Coin sotib olish")
async def buy_coins_menu(message: Message, state: FSMContext) -> None:
    if is_spam(message.from_user.id):
        await message.answer("⚠️ Iltimos, biroz kuting.")
        return

    # Oldingi stateni tozalash
    await state.clear()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CoinPackage).where(CoinPackage.is_active == True).order_by(CoinPackage.coins)
        )
        packages = result.scalars().all()

    if not packages:
        await message.answer(
            "❌ Hozirda mavjud paketlar yo'q.\n"
            "Keyinroq urinib ko'ring yoki admin bilan bog'laning."
        )
        return

    await state.set_state(PaymentStates.choosing_package)
    await message.answer(
        "💰 <b>Coin sotib olish</b>\n\n"
        "Quyidagi paketlardan birini tanlang:",
        reply_markup=packages_kb(packages),
    )


# ─── Paket tanlandi ───────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("buy_package:"))
async def package_selected(callback: CallbackQuery, state: FSMContext) -> None:
    pkg_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CoinPackage).where(CoinPackage.id == pkg_id, CoinPackage.is_active == True)
        )
        package = result.scalars().first()
        if not package:
            await callback.answer("❌ Bu paket mavjud emas.", show_alert=True)
            return

        card_number = await get_setting(session, "card_number", "0000 0000 0000 0000")
        card_owner = await get_setting(session, "card_owner", "Bot Admin")

    await state.update_data(package_id=pkg_id)
    await state.set_state(PaymentStates.waiting_receipt)

    await callback.message.edit_text(
        f"💳 <b>To'lov ma'lumotlari</b>\n\n"
        f"📦 Paket: <b>{package.coins} coin</b>\n"
        f"💰 Summa: <b>{package.price_uzs:,} so'm</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏦 Karta raqami:\n"
        f"<code>{card_number}</code>\n\n"
        f"👤 Karta egasi:\n"
        f"<b>{card_owner}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 <b>Ko'rsatma:</b>\n"
        f"1. Yuqoridagi karta raqamiga <b>{package.price_uzs:,} so'm</b> o'tkazing\n"
        f"2. «✅ To'ladim» tugmasini bosing\n"
        f"3. To'lov chekining rasmini yuboring\n"
        f"4. Admin tasdiqlashini kuting\n\n"
        f"⏱ Tasdiqlash vaqti: 5-30 daqiqa",
        reply_markup=paid_kb(pkg_id),
    )
    await callback.answer()


# ─── "To'ladim" tugmasi ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("i_paid:"))
async def i_paid(callback: CallbackQuery, state: FSMContext) -> None:
    # State'ni waiting_receipt ga o'rnatish
    data = await state.get_data()
    if not data.get("package_id"):
        pkg_id = int(callback.data.split(":")[1])
        await state.update_data(package_id=pkg_id)
    await state.set_state(PaymentStates.waiting_receipt)

    await callback.message.edit_text(
        "📸 <b>Chek rasmini yuboring</b>\n\n"
        "To'lov chekining rasmini (screenshot yoki fotosuratini) yuboring.\n\n"
        "⚠️ Eslatma: Cheksiz to'lovlar tasdiqlanmaydi.",
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_payment")
async def cancel_payment_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ To'lov bekor qilindi.")
    await callback.answer()


# ─── Chek rasmi qabul qilindi ─────────────────────────────────────────────────

@router.message(StateFilter(PaymentStates.waiting_receipt), F.photo)
async def receipt_received(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    pkg_id = data.get("package_id")

    if not pkg_id:
        await message.answer(
            "⚠️ Xatolik yuz berdi. Iltimos qaytadan boshlang.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        return

    photo_file_id = message.photo[-1].file_id

    async with AsyncSessionLocal() as session:
        user_res = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = user_res.scalars().first()
        if not user:
            await state.clear()
            return

        pkg_res = await session.execute(
            select(CoinPackage).where(CoinPackage.id == pkg_id)
        )
        package = pkg_res.scalars().first()
        if not package:
            await message.answer("❌ Paket topilmadi.")
            await state.clear()
            return

        payment = await create_payment(session, user, package)
        payment.receipt_file_id = photo_file_id
        await session.commit()

        admin_text = (
            f"💳 <b>Yangi to'lov so'rovi #{payment.id}</b>\n\n"
            f"👤 Foydalanuvchi: <a href='tg://user?id={user.telegram_id}'>{user.full_name}</a>\n"
            f"🆔 ID: <code>{user.telegram_id}</code>\n"
            f"📦 Paket: {package.coins} coin\n"
            f"💰 Summa: {package.price_uzs:,} so'm\n"
            f"📅 Vaqt: {payment.created_at.strftime('%d.%m.%Y %H:%M')}"
        )

        for admin_id in ADMIN_IDS:
            try:
                sent = await bot.send_photo(
                    chat_id=admin_id,
                    photo=photo_file_id,
                    caption=admin_text,
                    reply_markup=admin_payment_kb(payment.id),
                )
                if payment.admin_message_id is None:
                    payment.admin_message_id = sent.message_id
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

        await session.commit()

    await state.clear()
    await message.answer(
        "✅ <b>Chek qabul qilindi!</b>\n\n"
        "Admin sizning to'lovingizni tekshiradi.\n"
        "⏱ Tasdiqlash vaqti: 5-30 daqiqa\n\n"
        "Tasdiqlangach sizga xabar beriladi! 🎉",
        reply_markup=main_menu_kb(),
    )


@router.message(StateFilter(PaymentStates.waiting_receipt))
async def receipt_not_photo(message: Message) -> None:
    await message.answer(
        "⚠️ Iltimos, faqat <b>rasm (screenshot)</b> yuboring.\n"
        "Matn yoki fayl qabul qilinmaydi.",
    )


# ─── Admin: Tasdiqlash / Rad etish ───────────────────────────────────────────

@router.callback_query(F.data.startswith("approve_pay:"))
async def approve_pay(callback: CallbackQuery, bot: Bot) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    pay_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Payment).where(Payment.id == pay_id))
        payment = result.scalars().first()
        if not payment:
            await callback.answer("❌ To'lov topilmadi.", show_alert=True)
            return

        user = await session.get(User, payment.user_id)
        success = await approve_payment(session, payment)

        if not success:
            await callback.answer("⚠️ Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        new_balance = user.balance if user else "?"

    try:
        await callback.message.edit_caption(
            (callback.message.caption or "") + f"\n\n✅ <b>TASDIQLANDI</b> — @{callback.from_user.username}",
        )
    except Exception:
        pass

    if user:
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    f"✅ <b>To'lovingiz tasdiqlandi!</b>\n\n"
                    f"🪙 <b>{payment.coins} coin</b> balansingizga qo'shildi.\n"
                    f"💎 Joriy balans: <b>{new_balance} coin</b>\n\n"
                    f"🎨 Endi taqdimot yaratishingiz mumkin!"
                ),
                reply_markup=main_menu_kb(),
            )
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")

    await callback.answer("✅ Tasdiqlandi!")


@router.callback_query(F.data.startswith("reject_pay:"))
async def reject_pay(callback: CallbackQuery, bot: Bot) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    pay_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Payment).where(Payment.id == pay_id))
        payment = result.scalars().first()
        if not payment:
            await callback.answer("❌ To'lov topilmadi.", show_alert=True)
            return

        user = await session.get(User, payment.user_id)
        success = await reject_payment(session, payment)

        if not success:
            await callback.answer("⚠️ Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

    try:
        await callback.message.edit_caption(
            (callback.message.caption or "") + f"\n\n❌ <b>RAD ETILDI</b> — @{callback.from_user.username}",
        )
    except Exception:
        pass

    if user:
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    "❌ <b>To'lovingiz rad etildi.</b>\n\n"
                    "Mumkin bo'lgan sabablar:\n"
                    "• Noto'g'ri summa o'tkazilgan\n"
                    "• Chek rasmi aniq emas\n"
                    "• Noto'g'ri karta\n\n"
                    "📞 Muammo bo'lsa admin bilan bog'laning."
                ),
                reply_markup=main_menu_kb(),
            )
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")

    await callback.answer("❌ Rad etildi!")
