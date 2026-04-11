import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ChatMemberHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8780908767:AAEewN-jTc2_19hUZRu9mf-qudBTKM2A8Gk"   # @BotFather dan olingan token
ADMIN_IDS = [8537782289]             # Admin Telegram ID lari (list)

# ===================== LOGGING =====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== DATABASE =====================
def init_db():
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            chat_id     INTEGER PRIMARY KEY,
            title       TEXT,
            username    TEXT,
            member_count INTEGER DEFAULT 0,
            added_date  TEXT,
            is_banned   INTEGER DEFAULT 0,
            ban_reason  TEXT DEFAULT ''
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id     INTEGER,
            user_id     INTEGER,
            username    TEXT,
            date        TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    # Default sozlama
    c.execute("INSERT OR IGNORE INTO settings VALUES ('mention_mode', 'on')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('mention_text', '👋 Salom {mention}, xush kelibsiz!')")
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect("bot_data.db")

def add_group(chat_id, title, username):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO groups (chat_id, title, username, added_date)
        VALUES (?, ?, ?, ?)
    """, (chat_id, title, username or "", datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def update_group_title(chat_id, title):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE groups SET title=? WHERE chat_id=?", (title, chat_id))
    conn.commit()
    conn.close()

def ban_group(chat_id, reason=""):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE groups SET is_banned=1, ban_reason=? WHERE chat_id=?", (reason, chat_id))
    conn.commit()
    conn.close()

def unban_group(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE groups SET is_banned=0, ban_reason='' WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()

def is_banned(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT is_banned FROM groups WHERE chat_id=?", (chat_id,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == 1

def get_all_groups():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT chat_id, title, username, member_count, added_date, is_banned, ban_reason FROM groups")
    rows = c.fetchall()
    conn.close()
    return rows

def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM groups WHERE is_banned=0")
    active = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM groups WHERE is_banned=1")
    banned = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages")
    total_msg = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages WHERE date >= date('now')")
    today_msg = c.fetchone()[0]
    conn.close()
    return active, banned, total_msg, today_msg

def get_setting(key):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def log_message(chat_id, user_id, username):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (chat_id, user_id, username, date) VALUES (?,?,?,?)",
        (chat_id, user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()

# ===================== HELPERS =====================
def is_admin(user_id):
    return user_id in ADMIN_IDS

def admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Statistika", callback_data="stats"),
         InlineKeyboardButton("👥 Guruhlar", callback_data="groups_list_0")],
        [InlineKeyboardButton("🚫 Taqiqlangan", callback_data="banned_list"),
         InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings")],
        [InlineKeyboardButton("📢 Hammaga xabar", callback_data="broadcast_prompt")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ===================== HANDLERS =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.effective_chat.type != "private":
        return

    if is_admin(user.id):
        text = (
            f"👋 Salom, <b>{user.first_name}</b>!\n\n"
            "🤖 <b>Bot Admin Paneli</b>ga xush kelibsiz.\n"
            "Quyidagi tugmalardan foydalaning:"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML,
                                        reply_markup=admin_keyboard())
    else:
        await update.message.reply_text(
            f"👋 Salom, <b>{user.first_name}</b>!\n"
            "Men guruh botiman. Meni guruhingizga qoʻshing va admin qiling! 🚀",
            parse_mode=ParseMode.HTML
        )

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "🛠 <b>Admin Panel</b>", parse_mode=ParseMode.HTML,
        reply_markup=admin_keyboard()
    )

# --- Guruhga qo'shilganda / chiqarilganda ---
async def track_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if not result:
        return
    chat = result.chat
    new_status = result.new_chat_member.status

    if new_status in (ChatMember.MEMBER, ChatMember.ADMINISTRATOR):
        if chat.type in ("group", "supergroup"):
            add_group(chat.id, chat.title, chat.username)
            logger.info(f"Bot added to group: {chat.title} ({chat.id})")
    elif new_status in (ChatMember.LEFT, ChatMember.BANNED):
        logger.info(f"Bot removed from group: {chat.title} ({chat.id})")

# --- Guruhdagi xabarlar ---
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not user or chat.type not in ("group", "supergroup"):
        return

    # Taqiqlangan guruh tekshiruvi
    if is_banned(chat.id):
        return

    # Guruhni yangilash
    add_group(chat.id, chat.title, chat.username)

    # Xabarni log qilish
    log_message(chat.id, user.id, user.username or user.first_name)

    # Mention rejimi
    mode = get_setting("mention_mode")
    if mode != "on":
        return

    mention_text = get_setting("mention_text") or "👋 {mention}"
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    reply = mention_text.replace("{mention}", mention)\
                        .replace("{name}", user.first_name)\
                        .replace("{group}", chat.title)

    await update.message.reply_text(reply, parse_mode=ParseMode.HTML)

# ===================== CALLBACK HANDLER =====================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if not is_admin(user_id):
        await query.edit_message_text("❌ Ruxsat yoʻq!")
        return

    # --- STATISTIKA ---
    if data == "stats":
        active, banned, total_msg, today_msg = get_stats()
        text = (
            "📊 <b>Bot Statistikasi</b>\n\n"
            f"✅ Faol guruhlar: <b>{active}</b>\n"
            f"🚫 Taqiqlangan: <b>{banned}</b>\n"
            f"💬 Jami xabarlar: <b>{total_msg}</b>\n"
            f"📅 Bugungi xabarlar: <b>{today_msg}</b>\n"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    # --- GURUHLAR RO'YXATI ---
    elif data.startswith("groups_list_"):
        page = int(data.split("_")[-1])
        groups = [g for g in get_all_groups() if g[5] == 0]
        per_page = 5
        start_idx = page * per_page
        end_idx = start_idx + per_page
        page_groups = groups[start_idx:end_idx]

        if not page_groups:
            text = "👥 Hech qanday guruh yoʻq."
        else:
            text = f"👥 <b>Faol Guruhlar</b> ({len(groups)} ta):\n\n"
            for g in page_groups:
                chat_id, title, username, members, added, _, _ = g
                uname = f"@{username}" if username else "—"
                text += f"• <b>{title}</b>\n  🆔 <code>{chat_id}</code> | {uname}\n  📅 {added}\n\n"

        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"groups_list_{page-1}"))
        if end_idx < len(groups):
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"groups_list_{page+1}"))

        keyboard = []
        if nav_buttons:
            keyboard.append(nav_buttons)

        # Guruh taqiqlash uchun ID kiritish
        keyboard.append([InlineKeyboardButton("🚫 Guruh taqiqlash", callback_data="ban_group_prompt")])
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                      reply_markup=InlineKeyboardMarkup(keyboard))

    # --- TAQIQLANGAN GURUHLAR ---
    elif data == "banned_list":
        groups = [g for g in get_all_groups() if g[5] == 1]
        if not groups:
            text = "✅ Taqiqlangan guruh yoʻq."
        else:
            text = f"🚫 <b>Taqiqlangan Guruhlar</b> ({len(groups)} ta):\n\n"
            for g in groups:
                chat_id, title, username, _, added, _, reason = g
                text += f"• <b>{title}</b>\n  🆔 <code>{chat_id}</code>\n  📝 {reason or 'Sabab yoʻq'}\n\n"

        keyboard = [
            [InlineKeyboardButton("✅ Guruhni tiklash", callback_data="unban_group_prompt")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]
        ]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                      reply_markup=InlineKeyboardMarkup(keyboard))

    # --- SOZLAMALAR ---
    elif data == "settings":
        mode = get_setting("mention_mode")
        mention_text = get_setting("mention_text")
        status = "✅ Yoqilgan" if mode == "on" else "❌ O'chirilgan"
        text = (
            "⚙️ <b>Bot Sozlamalari</b>\n\n"
            f"💬 Mention rejimi: {status}\n\n"
            f"📝 Mention matni:\n<code>{mention_text}</code>\n\n"
            "<i>O'zgaruvchilar: {mention}, {name}, {group}</i>"
        )
        toggle = "off" if mode == "on" else "on"
        toggle_text = "❌ O'chirish" if mode == "on" else "✅ Yoqish"
        keyboard = [
            [InlineKeyboardButton(toggle_text, callback_data=f"toggle_mention_{toggle}")],
            [InlineKeyboardButton("✏️ Matnni o'zgartirish", callback_data="change_mention_text")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]
        ]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                      reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("toggle_mention_"):
        new_val = data.split("_")[-1]
        set_setting("mention_mode", new_val)
        await query.answer("✅ Saqlandi!", show_alert=True)
        # Sozlamalarni qayta ko'rsatish
        context.user_data["action"] = None
        await callback_handler_redirect(query, context, "settings")

    elif data == "change_mention_text":
        context.user_data["action"] = "change_mention_text"
        await query.edit_message_text(
            "✏️ Yangi mention matnini yuboring.\n\n"
            "<i>O'zgaruvchilar: {mention}, {name}, {group}</i>\n"
            "Misol: <code>👋 {mention}, salom!</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor qilish", callback_data="settings")]]))

    elif data == "ban_group_prompt":
        context.user_data["action"] = "ban_group"
        await query.edit_message_text(
            "🚫 Taqiqlash uchun guruh <b>ID</b>sini yuboring:\n"
            "<i>Misol: -1001234567890</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor qilish", callback_data="groups_list_0")]]))

    elif data == "unban_group_prompt":
        context.user_data["action"] = "unban_group"
        await query.edit_message_text(
            "✅ Tiklash uchun guruh <b>ID</b>sini yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor qilish", callback_data="banned_list")]]))

    elif data == "broadcast_prompt":
        context.user_data["action"] = "broadcast"
        await query.edit_message_text(
            "📢 Barcha guruhlarga yuboriladigan xabarni yozing:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor qilish", callback_data="back_main")]]))

    elif data == "back_main":
        await query.edit_message_text(
            "🛠 <b>Admin Panel</b>", parse_mode=ParseMode.HTML,
            reply_markup=admin_keyboard())

async def callback_handler_redirect(query, context, target):
    """Sozlamalarni qayta yuklovchi yordamchi funksiya"""
    mode = get_setting("mention_mode")
    mention_text = get_setting("mention_text")
    status = "✅ Yoqilgan" if mode == "on" else "❌ O'chirilgan"
    text = (
        "⚙️ <b>Bot Sozlamalari</b>\n\n"
        f"💬 Mention rejimi: {status}\n\n"
        f"📝 Mention matni:\n<code>{mention_text}</code>\n\n"
        "<i>O'zgaruvchilar: {mention}, {name}, {group}</i>"
    )
    toggle = "off" if mode == "on" else "on"
    toggle_text = "❌ O'chirish" if mode == "on" else "✅ Yoqish"
    keyboard = [
        [InlineKeyboardButton(toggle_text, callback_data=f"toggle_mention_{toggle}")],
        [InlineKeyboardButton("✏️ Matnni o'zgartirish", callback_data="change_mention_text")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]
    ]
    await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                  reply_markup=InlineKeyboardMarkup(keyboard))

# --- Admin PM xabar handler ---
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id) or update.effective_chat.type != "private":
        return

    action = context.user_data.get("action")
    text = update.message.text

    if action == "ban_group":
        try:
            chat_id = int(text.strip())
            ban_group(chat_id, "Admin tomonidan taqiqlandi")
            context.user_data["action"] = None
            await update.message.reply_text(
                f"✅ Guruh <code>{chat_id}</code> taqiqlandi!",
                parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID! Raqam kiriting.")

    elif action == "unban_group":
        try:
            chat_id = int(text.strip())
            unban_group(chat_id)
            context.user_data["action"] = None
            await update.message.reply_text(
                f"✅ Guruh <code>{chat_id}</code> tiklandi!",
                parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID!")

    elif action == "change_mention_text":
        set_setting("mention_text", text)
        context.user_data["action"] = None
        await update.message.reply_text(
            "✅ Mention matni saqlandi!\n\n"
            f"Yangi matn: <code>{text}</code>",
            parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())

    elif action == "broadcast":
        groups = [g for g in get_all_groups() if g[5] == 0]
        sent, failed = 0, 0
        for g in groups:
            try:
                await context.bot.send_message(
                    chat_id=g[0], text=f"📢 <b>E'lon:</b>\n\n{text}",
                    parse_mode=ParseMode.HTML)
                sent += 1
            except Exception:
                failed += 1
        context.user_data["action"] = None
        await update.message.reply_text(
            f"📢 <b>Yuborildi!</b>\n✅ Muvaffaqiyatli: {sent}\n❌ Xato: {failed}",
            parse_mode=ParseMode.HTML, reply_markup=admin_keyboard())

# ===================== MAIN =====================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(ChatMemberHandler(track_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
        handle_admin_message))
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
        handle_group_message))

    logger.info("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
