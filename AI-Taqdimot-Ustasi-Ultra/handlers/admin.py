from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDS
from database import AsyncSessionLocal, get_setting, set_setting
from models import CoinPackage, Payment, Presentation, User
from keyboards import (
    admin_coins_kb, admin_main_kb, admin_packages_kb,
    admin_pkg_edit_kb, admin_settings_kb, main_menu_kb,
)
from states import AdminStates
from utils.logger import logger

router = Router()


def admin_only(func):
    """Decorator to restrict access to admins only."""
    async def wrapper(event, *args, **kwargs):
        uid = event.from_user.id if hasattr(event, "from_user") else None
        if uid not in ADMIN_IDS:
            if hasattr(event, "answer"):
                await event.answer("❌ Ruxsat yo'q.")
            return
        return await func(event, *args, **kwargs)
    return wrapper


# ─── Admin entry ──────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("🛠 <b>Admin Panel</b>", reply_markup=admin_main_kb(), parse_mode="HTML")


@router.callback_query(F.data == "adm:back")
async def adm_back(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    await callback.message.edit_text("🛠 <b>Admin Panel</b>", reply_markup=admin_main_kb(), parse_mode="HTML")
    await callback.answer()


# ─── Statistics ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:users")
async def adm_users(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    async with AsyncSessionLocal() as session:
        total = await session.scalar(select(func.count(User.id)))
        blocked = await session.scalar(select(func.count(User.id)).where(User.is_blocked == True))
        new_today = await session.scalar(
            select(func.count(User.id)).where(
                func.date(User.created_at) == func.date(func.now())
            )
        )
    await callback.message.edit_text(
        f"👥 <b>Foydalanuvchilar</b>\n\n"
        f"📊 Jami: <b>{total}</b>\n"
        f"🆕 Bugun: <b>{new_today}</b>\n"
        f"🚫 Bloklangan: <b>{blocked}</b>",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "adm:stats")
async def adm_stats(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    async with AsyncSessionLocal() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        total_payments = await session.scalar(select(func.count(Payment.id)))
        approved_payments = await session.scalar(
            select(func.count(Payment.id)).where(Payment.status == "approved")
        )
        total_revenue = await session.scalar(
            select(func.sum(Payment.amount_uzs)).where(Payment.status == "approved")
        ) or 0
        total_pres = await session.scalar(select(func.count(Presentation.id)))
        pending = await session.scalar(
            select(func.count(Payment.id)).where(Payment.status == "pending")
        )

    await callback.message.edit_text(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{total_users}</b>\n"
        f"💰 Jami to'lovlar: <b>{total_payments}</b>\n"
        f"✅ Tasdiqlangan: <b>{approved_payments}</b>\n"
        f"⏳ Kutilayotgan: <b>{pending}</b>\n"
        f"💵 Jami daromad: <b>{total_revenue:,} so'm</b>\n"
        f"🎨 Taqdimotlar: <b>{total_pres}</b>",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Pending payments ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:pending")
async def adm_pending(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Payment).where(Payment.status == "pending").order_by(Payment.created_at)
        )
        payments = result.scalars().all()

    if not payments:
        await callback.message.edit_text(
            "✅ <b>Kutilayotgan to'lovlar yo'q!</b>",
            reply_markup=admin_main_kb(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    lines = [f"✅ <b>Kutilayotgan to'lovlar ({len(payments)} ta):</b>\n"]
    for p in payments:
        lines.append(f"• #{p.id} — {p.coins} coin — {p.amount_uzs:,} so'm — {p.created_at.strftime('%d.%m %H:%M')}")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "adm:payments")
async def adm_payments(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Payment).order_by(Payment.created_at.desc()).limit(15)
        )
        payments = result.scalars().all()

    if not payments:
        await callback.message.edit_text("💰 To'lovlar yo'q.", reply_markup=admin_main_kb(), parse_mode="HTML")
        await callback.answer()
        return

    lines = [f"💰 <b>So'nggi 15 ta to'lov:</b>\n"]
    status_icon = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
    for p in payments:
        icon = status_icon.get(p.status, "❓")
        lines.append(f"{icon} #{p.id} — {p.coins} coin — {p.amount_uzs:,} so'm — {p.created_at.strftime('%d.%m %H:%M')}")

    await callback.message.edit_text("\n".join(lines), reply_markup=admin_main_kb(), parse_mode="HTML")
    await callback.answer()


# ─── Coins management ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:coins")
async def adm_coins(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.message.edit_text(
        "🪙 <b>Coin boshqarish</b>\n\nFoydalanuvchiga coin qo'shish yoki olish:",
        reply_markup=admin_coins_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "adm:add_coins")
async def adm_add_coins_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AdminStates.enter_user_id_add)
    await callback.message.edit_text(
        "➕ <b>Coin qo'shish</b>\n\nFoydalanuvchi Telegram ID sini kiriting:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.enter_user_id_add)
async def adm_add_coins_uid(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Noto'g'ri ID. Raqam kiriting:")
        return
    await state.update_data(target_uid=uid)
    await state.set_state(AdminStates.enter_coins_add)
    await message.answer("Necha coin qo'shish kerak?")


@router.message(AdminStates.enter_coins_add)
async def adm_add_coins_amount(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        amount = int(message.text.strip())
        assert amount > 0
    except (ValueError, AssertionError):
        await message.answer("❌ Musbat son kiriting:")
        return

    data = await state.get_data()
    target_uid = data["target_uid"]

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == target_uid))
        user = result.scalars().first()
        if not user:
            await message.answer("❌ Foydalanuvchi topilmadi.")
            await state.clear()
            return
        user.balance += amount
        await session.commit()
        new_bal = user.balance

    await state.clear()
    await message.answer(
        f"✅ <b>{amount} coin qo'shildi!</b>\n"
        f"👤 {user.full_name}\n"
        f"💎 Yangi balans: {new_bal} coin",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm:remove_coins")
async def adm_remove_coins_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AdminStates.enter_user_id_remove)
    await callback.message.edit_text(
        "➖ <b>Coin olish</b>\n\nFoydalanuvchi Telegram ID sini kiriting:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.enter_user_id_remove)
async def adm_remove_coins_uid(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Raqam kiriting:")
        return
    await state.update_data(target_uid=uid)
    await state.set_state(AdminStates.enter_coins_remove)
    await message.answer("Necha coin olish kerak?")


@router.message(AdminStates.enter_coins_remove)
async def adm_remove_coins_amount(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        amount = int(message.text.strip())
        assert amount > 0
    except (ValueError, AssertionError):
        await message.answer("❌ Musbat son kiriting:")
        return

    data = await state.get_data()
    target_uid = data["target_uid"]

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == target_uid))
        user = result.scalars().first()
        if not user:
            await message.answer("❌ Foydalanuvchi topilmadi.")
            await state.clear()
            return
        user.balance = max(0, user.balance - amount)
        await session.commit()
        new_bal = user.balance

    await state.clear()
    await message.answer(
        f"✅ <b>{amount} coin olindi!</b>\n"
        f"👤 {user.full_name}\n"
        f"💎 Yangi balans: {new_bal} coin",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )


# ─── Broadcast ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:broadcast")
async def adm_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AdminStates.broadcast_message)
    await callback.message.edit_text(
        "📢 <b>Xabar yuborish</b>\n\nBarcha foydalanuvchilarga yuboriladigan xabarni kiriting:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.broadcast_message)
async def adm_broadcast_send(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    text = message.text or message.caption or ""
    if not text:
        await message.answer("❌ Matn kiriting.")
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.is_blocked == False)
        )
        users = result.scalars().all()

    sent = 0
    failed = 0
    for user in users:
        try:
            await bot.send_message(user.telegram_id, f"📢 <b>Yangilik!</b>\n\n{text}", parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1

    await state.clear()
    await message.answer(
        f"📢 <b>Xabar yuborildi!</b>\n\n✅ Muvaffaqiyatli: {sent}\n❌ Yuborilmadi: {failed}",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )


# ─── Block user ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:block")
async def adm_block_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AdminStates.block_user_id)
    await callback.message.edit_text(
        "🚫 <b>Foydalanuvchini bloklash/blokdan chiqarish</b>\n\n"
        "Foydalanuvchi Telegram ID sini kiriting:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.block_user_id)
async def adm_block_user(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Raqam kiriting:")
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == uid))
        user = result.scalars().first()
        if not user:
            await message.answer("❌ Foydalanuvchi topilmadi.")
            await state.clear()
            return
        user.is_blocked = not user.is_blocked
        await session.commit()
        status = "bloklandi 🚫" if user.is_blocked else "blokdan chiqarildi ✅"

    await state.clear()
    await message.answer(
        f"👤 <b>{user.full_name}</b> {status}",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )


# ─── Settings (card) ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:settings")
async def adm_settings(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    async with AsyncSessionLocal() as session:
        card_number = await get_setting(session, "card_number")
        card_owner = await get_setting(session, "card_owner")
    await callback.message.edit_text(
        f"⚙️ <b>Sozlamalar</b>\n\n"
        f"💳 Karta: <code>{card_number}</code>\n"
        f"👤 Egasi: <b>{card_owner}</b>",
        reply_markup=admin_settings_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "adm:card_number")
async def adm_card_number(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AdminStates.card_number_edit)
    await callback.message.edit_text("💳 Yangi karta raqamini kiriting:\n<i>Misol: 8600 1234 5678 9012</i>", parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.card_number_edit)
async def adm_save_card_number(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    async with AsyncSessionLocal() as session:
        await set_setting(session, "card_number", message.text.strip())
    await state.clear()
    await message.answer(f"✅ Karta raqami yangilandi: <code>{message.text.strip()}</code>", reply_markup=admin_main_kb(), parse_mode="HTML")


@router.callback_query(F.data == "adm:card_owner")
async def adm_card_owner(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AdminStates.card_owner_edit)
    await callback.message.edit_text("👤 Karta egasining ismini kiriting:", parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.card_owner_edit)
async def adm_save_card_owner(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    async with AsyncSessionLocal() as session:
        await set_setting(session, "card_owner", message.text.strip())
    await state.clear()
    await message.answer(f"✅ Karta egasi yangilandi: <b>{message.text.strip()}</b>", reply_markup=admin_main_kb(), parse_mode="HTML")


# ─── Package management ───────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:packages")
async def adm_packages(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CoinPackage).order_by(CoinPackage.coins))
        packages = result.scalars().all()
    await callback.message.edit_text(
        "🧾 <b>Coin paketlari</b>\n\nPaketni tanlang:",
        reply_markup=admin_packages_kb(packages),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm:pkg_edit:"))
async def adm_pkg_edit(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    pkg_id = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        pkg = await session.get(CoinPackage, pkg_id)
    if not pkg:
        await callback.answer("Paket topilmadi.")
        return
    await callback.message.edit_text(
        f"🧾 <b>Paket #{pkg.id}</b>\n\n"
        f"🪙 Coinlar: {pkg.coins}\n"
        f"💰 Narx: {pkg.price_uzs:,} so'm\n"
        f"📊 Holat: {'✅ Faol' if pkg.is_active else '❌ Nofaol'}",
        reply_markup=admin_pkg_edit_kb(pkg.id, pkg.is_active),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm:pkg_toggle:"))
async def adm_pkg_toggle(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    pkg_id = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        pkg = await session.get(CoinPackage, pkg_id)
        if pkg:
            pkg.is_active = not pkg.is_active
            await session.commit()
            status = "✅ Faol" if pkg.is_active else "❌ Nofaol"
    await callback.answer(f"Holat: {status}")
    await adm_packages(callback)


@router.callback_query(F.data.startswith("adm:pkg_price:"))
async def adm_pkg_price_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    pkg_id = int(callback.data.split(":")[2])
    await state.update_data(pkg_id=pkg_id)
    await state.set_state(AdminStates.package_edit_value)
    await callback.message.edit_text("💰 Yangi narxni (so'mda) kiriting:", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("adm:pkg_coins:"))
async def adm_pkg_coins_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    pkg_id = int(callback.data.split(":")[2])
    await state.update_data(pkg_id=pkg_id, edit_field="coins")
    await state.set_state(AdminStates.package_edit_value)
    await callback.message.edit_text("🪙 Yangi coin miqdorini kiriting:", parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.package_edit_value)
async def adm_pkg_save_value(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        val = int(message.text.strip())
        assert val > 0
    except (ValueError, AssertionError):
        await message.answer("❌ Musbat son kiriting:")
        return
    data = await state.get_data()
    pkg_id = data.get("pkg_id")
    field = data.get("edit_field", "price")
    async with AsyncSessionLocal() as session:
        pkg = await session.get(CoinPackage, pkg_id)
        if pkg:
            if field == "coins":
                pkg.coins = val
            else:
                pkg.price_uzs = val
            await session.commit()
    await state.clear()
    await message.answer(f"✅ Paket yangilandi!", reply_markup=admin_main_kb())


@router.callback_query(F.data == "adm:pkg_new")
async def adm_pkg_new_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AdminStates.package_new_coins)
    await callback.message.edit_text("➕ <b>Yangi paket</b>\n\nCoin miqdorini kiriting:", parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.package_new_coins)
async def adm_pkg_new_coins(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        coins = int(message.text.strip())
        assert coins > 0
    except (ValueError, AssertionError):
        await message.answer("❌ Musbat son kiriting:")
        return
    await state.update_data(new_coins=coins)
    await state.set_state(AdminStates.package_new_price)
    await message.answer("💰 Narxni (so'mda) kiriting:")


@router.message(AdminStates.package_new_price)
async def adm_pkg_new_price(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        price = int(message.text.strip())
        assert price > 0
    except (ValueError, AssertionError):
        await message.answer("❌ Musbat son kiriting:")
        return
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        pkg = CoinPackage(coins=data["new_coins"], price_uzs=price)
        session.add(pkg)
        await session.commit()
    await state.clear()
    await message.answer(
        f"✅ Yangi paket qo'shildi: {data['new_coins']} coin = {price:,} so'm",
        reply_markup=admin_main_kb(),
    )
