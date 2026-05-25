from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from models import CoinPackage


# ─── Main Menu ────────────────────────────────────────────────────────────────

def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🎨 Taqdimot yaratish"),
        KeyboardButton(text="💰 Coin sotib olish"),
    )
    builder.row(
        KeyboardButton(text="👛 Balansim"),
        KeyboardButton(text="📂 Taqdimotlarim"),
    )
    builder.row(
        KeyboardButton(text="ℹ️ Bot haqida"),
        KeyboardButton(text="📞 Aloqa"),
    )
    return builder.as_markup(resize_keyboard=True)


# ─── Coin Packages ────────────────────────────────────────────────────────────

def packages_kb(packages: list[CoinPackage]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pkg in packages:
        builder.row(
            InlineKeyboardButton(
                text=f"🪙 {pkg.coins} Coin — {pkg.price_uzs:,} so'm",
                callback_data=f"buy_package:{pkg.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_main"))
    return builder.as_markup()


# ─── Payment ──────────────────────────────────────────────────────────────────

def paid_kb(package_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ To'ladim", callback_data=f"i_paid:{package_id}"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_payment"))
    return builder.as_markup()


def admin_payment_kb(payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_pay:{payment_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_pay:{payment_id}"),
    )
    return builder.as_markup()


# ─── Presentation wizard ──────────────────────────────────────────────────────

def language_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uzbek"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:russian"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:english"),
    )
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_pres"))
    return builder.as_markup()


def style_kb() -> InlineKeyboardMarkup:
    styles = [
        ("🎓 Akademik", "Academic"),
        ("💼 Biznes", "Business"),
        ("🎨 Ijodiy", "Creative"),
        ("📚 Ta'limiy", "Educational"),
        ("⬜ Minimal", "Minimal"),
    ]
    builder = InlineKeyboardBuilder()
    for label, val in styles:
        builder.button(text=label, callback_data=f"style:{val}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_pres"))
    return builder.as_markup()


def color_kb() -> InlineKeyboardMarkup:
    colors = [
        ("🔵 Ko'k", "Blue"),
        ("⚫ Qora", "Black"),
        ("⚪ Oq", "White"),
        ("🟢 Yashil", "Green"),
        ("🌑 Premium qora", "PremiumDark"),
    ]
    builder = InlineKeyboardBuilder()
    for label, val in colors:
        builder.button(text=label, callback_data=f"color:{val}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_pres"))
    return builder.as_markup()


def output_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📝 Faqat matn — 5 coin", callback_data="output:text"))
    builder.row(InlineKeyboardButton(text="📊 PPTX fayl — 10 coin", callback_data="output:pptx"))
    builder.row(InlineKeyboardButton(text="⭐ Premium batafsil — 15 coin", callback_data="output:premium"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_pres"))
    return builder.as_markup()


def confirm_presentation_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_pres"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_pres"),
    )
    return builder.as_markup()


# ─── Admin Panel ──────────────────────────────────────────────────────────────

def admin_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="adm:users"),
        InlineKeyboardButton(text="💰 To'lovlar", callback_data="adm:payments"),
    )
    builder.row(
        InlineKeyboardButton(text="✅ Kutilayotgan", callback_data="adm:pending"),
        InlineKeyboardButton(text="🪙 Coin boshqarish", callback_data="adm:coins"),
    )
    builder.row(
        InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="adm:broadcast"),
        InlineKeyboardButton(text="🚫 Bloklash", callback_data="adm:block"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="adm:stats"),
        InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="adm:settings"),
    )
    builder.row(InlineKeyboardButton(text="🧾 Paketlarni tahrirlash", callback_data="adm:packages"))
    return builder.as_markup()


def admin_coins_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Coin qo'shish", callback_data="adm:add_coins"),
        InlineKeyboardButton(text="➖ Coin olish", callback_data="adm:remove_coins"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:back"))
    return builder.as_markup()


def admin_settings_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Karta raqamini o'zgartirish", callback_data="adm:card_number"))
    builder.row(InlineKeyboardButton(text="👤 Karta egasini o'zgartirish", callback_data="adm:card_owner"))
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:back"))
    return builder.as_markup()


def admin_packages_kb(packages: list[CoinPackage]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pkg in packages:
        status = "✅" if pkg.is_active else "❌"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {pkg.coins} coin = {pkg.price_uzs:,} so'm",
                callback_data=f"adm:pkg_edit:{pkg.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="➕ Yangi paket", callback_data="adm:pkg_new"))
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:back"))
    return builder.as_markup()


def admin_pkg_edit_kb(pkg_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✏️ Narxni o'zgartirish", callback_data=f"adm:pkg_price:{pkg_id}"))
    builder.row(InlineKeyboardButton(text="✏️ Coin miqdorini o'zgartirish", callback_data=f"adm:pkg_coins:{pkg_id}"))
    toggle_label = "❌ O'chirish" if is_active else "✅ Yoqish"
    builder.row(InlineKeyboardButton(text=toggle_label, callback_data=f"adm:pkg_toggle:{pkg_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:packages"))
    return builder.as_markup()


def back_kb(callback: str = "back_main") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data=callback))
    return builder.as_markup()
