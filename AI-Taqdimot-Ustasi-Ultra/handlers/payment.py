"""
Payment handler — to'lov oqimi (OpenAI versiyasi)

Oqim:
  1. Foydalanuvchi paket tanlaydi → karta ma'lumotlari ko'rinadi
  2. Foydalanuvchi «To'ladim» tugmasini bosadi → chek rasmini yuboradi
  3. Admin chek + [✅ Tasdiqlash | ❌ Rad etish] tugmalarini ko'radi
  4a. Tasdiqlash → chek mesaji ✅ badge bilan yangilanadi
                 → foydalanuvchiga coin qo'shilgani haqida xabar
                 → barcha adminlarga xabardorlik
  4b. Rad etish  → admin ixtiyoriy qayd yozadi (yoki qaydsiz rad etadi)
                 → chek mesaji ❌ badge + sabab bilan yangilanadi
                 → foydalanuvchiga sabab ko'rsatilgan xabar
                 → barcha adminlarga xabardorlik
"""

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from config import ADMIN_IDS
from database import AsyncSessionLocal, get_setting
from models import CoinPackage, Payment, User
from keyboards import (
    admin_payment_kb, main_menu_kb, packages_kb,
    paid_kb, reject_reason_kb,
)
from services.payment_service import approve_payment, reject_payment, create_payment
from states import PaymentStates, RejectPaymentStates
from utils.logger import logger
from utils.validators import is_spam

router = Router()


# ──────────────────────────────────────────────────────────────────────────────
# 1. Paketlar ro'yxati
# ──────────────────────────────────────────────────────────────────────────────

@router.message(F.text == "💰 Coin sotib olish")
async def buy_coins_menu(message: Message, state: FSMContext) -> None:
    if is_spam(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CoinPackage).where(CoinPackage.is_active == True)
        )
        packages = result.scalars().all()

    if not packages:
        await message.answer("❌ Hozirda mavjud paketlar yo'q. Keyinroq urinib ko'ring.")
        return

    await state.set_state(PaymentStates.choosing_package)
    await message.answer(
        "💰 <b>Coin sotib olish</b>\n\nQuyidagi paketlardan birini tanlang:",
        reply_markup=packages_kb(packages),
        parse_mode="HTML",
    )


# ──────────────────────────────────────────────────────────────────────────────
# 2. Paket tanlandi → karta ma'lumotlari
# ──────────────────────────────────────────────────────────────────────────────

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
        card_owner  = await get_setting(session, "card_owner",  "Bot Admin")

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
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("i_paid:"))
async def i_paid(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "📸 <b>Chek rasmini yuboring</b>\n\n"
        "To'lov chekining rasmini (screenshot yoki fotosurat) yuboring.\n\n"
        "⚠️ Eslatma: Cheksiz to'lovlar tasdiqlanmaydi.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_payment")
async def cancel_payment_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ To'lov bekor qilindi.")
    await callback.answer()


# ──────────────────────────────────────────────────────────────────────────────
# 3. Chek rasmi keldi → adminlarga yuborish
# ──────────────────────────────────────────────────────────────────────────────

@router.message(PaymentStates.waiting_receipt, F.photo)
async def receipt_received(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    pkg_id = data.get("package_id")
    if not pkg_id:
        await state.clear()
        return

    photo_file_id = message.photo[-1].file_id

    async with AsyncSessionLocal() as session:
        user_res = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = user_res.scalars().first()
        if not user:
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
            f"📦 Paket: <b>{package.coins} coin</b>\n"
            f"💰 Summa: <b>{package.price_uzs:,} so'm</b>\n"
            f"📅 Vaqt: {payment.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"⏳ <b>Holat: Ko'rib chiqilmoqda</b>"
        )

        # Barcha adminlarga chek + tugmalar yuborish
        first_msg_id = None
        for admin_id in ADMIN_IDS:
            try:
                sent = await bot.send_photo(
                    chat_id=admin_id,
                    photo=photo_file_id,
                    caption=admin_text,
                    reply_markup=admin_payment_kb(payment.id),
                    parse_mode="HTML",
                )
                if first_msg_id is None:
                    first_msg_id = sent.message_id
                    payment.admin_message_id = sent.message_id
            except Exception as e:
                logger.error(f"Admin {admin_id} ga xabar yuborib bo'lmadi: {e}")

        await session.commit()

    await state.clear()
    await message.answer(
        "✅ <b>Chek qabul qilindi!</b>\n\n"
        "Admin sizning to'lovingizni tekshiradi.\n"
        "⏱ Tasdiqlash vaqti: 5-30 daqiqa\n\n"
        "Tasdiqlangach sizga xabar beriladi! 🎉",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )


@router.message(PaymentStates.waiting_receipt)
async def receipt_not_photo(message: Message) -> None:
    await message.answer(
        "⚠️ Iltimos, faqat <b>rasm (screenshot)</b> yuboring.\n"
        "Matn yoki fayl qabul qilinmaydi.",
        parse_mode="HTML",
    )


# ──────────────────────────────────────────────────────────────────────────────
# 4a. Admin: TASDIQLASH
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("approve_pay:"))
async def approve_pay(callback: CallbackQuery, bot: Bot) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    pay_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        result  = await session.execute(select(Payment).where(Payment.id == pay_id))
        payment = result.scalars().first()
        if not payment:
            await callback.answer("❌ To'lov topilmadi.", show_alert=True)
            return

        user    = await session.get(User, payment.user_id)
        success = await approve_payment(session, payment)

        if not success:
            await callback.answer("⚠️ Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        new_balance = user.balance if user else "?"
        coins       = payment.coins
        amount      = payment.amount_uzs
        admin_name  = callback.from_user.full_name
        admin_uname = f"@{callback.from_user.username}" if callback.from_user.username else admin_name

    # ── Chek mesajini ✅ badge bilan yangilash ──
    new_caption = (
        f"💳 <b>To'lov #{pay_id}</b>\n\n"
        f"👤 Foydalanuvchi: {user.full_name if user else '?'}\n"
        f"📦 {coins} coin | 💰 {amount:,} so'm\n\n"
        f"{'━'*20}\n"
        f"✅ <b>TASDIQLANDI</b>\n"
        f"👮 Admin: {admin_uname}"
    )
    try:
        await callback.message.edit_caption(new_caption, parse_mode="HTML", reply_markup=None)
    except Exception as e:
        logger.warning(f"Admin mesajini edit qilib bo'lmadi: {e}")

    await callback.answer("✅ Muvaffaqiyatli tasdiqlandi!", show_alert=True)

    # ── Boshqa adminlarga xabardorlik ──
    for admin_id in ADMIN_IDS:
        if admin_id == callback.from_user.id:
            continue
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=(
                    f"✅ <b>To'lov #{pay_id} tasdiqlandi</b>\n\n"
                    f"👤 Foydalanuvchi: {user.full_name if user else '?'}\n"
                    f"📦 {coins} coin | 💰 {amount:,} so'm\n"
                    f"👮 Tasdiqlagan: {admin_uname}"
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Admin {admin_id} ga xabar yuborib bo'lmadi: {e}")

    # ── Foydalanuvchiga xabar ──
    if user:
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    "🎉 <b>To'lovingiz tasdiqlandi!</b>\n\n"
                    f"🪙 <b>+{coins} coin</b> balansingizga qo'shildi.\n"
                    f"💎 Joriy balans: <b>{new_balance} coin</b>\n\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "🎨 Endi taqdimot yaratishingiz mumkin!\n"
                    "Asosiy menyudan «🎨 Taqdimot yaratish» ni tanlang."
                ),
                reply_markup=main_menu_kb(),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Foydalanuvchi {user.telegram_id} ga xabar yuborib bo'lmadi: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# 4b-1. Admin: RAD ETISH — qayd so'rash
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("reject_pay:"))
async def reject_pay_start(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    pay_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        result  = await session.execute(select(Payment).where(Payment.id == pay_id))
        payment = result.scalars().first()
        if not payment:
            await callback.answer("❌ To'lov topilmadi.", show_alert=True)
            return
        if payment.status != "pending":
            await callback.answer("⚠️ Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

    await state.set_state(RejectPaymentStates.waiting_reason)
    await state.update_data(
        reject_pay_id=pay_id,
        reject_admin_chat=callback.from_user.id,
    )

    await callback.answer()
    await bot.send_message(
        chat_id=callback.from_user.id,
        text=(
            f"❌ <b>To'lov #{pay_id} — Rad etish</b>\n\n"
            "Foydalanuvchiga <b>rad etish sababini</b> yozing.\n"
            "Bu xabar foydalanuvchiga <b>aynan siz yozganidek</b> yuboriladi.\n\n"
            "<i>Ixtiyoriy — sababsiz rad etmoqchi bo'lsangiz quyidagi tugmani bosing.</i>"
        ),
        reply_markup=reject_reason_kb(pay_id),
        parse_mode="HTML",
    )


# ──────────────────────────────────────────────────────────────────────────────
# 4b-2. Admin: RAD ETISH — qayd matni keldi
# ──────────────────────────────────────────────────────────────────────────────

@router.message(RejectPaymentStates.waiting_reason, F.text)
async def reject_pay_reason(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return

    data   = await state.get_data()
    pay_id = data.get("reject_pay_id")
    reason = message.text.strip()

    await _do_reject(
        bot=bot, state=state,
        admin=message.from_user,
        pay_id=pay_id,
        reason=reason,
        admin_chat_id=message.from_user.id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# 4b-3. Admin: RAD ETISH — qaydsiz
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("reject_noreason:"))
async def reject_pay_noreason(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    pay_id = int(callback.data.split(":")[1])
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass

    await _do_reject(
        bot=bot, state=state,
        admin=callback.from_user,
        pay_id=pay_id,
        reason=None,
        admin_chat_id=callback.from_user.id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# 4b-4. Admin: RAD ETISHNI BEKOR QILISH
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("reject_cancel:"))
async def reject_pay_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text("↩️ Rad etish bekor qilindi.")
    await callback.answer()


# ──────────────────────────────────────────────────────────────────────────────
# Rad etish — ichki mantiq
# ──────────────────────────────────────────────────────────────────────────────

async def _do_reject(
    bot: Bot,
    state: FSMContext,
    admin,
    pay_id: int,
    reason: str | None,
    admin_chat_id: int,
) -> None:
    admin_uname = f"@{admin.username}" if admin.username else admin.full_name
    reason_line = f"\n📝 Sabab: <i>{reason}</i>" if reason else ""

    async with AsyncSessionLocal() as session:
        result  = await session.execute(select(Payment).where(Payment.id == pay_id))
        payment = result.scalars().first()

        if not payment:
            await bot.send_message(admin_chat_id, "❌ To'lov topilmadi.")
            await state.clear()
            return

        user    = await session.get(User, payment.user_id)
        success = await reject_payment(session, payment)

        if not success:
            await bot.send_message(
                admin_chat_id,
                "⚠️ Bu to'lov allaqachon ko'rib chiqilgan.",
            )
            await state.clear()
            return

        if reason:
            payment.reject_reason = reason
        await session.commit()

        coins  = payment.coins
        amount = payment.amount_uzs
        msg_id = payment.admin_message_id

    # ── Chek mesajini ❌ badge bilan yangilash (barcha adminlarda) ──
    if msg_id:
        new_caption = (
            f"💳 <b>To'lov #{pay_id}</b>\n\n"
            f"👤 Foydalanuvchi: {user.full_name if user else '?'}\n"
            f"📦 {coins} coin | 💰 {amount:,} so'm\n\n"
            f"{'━'*20}\n"
            f"❌ <b>RAD ETILDI</b>\n"
            f"👮 Admin: {admin_uname}"
            + reason_line
        )
        for admin_id in ADMIN_IDS:
            try:
                await bot.edit_message_caption(
                    chat_id=admin_id,
                    message_id=msg_id,
                    caption=new_caption,
                    parse_mode="HTML",
                    reply_markup=None,
                )
            except Exception:
                pass  # Boshqa adminlarda message_id boshqacha bo'lishi mumkin

    # ── Rad etgan adminga tasdiqlash xabari ──
    await bot.send_message(
        chat_id=admin_chat_id,
        text=(
            f"✅ <b>To'lov #{pay_id} rad etildi.</b>{reason_line}\n\n"
            f"👤 Foydalanuvchi: {user.full_name if user else '?'}\n"
            f"🪙 {coins} coin | 💰 {amount:,} so'm"
        ),
        parse_mode="HTML",
    )

    # ── Boshqa adminlarga xabardorlik ──
    for admin_id in ADMIN_IDS:
        if admin_id == admin_chat_id:
            continue
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=(
                    f"ℹ️ <b>To'lov #{pay_id} rad etildi</b>\n"
                    f"👤 Foydalanuvchi: {user.full_name if user else '?'}\n"
                    f"👮 Admin: {admin_uname}"
                    + reason_line
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Admin {admin_id} ga xabar yuborib bo'lmadi: {e}")

    # ── Foydalanuvchiga xabar ──
    if user:
        if reason:
            reason_block = (
                f"\n\n📝 <b>Admin izohi:</b>\n"
                f"<blockquote>{reason}</blockquote>"
            )
        else:
            reason_block = "\n\n❓ Qo'shimcha ma'lumot uchun admin bilan bog'laning."

        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    "❌ <b>Afsuski, to'lovingiz rad etildi.</b>"
                    + reason_block
                    + "\n\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "🔄 Qayta to'lov qilmoqchi bo'lsangiz:\n"
                    "«💰 Coin sotib olish» tugmasini bosing."
                ),
                reply_markup=main_menu_kb(),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Foydalanuvchi {user.telegram_id} ga xabar yuborib bo'lmadi: {e}")

    await state.clear()
