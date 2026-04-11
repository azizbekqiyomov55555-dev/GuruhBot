# ╔══════════════════════════════════════════════════════════════════╗
# ║    🤖 YORDAMCHI + 24/7 JONLI EFIR BOT — YANGILANGAN VERSIYA     ║
# ║  ✅ Kontakt tanlash + Taklif + Avtomatik Live Stream             ║
# ╚══════════════════════════════════════════════════════════════════╝
#
# 💡 MASLAHATLAR:
#   1. Botni guruhga ADMIN sifatida qo'shing
#   2. @BotFather → Bot Settings → Group Privacy → DISABLE qiling
#   3. BOT_TOKEN, ADMIN_IDS va LIVE_GROUP_IDS ni to'ldiring
#   4. "Manage Video Chats" admin ruxsatini bering
#   5. pip install python-telegram-bot==20.7

import logging
import sqlite3
import asyncio
import random
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    ChatMember, Bot
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ChatMemberHandler, ContextTypes, filters
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

# ═══════════════════════════════════════════════════════
#                    ⚙️ ASOSIY SOZLAMALAR
# ═══════════════════════════════════════════════════════
BOT_TOKEN      = "8780908767:AAEewN-jTc2_19hUZRu9mf-qudBTKM2A8Gk"  # Bot token
ADMIN_IDS      = [8537782289]          # Admin Telegram ID lari
BOT_NAME       = "Yordamchi Bot"

# ── Jonli Efir Sozlamalari ──────────────────────────────
LIVE_GROUP_IDS = [
    -1003835671404,   # 1-guruh
    -1002823910957,   # 2-guruh
]
LIVE_TITLE     = "🔴 24/7 Jonli Efir"  # Efir nomi
CHECK_INTERVAL = 60                    # Har necha sekundda tekshirsin

# ── Taklif Xabari Sozlamalari ───────────────────────────
INVITE_INTERVAL = 60                   # Har necha sekundda xabar tashlansin
INVITE_MESSAGE  = (
    "👋 <b>Assalom aleykum birodarlar!</b>\n\n"
    "👥 Guruhga odam qo'shinlar akalar!\n"
    "Ko'taraylik guruhni! 💪\n\n"
    "Joniyiz sog' bo'lsin! 🤝🌟"
)

# Taklif havola bazasi: invite_link → (user_id, user_name, chat_id)
invite_links_db: dict = {}

# Foydalanuvchi holati: taklif uchun guruh_id saqlash
# user_id → gid
pending_invite: dict = {}


# ═══════════════════════════════════════════════════════
#                  💬 AVTOMATIK JAVOBLAR BAZASI
# ═══════════════════════════════════════════════════════
RESPONSES = {

    # ── SALOMLASHUVLAR ──────────────────────────────────
    "assalomu alaykum": [
        "Va alaykum assalom va rahmatulloh, {name}! 🤲✨",
        "Va alaykum assalom, {name}! Xayrli kun! 😊",
        "Assalomu alaykum {name}! Yaxshi keldingiz! 🌟",
    ],
    "assalom": [
        "Va alaykum assalom, {name}! 🙏😊",
        "Assalomdan ham yaxshi so'z yo'q, {name}! ✨",
        "Va alaykum {name}! Xayrli kun! ☀️",
        "Assalomu alaykum {name}! Xush kelibsiz! 🌟",
    ],
    "salom": [
        "Va alaykum assalom, {name}! 😊",
        "Salom-salom {name}! Qandaysiz? 😄",
        "Vaalaykum {name}! Yaxshi kunlar tilaman! ☀️",
        "Hey {name}, salom! Kayfiyat qanday? 😎",
        "Salom {name}! Bugun ham zo'r kun bo'lsin! ✨",
        "Vaalaykum assalom {name}! 👋🌟",
    ],
    "xayrli tong": [
        "Xayrli tong {name}! ☀️🌸 Yangi kun yangi imkoniyat!",
        "Tong muborak {name}! ☀️ Omadli kun bo'lsin!",
        "{name}, xayrli tong! 🌅 Kofengiz tayyor bo'lsin! ☕",
        "Xayrli tong! 🌅 {name}, bugun ajoyib kun bo'ladi!",
    ],
    "xayrli kun": [
        "Sizga ham xayrli kun {name}! ☀️😊",
        "Xayrli kun {name}! 🌟 Kayfiyat a'lo bo'lsin!",
        "Rahmat {name}! Sizga ham baxtli kun! 🌈",
        "{name}, xayrli kun! Omad har doim sizda bo'lsin! 🍀",
    ],
    "xayrli kech": [
        "Xayrli kech {name}! 🌙✨ Yaxshi dam oling!",
        "{name}, xayrli oqshom! 🌃 Charchagan bo'lsangiz dam oling!",
        "Xayrli kech {name}! 🌙 Tinch tun bo'lsin!",
    ],
    "привет": [
        "Привет {name}! 😊",
        "Привет-привет {name}! Как дела? 😄",
        "Здравствуй {name}! Xush kelibsiz! 👋",
    ],
    "hello": [
        "Hello {name}! 👋 Welcome!",
        "Hey {name}! 😊 Nice to meet you!",
        "Hi {name}! Salom! 🌟",
    ],
    "hi": [
        "Hi {name}! 👋",
        "Hey {name}! 😊",
        "Hello {name}! 🌟",
    ],
    "ало": [
        "Alo {name}! 📞 Eshityapman!",
        "Ha {name}! Nima gap? 😄",
    ],
    "alo": [
        "Alo {name}! 📞 Ha, eshityapman!",
        "Ha {name}! Nima deysan? 😊",
        "Eshityapman {name}! 👂",
    ],

    # ── XAYRLASHUVLAR ───────────────────────────────────
    "xayr": [
        "Xayr {name}! 👋 Ko'rishguncha! Eson-omon yuring!",
        "Xayr-xayr {name}! 🌟 Sog' bo'ling!",
        "{name}, ko'rishguncha! 👋 Yaxshi keting!",
        "Xayr {name}! Omad bilan! 🍀",
    ],
    "hayr": [
        "Hayr {name}! Ko'rishguncha! 👋",
        "Eson-omon yuring {name}! 🌟",
    ],
    "bye": [
        "Bye {name}! Ko'rishguncha! 👋",
        "See you {name}! 😊",
        "Bye-bye {name}! 🌟",
    ],
    "yaxshi kecha": [
        "Yaxshi kecha {name}! 🌙✨ Chiroyli tushlar!",
        "{name}, tinch uxlang! 😴🌙",
        "Yaxshi uxlang {name}! 🌙",
    ],

    # ── HOLINI SO'RASH ───────────────────────────────────
    "qalaysiz": [
        "Yaxshi rahmat! {name}, siz-chi? 😊",
        "Ajoyib! {name}, sizga ham yaxshilik tilayman! 🌟",
        "Hammasi zo'r {name}! Siz qalaysiz? 😄",
        "Yaxshi-yaxshi! {name}, siz ham yaxshimisiz? 😊",
    ],
    "qalay": [
        "Yaxshi rahmat {name}! Siz-chi? 😊",
        "Zo'r! {name}, hammasi joyida! 💪",
        "Ajoyib kayfiyatda {name}! Siz-chi? 🌟",
    ],
    "yaxshimisiz": [
        "Ha yaxshi! {name}, siz ham yaxshi bo'ling! 😊",
        "Juda yaxshi rahmat {name}! 🌟",
        "Yaxshi! {name}, sizga ham yaxshilik! 💫",
    ],
    "как дела": [
        "Отлично {name}! Спасибо! 😊",
        "Всё хорошо {name}! 🌟 А у вас?",
    ],
    "nima gap": [
        "{name}, hech gap yo'q, tinch! 😄",
        "Hammasi yaxshi {name}! Siz-chi? 😊",
        "Gap yo'q {name}! Yaxshi kunlar! ☀️",
        "Tinchlik {name}! Nima yangiliklar? 🌟",
    ],
    "how are you": [
        "I'm great {name}! Thanks! 😊",
        "Fine, thank you {name}! And you? 🌟",
    ],

    # ── MINNATDORLIK ─────────────────────────────────────
    "rahmat": [
        "Arzimaydi {name}! 😊 Doimo xizmatda!",
        "Marhamat {name}! 🌟",
        "Iltimos {name}! Kerak bo'lsa yana ayting! 💫",
        "Xursand bo'ldim {name}! 😄",
        "Hech gap emas {name}! 👍",
    ],
    "raxmat": [
        "Arzimaydi {name}! 😊",
        "Marhamat {name}! 🌟",
        "Iltimos {name}! 💫",
    ],
    "спасибо": [
        "Пожалуйста {name}! 😊",
        "Не за что {name}! 🌟",
    ],
    "thank you": [
        "You're welcome {name}! 😊",
        "No problem {name}! 🌟",
    ],
    "thanks": [
        "Sure thing {name}! 😊",
        "No worries {name}! 🌟",
    ],

    # ── KECHIRASIZ ───────────────────────────────────────
    "kechirasiz": [
        "{name}, hech gap emas! 😊",
        "Ayb yo'q {name}! 🌟",
        "Muammo yo'q {name}! 😄",
    ],
    "uzr": [
        "Hech gap emas {name}! 😊",
        "Ayb yo'q {name}, muammo yo'q! 🌟",
        "Mayli {name}! 😄",
    ],

    # ── MAQTOV ───────────────────────────────────────────
    "zo'r": [
        "Ha {name}, rostdan ham zo'r! 💪🔥",
        "Ajoyib {name}! 🌟",
        "Zo'r-zo'r {name}! 👏",
    ],
    "super": [
        "Super-super {name}! 🔥💯",
        "{name}, juda zo'r! 🌟👏",
        "Ajoyib {name}! ✨",
    ],
    "ajoyib": [
        "Ha {name}, chindan ham ajoyib! 🌟✨",
        "Zo'r {name}! 😄",
    ],
    "bravo": [
        "Bravo {name}! 👏🎉",
        "Juda ajoyib {name}! 🌟👏",
    ],
    "barakalla": [
        "Barakalla {name}! 👏🌟",
        "Barakalla, zo'r {name}! 👏😊",
        "{name}, zo'r! Barakalla! 💫",
    ],
    "qoyil": [
        "Qoyilmaqom {name}! 👏✨",
        "Qoyil {name}, zo'r! 🌟",
        "{name}, qoyil qoldirdingiz! 🤩",
    ],
    "ok": [
        "Ok {name}! 👍",
        "Zo'r {name}! ✅",
        "Mayli {name}! 😊",
    ],
    "ha": [
        "Ha, to'g'ri {name}! 👍",
        "Albatta {name}! 😊",
    ],
    "omad": [
        "Omad tilayman {name}! 🍀💫",
        "{name}, omad har doim sizda bo'lsin! 🍀",
    ],
    "inshalloh": [
        "Inshalloh, albatta bo'ladi {name}! 🤲🌟",
        "Inshalloh {name}! 🤲",
    ],
    "mashalloh": [
        "Mashalloh {name}! 🤲🌟",
        "Mashalloh, barakali bo'lsin {name}! 🤲",
    ],
    "alhamdulillah": [
        "Alhamdulillah {name}! 🤲",
        "Alhamdulillah {name}! 🤲🌟",
    ],
    "tabrik": [
        "Tabriklayman {name}! 🎉🎊",
        "Muborak bo'lsin {name}! 🎉",
    ],
    "tug'ilgan kun": [
        "Tug'ilgan kun muborak {name}! 🎂🎉🎊",
        "Ko'p yillar yashang {name}! 🎂🎉",
    ],
    "❤️": [
        "❤️ Rahmat {name}!",
        "🥰 Siz ham {name}!",
    ],
    "👍": [
        "👍 Zo'r {name}!",
        "✅ Yaxshi {name}!",
    ],
    "🔥": [
        "🔥🔥 {name}, zo'r!",
    ],
    "🎉": [
        "🎉🎊 {name}, tabriklayman!",
    ],
}


# ═══════════════════════════════════════════════════════
#              🔍 JAVOB IZLASH (uzun kalitdan boshlab)
# ═══════════════════════════════════════════════════════
def get_auto_reply(text: str, user_name: str):
    t = text.lower().strip()
    for kw in sorted(RESPONSES, key=len, reverse=True):
        if kw in t:
            reply = random.choice(RESPONSES[kw])
            return reply.replace("{name}", user_name)
    return None


# ═══════════════════════════════════════════════════════
#                      📦 DATABASE
# ═══════════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS groups (
        chat_id INTEGER PRIMARY KEY, title TEXT, username TEXT,
        member_count INTEGER DEFAULT 0, added_date TEXT,
        is_banned INTEGER DEFAULT 0, ban_reason TEXT DEFAULT '')""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER,
        user_id INTEGER, username TEXT, date TEXT)""")
    conn.commit(); conn.close()

def get_db(): return sqlite3.connect("bot_data.db")

def add_group(chat_id, title, username):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO groups (chat_id,title,username,added_date) VALUES (?,?,?,?)",
              (chat_id, title, username or "", datetime.now().strftime("%Y-%m-%d %H:%M")))
    c.execute("UPDATE groups SET title=? WHERE chat_id=?", (title, chat_id))
    conn.commit(); conn.close()

def ban_group(chat_id, reason=""):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE groups SET is_banned=1,ban_reason=? WHERE chat_id=?", (reason, chat_id))
    conn.commit(); conn.close()

def unban_group(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE groups SET is_banned=0,ban_reason='' WHERE chat_id=?", (chat_id,))
    conn.commit(); conn.close()

def is_banned(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT is_banned FROM groups WHERE chat_id=?", (chat_id,))
    row = c.fetchone(); conn.close()
    return row and row[0] == 1

def get_all_groups():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT chat_id,title,username,member_count,added_date,is_banned,ban_reason FROM groups")
    rows = c.fetchall(); conn.close(); return rows

def get_stats():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM groups WHERE is_banned=0"); active = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM groups WHERE is_banned=1"); banned = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages"); total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages WHERE date >= date('now')"); today = c.fetchone()[0]
    conn.close(); return active, banned, total, today

def log_message(chat_id, user_id, username):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO messages (chat_id,user_id,username,date) VALUES (?,?,?,?)",
              (chat_id, user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()


# ═══════════════════════════════════════════════════════
#                    🛠️ YORDAMCHILAR
# ═══════════════════════════════════════════════════════
logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def is_admin(uid): return uid in ADMIN_IDS

def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistika",   callback_data="stats"),
         InlineKeyboardButton("👥 Guruhlar",     callback_data="groups_0")],
        [InlineKeyboardButton("🚫 Taqiqlangan",  callback_data="banned"),
         InlineKeyboardButton("⚙️ Sozlamalar",  callback_data="settings")],
        [InlineKeyboardButton("📢 Broadcast",    callback_data="broadcast_ask")],
        [InlineKeyboardButton("🔴 Efir holati",  callback_data="live_status")],
    ])

def user_kb(bot_username):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Guruhga qo'shish", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("❓ Qo'shilmadimi? — Qo'llanma", callback_data="how_to_add")],
        [InlineKeyboardButton("🆘 Adminga yozish", callback_data="contact_admin")],
    ])


# ═══════════════════════════════════════════════════════
#               🔴 JONLI EFIR FUNKSIYALARI
# ═══════════════════════════════════════════════════════
async def start_video_chat(bot: Bot, chat_id: int = None) -> bool:
    """Guruhda yangi jonli efir yaratadi. chat_id=None bo'lsa BARCHA guruhlarda yoqadi."""
    targets = [chat_id] if chat_id else LIVE_GROUP_IDS
    all_ok = True
    for gid in targets:
        try:
            await bot.create_video_chat(
                chat_id=gid,
                title=LIVE_TITLE,
                is_broadcast=True,
            )
            logger.info(f"✅ Jonli efir yoqildi: {gid}")
        except TelegramError as e:
            if "VOICE_CHAT_ALREADY_STARTED" in str(e) or "already" in str(e).lower():
                logger.info(f"ℹ️  Allaqachon yoqiq: {gid}")
            else:
                logger.error(f"❌ Xato ({gid}): {e}")
                all_ok = False
    return all_ok


async def monitor_live_stream(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Har CHECK_INTERVAL sekundda BARCHA guruhlarda jonli efirni tekshiradi."""
    if context.bot_data.get("live_paused", False):
        return
    bot: Bot = context.bot
    for gid in LIVE_GROUP_IDS:
        try:
            chat = await bot.get_chat(gid)
        except TelegramError as e:
            logger.error(f"Chat ma'lumotini olishda xato ({gid}): {e}")
            continue
        video_chat = getattr(chat, "video_chat_started", None)
        if video_chat is None:
            logger.warning(f"⚠️  Jonli efir yoqiq emas ({gid})! Qayta yoqilmoqda...")
            try:
                await bot.create_video_chat(chat_id=gid, title=LIVE_TITLE, is_broadcast=True)
                await bot.send_message(chat_id=gid, text="🔴 Jonli efir avtomatik qayta yoqildi!")
                logger.info(f"✅ Yoqildi: {gid}")
            except TelegramError as e:
                if "already" not in str(e).lower():
                    logger.error(f"❌ Yoqishda xato ({gid}): {e}")
        else:
            logger.info(f"✅ Jonli efir faol: {gid}")


async def on_video_chat_ended(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Jonli efir o'chib ketganda darhol o'sha guruhda qayta yoqadi."""
    if context.bot_data.get("live_paused", False):
        return
    chat_id = update.effective_chat.id
    if chat_id not in LIVE_GROUP_IDS:
        return
    logger.warning(f"🔴 Jonli efir o'chdi ({chat_id})! Darhol qayta yoqilmoqda...")
    await asyncio.sleep(3)
    await start_video_chat(context.bot, chat_id=chat_id)


# ── Jonli efir buyruqlari (faqat adminlar uchun) ────────

async def cmd_start_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bu buyruq faqat adminlar uchun!")
        return
    await update.message.reply_text("⏳ Jonli efir yoqilmoqda...")
    success = await start_video_chat(context.bot)
    if success:
        context.bot_data["live_paused"] = False
        await update.message.reply_text("✅ Jonli efir yoqildi! Monitoring faol.")
    else:
        await update.message.reply_text(
            "❌ Jonli efirni yoqib bo'lmadi.\n"
            "Bot guruhda admin ekanligini va 'Manage Video Chats' ruxsati borligini tekshiring."
        )

async def cmd_stop_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bu buyruq faqat adminlar uchun!")
        return
    context.bot_data["live_paused"] = True
    stopped = []
    for gid in LIVE_GROUP_IDS:
        try:
            await context.bot.end_video_chat(gid)
            stopped.append(str(gid))
        except TelegramError:
            pass
    await update.message.reply_text(
        f"⛔ Jonli efir o'chirildi ({len(stopped)} guruh). Monitoring to'xtatildi.\n"
        "Qayta yoqish uchun: /resume_live"
    )

async def cmd_resume_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bu buyruq faqat adminlar uchun!")
        return
    context.bot_data["live_paused"] = False
    await update.message.reply_text("▶️ Monitoring qayta boshlandi!")
    await start_video_chat(context.bot)

async def cmd_live_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    paused = context.bot_data.get("live_paused", False)
    monitoring = "⏸ To'xtatilgan" if paused else "✅ Ishlayapti"
    lines = [f"📊 <b>Jonli Efir Holati</b>\n👁 Monitoring: {monitoring}\n"]
    for i, gid in enumerate(LIVE_GROUP_IDS, 1):
        try:
            chat = await context.bot.get_chat(gid)
            vc = getattr(chat, "video_chat_started", None)
            efir = "🔴 Faol" if vc else "⚫ Faol emas"
            title = chat.title or str(gid)
        except Exception:
            efir = "❓ Noma'lum"; title = str(gid)
        lines.append(f"{i}. <b>{title}</b>\n   Efir: {efir}\n   ID: <code>{gid}</code>")
    lines.append(f"\n⏱ Interval: {CHECK_INTERVAL} sekund")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════
#                     📨 ASOSIY HANDLERLAR
# ═══════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private": return
    user = update.effective_user
    bot_info = await context.bot.get_me()

    if is_admin(user.id):
        active, banned, total, today = get_stats()
        paused = context.bot_data.get("live_paused", False)
        live_icon = "⏸" if paused else "🔴"
        live_text = "To'xtatilgan" if paused else "Faol"
        await update.message.reply_text(
            f"👑 Xush kelibsiz, <b>{user.first_name}</b>!\n\n"
            f"🤖 <b>{BOT_NAME}</b> — Admin Panel\n\n"
            "📊 <b>Hozirgi holat:</b>\n"
            f"  ✅ Faol guruhlar:   <b>{active}</b>\n"
            f"  🚫 Taqiqlangan:     <b>{banned}</b>\n"
            f"  💬 Jami xabarlar:   <b>{total}</b>\n"
            f"  📅 Bugun:           <b>{today}</b>\n"
            f"  {live_icon} Jonli efir monitoring: <b>{live_text}</b>\n\n"
            "👇 Boshqarish uchun tugmani bosing:",
            parse_mode=ParseMode.HTML, reply_markup=admin_kb()
        )
    else:
        await update.message.reply_text(
            f"✨ <b>Assalomu alaykum, {user.first_name}!</b>\n\n"
            f"🤖 Men <b>{BOT_NAME}</b>man!\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎯 <b>Nima qila olaman?</b>\n"
            "  💬 Salomlashuvlarga alik olaman\n"
            "  🗣 Savollarga avtomatik javob beraman\n"
            "  🤝 Guruh a'zolari bilan muloqot qilaman\n"
            "  🎉 Yangi a'zolarni kutib olaman\n"
            "  🔴 Guruhda 24/7 jonli efir yoqib turaman\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 <b>Quyidan birini tanlang:</b>",
            parse_mode=ParseMode.HTML, reply_markup=user_kb(bot_info.username)
        )

async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(
        f"🛠 <b>Admin Panel</b> — {BOT_NAME}",
        parse_mode=ParseMode.HTML, reply_markup=admin_kb()
    )

async def track_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = update.my_chat_member
    if not r: return
    chat = r.chat
    status = r.new_chat_member.status
    if status in (ChatMember.MEMBER, ChatMember.ADMINISTRATOR):
        if chat.type in ("group", "supergroup"):
            add_group(chat.id, chat.title, chat.username)
            logger.info(f"✅ Qo'shildi: {chat.title} ({chat.id})")
    elif status in (ChatMember.LEFT, ChatMember.BANNED):
        logger.info(f"❌ Chiqarildi: {chat.title} ({chat.id})")

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot: continue
        name = member.first_name
        mn = f'<a href="tg://user?id={member.id}">{name}</a>'
        greets = [
            f"🎉 Xush kelibsiz {mn}! Bu guruhga qo'shilganingizdan xursandmiz! 😊🌟",
            f"👋 Salom {mn}! Guruhimizga xush kelibsiz! Yaxshi vaqt o'tkazing! 🎊",
            f"🌟 {mn}, guruhimizga marhamat! Yoqimli muhit yaratishda yordam bering! 😄",
            f"✨ {mn} bilan guruh yanada jonlandi! Xush kelibsiz! 🎉💫",
            f"💫 Xush kelibsiz {mn}! Savollaringiz bo'lsa bemalol so'rang! 😊",
        ]
        await update.message.reply_text(random.choice(greets), parse_mode=ParseMode.HTML)

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg  = update.message
    if not user or not msg or chat.type not in ("group", "supergroup"): return
    if is_banned(chat.id): return
    add_group(chat.id, chat.title, chat.username)
    log_message(chat.id, user.id, user.username or user.first_name)
    text = msg.text or ""
    if not text: return
    reply = get_auto_reply(text, user.first_name)
    if reply:
        await msg.reply_text(reply, parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════
#        📲 KONTAKT TANLASH — TAKLIF FUNKSIYASI (YANGI!)
# ═══════════════════════════════════════════════════════

async def send_contact_select_keyboard(update_or_query, context, gid: int, user):
    """
    Foydalanuvchiga kontakt tanlash uchun ReplyKeyboardMarkup yuboradi.
    Bu Telegram'ning native "do'stni tanlash" UI'ini ochadi.
    Keyin shu kontaktga taklif havolasi yuboriladi.
    """
    # Pending holatga saqlaymiz
    pending_invite[user.id] = gid

    # Kontakt ulashish tugmasi — Telegram native UI ochadi
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton(
            "👤 Do'st tanlash",
            request_user=True,  # Telegram kontakt/foydalanuvchi tanlash oynasini ochadi
        )]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    # Avval taklif havolasini tayyorlab qo'yamiz
    try:
        link_obj = await context.bot.create_chat_invite_link(
            chat_id=gid,
            name=f"Taklif_{user.id}_{int(datetime.now().timestamp())}",
        )
        link_str = link_obj.invite_link
        invite_links_db[link_str] = (user.id, user.first_name, gid)
        # Link'ni user_data'ga saqlaymiz
        context.user_data[f"invite_link_{gid}"] = link_str
    except TelegramError as e:
        logger.error(f"Invite link yaratishda xato: {e}")
        link_str = None

    # Taklif xabari matni
    if link_str:
        share_url = (
            f"https://t.me/share/url"
            f"?url={link_str}"
            f"&text=Assalom!+Guruhimizga+qo%27shiling+%F0%9F%91%8B"
        )

        # Foydalanuvchi xabar yuborgan joyga qarab javob beramiz
        if hasattr(update_or_query, "message") and update_or_query.message:
            # CallbackQuery
            await update_or_query.message.reply_text(
                "🔗 <b>Sizning shaxsiy taklif havolangiz tayyor!</b>\n\n"
                "👇 Quyidagi tugmalardan birini tanlang:\n\n"
                "1️⃣ <b>Do'st tanlash</b> — Telegramdagi do'stingizni belgilang\n"
                "2️⃣ <b>Havola ulashish</b> — Linkni yuborib taklif qiling\n\n"
                "Kimni qo'shsangiz, bot sizni ommaviy maqtaydi! 🎉",
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            # Inline havola tugmasini ham qo'shamiz
            await update_or_query.message.reply_text(
                "📤 Yoki havola orqali taklif qiling:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📤 Havola ulashish", url=share_url)
                ]])
            )
        else:
            await update_or_query.reply_text(
                "🔗 <b>Taklif havolangiz tayyor!</b>\n\n"
                "👇 Do'stingizni tanlang yoki havolani yuboring:",
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
            await update_or_query.reply_text(
                "📤 Havola orqali taklif qiling:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📤 Havola ulashish", url=share_url)
                ]])
            )
    else:
        err_msg = "❌ Havola yaratishda xato. Bot guruhda admin ekanligini tekshiring."
        if hasattr(update_or_query, "message") and update_or_query.message:
            await update_or_query.message.reply_text(err_msg)
        else:
            await update_or_query.reply_text(err_msg)


async def handle_user_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Foydalanuvchi kontakt tanlaganda ishlaydi.
    Tanlangan foydalanuvchiga taklif havolasini forward qiladi.
    """
    msg = update.message
    user = update.effective_user
    if not msg or not hasattr(msg, "user_shared") or not msg.user_shared:
        return

    selected_user_id = msg.user_shared.user_id
    gid = pending_invite.pop(user.id, None)

    if not gid:
        await msg.reply_text(
            "⚠️ Taklif sessiyasi tugagan. Iltimos qayta \"➕ Taklif qilish\" tugmasini bosing.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Saqlangan havolani olamiz
    link_str = context.user_data.get(f"invite_link_{gid}")

    if link_str:
        share_url = (
            f"https://t.me/share/url"
            f"?url={link_str}"
            f"&text=Assalom!+Guruhimizga+qo%27shiling+%F0%9F%91%8B"
        )
        # Tanlangan foydalanuvchiga to'g'ridan-to'g'ri xabar yuborishga harakat
        try:
            await context.bot.send_message(
                chat_id=selected_user_id,
                text=(
                    f"👋 Assalomu alaykum!\n\n"
                    f"<b>{user.first_name}</b> sizni guruhga taklif qilmoqda! 🎉\n\n"
                    f"🔗 Quyidagi havola orqali qo'shiling:"
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Guruhga qo'shilish", url=link_str)
                ]])
            )
            await msg.reply_text(
                f"✅ <b>Do'stingizga taklif yuborildi!</b>\n\n"
                f"Agar u qo'shilsa, bot sizni maqtaydi! 🎊",
                parse_mode=ParseMode.HTML,
                reply_markup=ReplyKeyboardRemove()
            )
        except TelegramError:
            # Bot o'sha odamga yoza olmasa — share URL orqali
            await msg.reply_text(
                "📤 Do'stingizga bu havolani yuboring:",
                reply_markup=ReplyKeyboardRemove()
            )
            await msg.reply_text(
                f"🔗 {link_str}\n\n"
                f"Yoki tugma orqali ulashing:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📤 Havola ulashish", url=share_url)
                ]])
            )
    else:
        await msg.reply_text(
            "❌ Havola topilmadi. Iltimos qayta urinib ko'ring.",
            reply_markup=ReplyKeyboardRemove()
        )


async def handle_admin_pm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id) or update.effective_chat.type != "private": return
    action = context.user_data.get("action")
    text = update.message.text or ""

    if action == "ban_id":
        try:
            cid = int(text.strip())
            ban_group(cid, "Admin tomonidan taqiqlandi")
            context.user_data.pop("action", None)
            await update.message.reply_text(
                f"✅ Guruh <code>{cid}</code> taqiqlandi!",
                parse_mode=ParseMode.HTML, reply_markup=admin_kb())
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID! Raqam kiriting.")
    elif action == "unban_id":
        try:
            cid = int(text.strip())
            unban_group(cid)
            context.user_data.pop("action", None)
            await update.message.reply_text(
                f"✅ Guruh <code>{cid}</code> tiklandi!",
                parse_mode=ParseMode.HTML, reply_markup=admin_kb())
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID!")
    elif action == "broadcast":
        groups = [g for g in get_all_groups() if g[5] == 0]
        sent = failed = 0
        for g in groups:
            try:
                await context.bot.send_message(
                    g[0], f"📢 <b>E'lon:</b>\n\n{text}", parse_mode=ParseMode.HTML)
                sent += 1
            except Exception:
                failed += 1
        context.user_data.pop("action", None)
        await update.message.reply_text(
            f"📢 <b>Yuborildi!</b>\n✅ Muvaffaqiyatli: <b>{sent}</b>\n❌ Xato: <b>{failed}</b>",
            parse_mode=ParseMode.HTML, reply_markup=admin_kb())


# ═══════════════════════════════════════════════════════
#                📢 TAKLIF XABARI FUNKSIYALARI
# ═══════════════════════════════════════════════════════

async def send_group_invite_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Har INVITE_INTERVAL sekundda guruhlarga taklif xabari yuboradi."""
    for gid in LIVE_GROUP_IDS:
        try:
            await context.bot.send_message(
                chat_id=gid,
                text=INVITE_MESSAGE,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "➕ Taklif qilish",
                        callback_data=f"invite_{gid}"
                    )
                ]])
            )
            logger.info(f"📢 Taklif xabari yuborildi: {gid}")
        except Exception as e:
            logger.error(f"Taklif xabarini yuborishda xato ({gid}): {e}")


async def track_new_member_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yangi a'zo qo'shilganda, uni kim taklif qilganini aniqlaydi va minnatdorlik bildiradi."""
    result = update.chat_member
    if not result:
        return

    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status

    if old_status in (ChatMember.LEFT, ChatMember.BANNED) and \
       new_status in (ChatMember.MEMBER, ChatMember.ADMINISTRATOR):

        new_member = result.new_chat_member.user
        chat_id    = result.chat.id
        invite_link_used = getattr(result, "invite_link", None)

        if invite_link_used and hasattr(invite_link_used, "invite_link"):
            link_str = invite_link_used.invite_link
            if link_str in invite_links_db:
                inviter_id, inviter_name, _ = invite_links_db[link_str]
                inviter_mention = f'<a href="tg://user?id={inviter_id}">{inviter_name}</a>'
                new_mention     = f'<a href="tg://user?id={new_member.id}">{new_member.first_name}</a>'
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"🎉 Rahmat birodar {inviter_mention}!\n\n"
                            f"Siz <b>{new_mention}</b>ni guruhga qo'shdingiz! 🤝\n"
                            f"Barakalla, guruh kengaymoqda! 💪🌟"
                        ),
                        parse_mode=ParseMode.HTML,
                    )
                except Exception as e:
                    logger.error(f"Taklif minnatdorlik xabarida xato: {e}")


# ═══════════════════════════════════════════════════════
#                   🔘 CALLBACK HANDLERLAR
# ═══════════════════════════════════════════════════════
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query
    await q.answer()
    d   = q.data
    uid = q.from_user.id
    bot_info = await context.bot.get_me()

    # ── FOYDALANUVCHI ──
    if d == "how_to_add":
        await q.edit_message_text(
            "📖 <b>Botni guruhga qo'shish — 5 qadam</b>\n\n"
            "1️⃣ Quyidagi <b>«Guruhga qo'shish»</b> tugmasini bosing\n"
            "2️⃣ Ro'yxatdan guruhingizni tanlang\n"
            "3️⃣ <b>«Bot qo'shish»</b> tugmasini tasdiqlang\n\n"
            "4️⃣ Guruh sozlamalari → <b>Adminlar</b>ga kiring\n"
            "5️⃣ Botni toping → <b>Barcha ruxsatlarni bering ✓</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <b>Muhim:</b> Bot admin bo'lmasa xabarlarni "
            "o'qiy olmaydi va javob bera olmaydi!\n\n"
            "✅ Shundan so'ng bot to'liq ishlaydi! 🎉",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Guruhga qo'shish",
                    url=f"https://t.me/{bot_info.username}?startgroup=true")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_user")],
            ])
        ); return

    if d == "contact_admin":
        await q.edit_message_text(
            "🆘 <b>Yordam kerakmi?</b>\n\n"
            "📩 Adminga to'g'ridan-to'g'ri murojaat qiling!\n\n"
            "✅ Admin xabaringizni ko'radi\n"
            "⏰ Javob vaqti: <b>24 soat ichida</b>\n\n"
            "👇 Quyidagi tugmani bosib yozing:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 Adminga yozish",
                    url=f"tg://user?id={ADMIN_IDS[0]}")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_user")],
            ])
        ); return

    if d == "back_user":
        await q.edit_message_text(
            f"✨ <b>🤖 {BOT_NAME}</b>\n\n👇 Quyidagi tugmalardan birini tanlang:",
            parse_mode=ParseMode.HTML, reply_markup=user_kb(bot_info.username)
        ); return

    # ── TAKLIF TUGMASI — YANGILANGAN (kontakt tanlash UI) ──
    if d.startswith("invite_"):
        gid = int(d.split("_")[1])
        user = q.from_user
        await send_contact_select_keyboard(q, context, gid, user)
        return

    # ── ADMIN ──
    if not is_admin(uid):
        await q.edit_message_text("❌ Ruxsat yo'q!"); return

    if d == "stats":
        active, banned, total, today = get_stats()
        await q.edit_message_text(
            "📊 <b>Bot Statistikasi</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Faol guruhlar:    <b>{active}</b>\n"
            f"🚫 Taqiqlangan:      <b>{banned}</b>\n"
            f"📊 Jami guruhlar:    <b>{active + banned}</b>\n\n"
            f"💬 Jami xabarlar:    <b>{total}</b>\n"
            f"📅 Bugungi xabarlar: <b>{today}</b>\n\n"
            f"🕐 <i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")
            ]]))

    elif d == "live_status":
        paused = context.bot_data.get("live_paused", False)
        monitoring = "⏸ To'xtatilgan" if paused else "✅ Ishlayapti"
        lines = [f"🔴 <b>Jonli Efir Holati</b>\n━━━━━━━━━━━━━━━━━━━━\n👁 Monitoring: {monitoring}\n"]
        for i, gid in enumerate(LIVE_GROUP_IDS, 1):
            try:
                chat = await context.bot.get_chat(gid)
                vc = getattr(chat, "video_chat_started", None)
                efir = "🔴 Faol" if vc else "⚫ Faol emas"
                title = chat.title or str(gid)
            except Exception:
                efir = "❓ Noma'lum"; title = str(gid)
            lines.append(f"{i}. <b>{title}</b>\n   {efir} | <code>{gid}</code>")
        lines.append(f"\n⏱ Interval: {CHECK_INTERVAL} sekund")
        toggle_label = "▶️ Monitoringni yoqish" if paused else "⏸ Monitoringni to'xtatish"
        toggle_data  = "live_resume_cb" if paused else "live_pause_cb"
        await q.edit_message_text(
            "\n".join(lines),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔴 Barchasini Yoq",   callback_data="live_start_cb"),
                 InlineKeyboardButton("⛔ Barchasini O'chir", callback_data="live_stop_cb")],
                [InlineKeyboardButton(toggle_label, callback_data=toggle_data)],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")],
            ]))

    elif d == "live_start_cb":
        success = await start_video_chat(context.bot)
        context.bot_data["live_paused"] = False
        msg = "✅ Jonli efir yoqildi! Monitoring faol." if success else "❌ Yoqib bo'lmadi. Ruxsatlarni tekshiring."
        await q.edit_message_text(msg,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="live_status")
            ]]))

    elif d == "live_stop_cb":
        context.bot_data["live_paused"] = True
        for gid in LIVE_GROUP_IDS:
            try:
                await context.bot.end_video_chat(gid)
            except TelegramError:
                pass
        await q.edit_message_text(
            f"⛔ {len(LIVE_GROUP_IDS)} ta guruhda jonli efir o'chirildi. Monitoring to'xtatildi.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="live_status")
            ]]))

    elif d == "live_pause_cb":
        context.bot_data["live_paused"] = True
        await q.edit_message_text("⏸ Monitoring to'xtatildi.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="live_status")
            ]]))

    elif d == "live_resume_cb":
        context.bot_data["live_paused"] = False
        await start_video_chat(context.bot)
        await q.edit_message_text("▶️ Monitoring qayta boshlandi! Jonli efir yoqilmoqda...",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="live_status")
            ]]))

    elif d.startswith("groups_"):
        page   = int(d.split("_")[1])
        groups = [g for g in get_all_groups() if g[5] == 0]
        per_page = 5
        pg = groups[page * per_page:(page + 1) * per_page]
        if not groups:
            text = "👥 Hech qanday faol guruh yo'q."
        else:
            text = f"👥 <b>Faol Guruhlar</b> — {len(groups)} ta\n━━━━━━━━━━━━━━━━━━━━\n\n"
            for g in pg:
                cid, title, uname, _, added, _, _ = g
                un = f"@{uname}" if uname else "—"
                text += f"📌 <b>{title}</b>\n   🆔 <code>{cid}</code>  🔗 {un}\n   📅 {added}\n\n"
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️", callback_data=f"groups_{page-1}"))
        if (page+1)*per_page < len(groups):
            nav.append(InlineKeyboardButton("➡️", callback_data=f"groups_{page+1}"))
        rows = []
        if nav: rows.append(nav)
        rows += [
            [InlineKeyboardButton("🚫 Guruh taqiqlash", callback_data="ask_ban")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")],
        ]
        await q.edit_message_text(text, parse_mode=ParseMode.HTML,
                                   reply_markup=InlineKeyboardMarkup(rows))

    elif d == "banned":
        groups = [g for g in get_all_groups() if g[5] == 1]
        if not groups:
            text = "✅ Taqiqlangan guruhlar yo'q!"
        else:
            text = f"🚫 <b>Taqiqlangan Guruhlar</b> — {len(groups)} ta\n━━━━━━━━━━━━━━━━━━━━\n\n"
            for g in groups:
                cid, title, _, _, added, _, reason = g
                text += f"🔴 <b>{title}</b>\n   🆔 <code>{cid}</code>\n   📝 {reason or '—'}\n\n"
        await q.edit_message_text(text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Guruhni tiklash", callback_data="ask_unban")],
                [InlineKeyboardButton("🔙 Orqaga",          callback_data="back_admin")],
            ]))

    elif d == "settings":
        total_words   = len(RESPONSES)
        total_replies = sum(len(v) for v in RESPONSES.values())
        paused = context.bot_data.get("live_paused", False)
        live_status_text = "To'xtatilgan" if paused else "Faol"
        await q.edit_message_text(
            "⚙️ <b>Bot Sozlamalari</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 Kalit so'zlar:    <b>{total_words}</b>\n"
            f"📝 Jami javoblar:    <b>{total_replies}</b>\n\n"
            f"🤖 Bot nomi:         <b>{BOT_NAME}</b>\n"
            f"👑 Adminlar:         <b>{len(ADMIN_IDS)}</b>\n\n"
            f"🔴 Live monitoring:  <b>{live_status_text}</b>\n"
            f"📡 Kuzatiladigan guruhlar: <b>{len(LIVE_GROUP_IDS)} ta</b>\n"
            f"⏱ Tekshirish vaqti: <b>{CHECK_INTERVAL} sek</b>\n\n"
            "⚡ Barcha funksiyalar <b>faol</b>!\n\n"
            "💡 <i>Yangi so'z qo'shish uchun RESPONSES lug'atini tahrirlang</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")
            ]]))

    elif d == "broadcast_ask":
        context.user_data["action"] = "broadcast"
        groups = [g for g in get_all_groups() if g[5] == 0]
        await q.edit_message_text(
            f"📢 <b>Broadcast</b>\n\n"
            f"📊 Guruhlar soni: <b>{len(groups)}</b>\n\n"
            "✍️ Yuboriladigan xabarni yozing:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")
            ]]))

    elif d == "ask_ban":
        context.user_data["action"] = "ban_id"
        await q.edit_message_text(
            "🚫 <b>Guruh taqiqlash</b>\n\nGuruh <b>ID</b>sini yuboring:\n<i>Misol: -1001234567890</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Bekor", callback_data="groups_0")
            ]]))

    elif d == "ask_unban":
        context.user_data["action"] = "unban_id"
        await q.edit_message_text(
            "✅ <b>Guruhni tiklash</b>\n\nGuruh <b>ID</b>sini yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Bekor", callback_data="banned")
            ]]))

    elif d == "back_admin":
        active, banned, total, today = get_stats()
        await q.edit_message_text(
            f"🛠 <b>Admin Panel</b> — {BOT_NAME}\n\n"
            f"✅ Faol: <b>{active}</b>  •  🚫 Taqiqlangan: <b>{banned}</b>  •  💬 Xabarlar: <b>{total}</b>",
            parse_mode=ParseMode.HTML, reply_markup=admin_kb())


# ═══════════════════════════════════════════════════════
#                    🚀 ISHGA TUSHIRISH
# ═══════════════════════════════════════════════════════
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # ── Komandalar ──
    app.add_handler(CommandHandler("start",        cmd_start))
    app.add_handler(CommandHandler("panel",        cmd_panel))
    app.add_handler(CommandHandler("start_live",   cmd_start_live))
    app.add_handler(CommandHandler("stop_live",    cmd_stop_live))
    app.add_handler(CommandHandler("resume_live",  cmd_resume_live))
    app.add_handler(CommandHandler("live_status",  cmd_live_status))

    # ── Guruh hodisalari ──
    app.add_handler(ChatMemberHandler(track_bot, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(track_new_member_invite, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # ── Jonli efir o'chganda ushlash ──
    app.add_handler(MessageHandler(
        filters.StatusUpdate.VIDEO_CHAT_ENDED,
        on_video_chat_ended
    ))

    # ── Kontakt tanlash (user_shared) handler — YANGI ──
    # Foydalanuvchi "Do'st tanlash" tugmasidan biror odamni tanlaganda ishlaydi
    app.add_handler(MessageHandler(
        filters.StatusUpdate.USER_SHARED,
        handle_user_shared
    ))

    # ── Callback va xabarlar ──
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
        handle_admin_pm))
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
        handle_group_message))

    # ── 24/7 Jonli efir monitoring (har CHECK_INTERVAL sekundda) ──
    app.job_queue.run_repeating(
        monitor_live_stream,
        interval=CHECK_INTERVAL,
        first=15,
    )

    # ── Har INVITE_INTERVAL sekundda taklif xabari ──
    app.job_queue.run_repeating(
        send_group_invite_message,
        interval=INVITE_INTERVAL,
        first=20,
    )

    logger.info(f"🚀 {BOT_NAME} ishga tushdi!")
    logger.info(f"🔴 Jonli efir monitoring: {len(LIVE_GROUP_IDS)} ta guruh, har {CHECK_INTERVAL} sekund")
    logger.info(f"📢 Taklif xabari: har {INVITE_INTERVAL} sekund")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
