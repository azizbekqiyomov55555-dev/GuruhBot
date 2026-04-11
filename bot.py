# ╔══════════════════════════════════════════════════════════════════╗
# ║        🤖 YORDAMCHI BOT — TO'LIQ FINAL VERSIYA v3              ║
# ║   ✅ Pyrogram (MTProto) + python-telegram-bot birga             ║
# ║   🔴 Jonli efir Pyrogram orqali yoqiladi (100% ishonchli)      ║
# ╚══════════════════════════════════════════════════════════════════╝
#
# 💡 ISHGA TUSHIRISH:
#   pip install pyrogram tgcrypto python-telegram-bot==20.7
#
# ⚙️ SOZLASH (bir marta):
#   1. https://my.telegram.org → API development tools
#   2. App title: GuruhBot, Platform: Other
#   3. API_ID va API_HASH ni oling → quyida yozing
#   4. PHONE_NUMBER — botingiz bilan ADMIN bo'lgan akkaunt raqami
#
# ⚙️ BOT SOZLAMALARI (@BotFather):
#   1. Bot Settings → Group Privacy → DISABLE
#   2. Botni guruhga ADMIN qiling
#   3. Admin ruxsatlari: ✅ Manage Video Chats, ✅ Invite Users
#   4. Bot Settings → Allow Groups → ✅

import logging
import sqlite3
import asyncio
import random
import urllib.parse
from datetime import datetime

# ── Pyrogram (MTProto — jonli efir uchun) ───────────────
from pyrogram import Client as PyroClient
from pyrogram.errors import FloodWait, ChatAdminRequired, RPCError

# ── python-telegram-bot (bot funksiyalari uchun) ────────
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember, Bot
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
BOT_TOKEN    = "8780908767:AAEewN-jTc2_19hUZRu9mf-qudBTKM2A8Gk"
ADMIN_IDS    = [8537782289]
BOT_NAME     = "Yordamchi Bot"

# ── Pyrogram sozlamalari (my.telegram.org) ─────────────
API_ID         = 37366974
API_HASH       = "08d09c7ed8b7cb414ed6a99c104f1bd6"
# ✅ Lokal skript bilan olingan string session (PHONE_NUMBER o'rniga)
SESSION_STRING = "AgI6LL4AVCYtJZyPAePI39DYwLzwV74HqiuErGzh52J-0HkfA_ZoW9XZEResoB0T7upL-6kGyXlPX-egXLXsLSxANzQ9zl1b5zfhzHMaNKwtXUI4ly45EO6cv8Mik4TZ9gvqfk7kbWLCP0j83WrsdLj_09qkc9lqyQfxXnQS_yhxwDIeCiMnG0r6QG_nlczylA-WhRtoGoo-1KHq_4KEufih9yl2_xsgiwT66mR3iE9dAgLajnC6W-ZMiL7_aq-iFGTYAuwP7BD6canOmVB5esmSEM8Q9h_QiKLoigP44pK3UZWOJICRdvAm2DaAgFEne0SdVqcdHP_CcpEaNRqgxKlW__bmXQAAAAH85DgRAA"

# ── Guruh ID lari ──────────────────────────────────────
LIVE_GROUP_IDS = [
    -1002823910957,   # asosiy guruh
]

LIVE_TITLE      = "🔴 24/7 Jonli Efir"
CHECK_INTERVAL  = 30
INVITE_INTERVAL = 60

INVITE_MESSAGE = (
    "👋 <b>Assalom aleykum birodarlar!</b>\n\n"
    "👥 Guruhga odam qo'shinlar akalar!\n"
    "Ko'taraylik guruhni! 💪\n\n"
    "Joniyiz sog' bo'lsin! 🤝🌟"
)

# Global Pyrogram client
pyro_app: PyroClient = None
invite_links_db: dict = {}


# ═══════════════════════════════════════════════════════
#           📡 PYROGRAM ORQALI JONLI EFIR (asosiy fix)
# ═══════════════════════════════════════════════════════
async def pyro_create_video_chat(chat_id: int, title: str = "🔴 Jonli Efir") -> bool:
    """
    Pyrogram MTProto orqali jonli efir yaratadi.
    Bu Bot API'dan farqli — haqiqatda ishlaydi!
    """
    global pyro_app
    if pyro_app is None or not pyro_app.is_connected:
        logger.error("❌ Pyrogram ulanmagan!")
        return False
    try:
        await pyro_app.create_video_chat(chat_id, title=title)
        logger.info(f"✅ Pyrogram: Jonli efir yoqildi → {chat_id}")
        return True
    except FloodWait as e:
        logger.warning(f"⏳ FloodWait {e.value} sekund: {chat_id}")
        await asyncio.sleep(e.value)
        try:
            await pyro_app.create_video_chat(chat_id, title=title)
            return True
        except Exception:
            return False
    except RPCError as e:
        err = str(e)
        if "GROUPCALL_ALREADY_STARTED" in err or "already" in err.lower():
            logger.info(f"ℹ️ Allaqachon yoqiq: {chat_id}")
            return True
        logger.error(f"❌ Pyrogram create_video_chat xato ({chat_id}): {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Kutilmagan xato ({chat_id}): {e}")
        return False


async def pyro_end_video_chat(chat_id: int) -> bool:
    """Pyrogram orqali jonli efirni o'chiradi."""
    global pyro_app
    if pyro_app is None or not pyro_app.is_connected:
        return False
    try:
        await pyro_app.end_video_chat(chat_id)
        logger.info(f"✅ Pyrogram: Jonli efir o'chirildi → {chat_id}")
        return True
    except RPCError as e:
        logger.error(f"❌ end_video_chat xato ({chat_id}): {e}")
        return False


async def pyro_is_video_chat_active(chat_id: int) -> bool:
    """Jonli efir holatini Pyrogram orqali tekshiradi."""
    global pyro_app
    if pyro_app is None or not pyro_app.is_connected:
        return False
    try:
        chat = await pyro_app.get_chat(chat_id)
        return chat.video_chat_started is not None
    except Exception as e:
        logger.error(f"❌ get_chat xato ({chat_id}): {e}")
        return False


async def start_all_video_chats() -> dict:
    """Barcha guruhlarda jonli efirni yoqadi. Xato bo'lsa o'tkazib yuboradi."""
    results = {}
    for gid in LIVE_GROUP_IDS:
        try:
            ok = await pyro_create_video_chat(gid, LIVE_TITLE)
            results[gid] = ok
            if ok:
                logger.info(f"✅ Jonli efir yoqildi: {gid}")
            else:
                logger.warning(f"⚠️ Yoqilmadi (ruxsat yo'q?): {gid}")
        except Exception as e:
            logger.error(f"❌ Xato ({gid}): {e}")
            results[gid] = False
        await asyncio.sleep(1)
    return results


# ═══════════════════════════════════════════════════════
#                  💬 AVTOMATIK JAVOBLAR
# ═══════════════════════════════════════════════════════
RESPONSES = {
    "assalomu alaykum": [
        "Va alaykum assalom va rahmatulloh, {name}! 🤲✨",
        "Va alaykum assalom, {name}! Xayrli kun! 😊",
    ],
    "assalom": [
        "Va alaykum assalom, {name}! 🙏😊",
        "Va alaykum {name}! Xayrli kun! ☀️",
        "Assalomu alaykum {name}! Xush kelibsiz! 🌟",
    ],
    "salom": [
        "Va alaykum assalom, {name}! 😊",
        "Salom-salom {name}! Qandaysiz? 😄",
        "Hey {name}, salom! Kayfiyat qanday? 😎",
        "Salom {name}! Bugun ham zo'r kun bo'lsin! ✨",
    ],
    "xayrli tong": [
        "Xayrli tong {name}! ☀️🌸",
        "Tong muborak {name}! ☀️ Omadli kun bo'lsin!",
    ],
    "xayrli kun": [
        "Sizga ham xayrli kun {name}! ☀️😊",
        "Xayrli kun {name}! 🌟 Kayfiyat a'lo bo'lsin!",
    ],
    "xayrli kech": [
        "Xayrli kech {name}! 🌙✨",
        "Xayrli kech {name}! 🌙 Tinch tun bo'lsin!",
    ],
    "xayr": [
        "Xayr {name}! 👋 Eson-omon yuring!",
        "Xayr-xayr {name}! 🌟 Sog' bo'ling!",
    ],
    "hayr": ["Hayr {name}! Ko'rishguncha! 👋"],
    "bye":  ["Bye {name}! Ko'rishguncha! 👋", "See you {name}! 😊"],
    "rahmat": [
        "Arzimaydi {name}! 😊 Doimo xizmatda!",
        "Marhamat {name}! 🌟",
        "Hech gap emas {name}! 👍",
    ],
    "raxmat": ["Arzimaydi {name}! 😊", "Marhamat {name}! 🌟"],
    "qalaysiz": [
        "Yaxshi rahmat! {name}, siz-chi? 😊",
        "Hammasi zo'r {name}! Siz qalaysiz? 😄",
    ],
    "qalay":  ["Yaxshi rahmat {name}! Siz-chi? 😊", "Zo'r! {name}! 💪"],
    "nima gap": [
        "{name}, hech gap yo'q, tinch! 😄",
        "Tinchlik {name}! Nima yangiliklar? 🌟",
    ],
    "zo'r":       ["Ha {name}, rostdan ham zo'r! 💪🔥", "Ajoyib {name}! 🌟"],
    "super":      ["Super-super {name}! 🔥💯", "{name}, juda zo'r! 🌟👏"],
    "barakalla":  ["Barakalla {name}! 👏🌟", "{name}, zo'r! Barakalla! 💫"],
    "ok":         ["Ok {name}! 👍", "Mayli {name}! 😊"],
    "ha":         ["Ha, to'g'ri {name}! 👍", "Albatta {name}! 😊"],
    "omad":       ["Omad tilayman {name}! 🍀💫"],
    "inshalloh":  ["Inshalloh {name}! 🤲🌟"],
    "mashalloh":  ["Mashalloh {name}! 🤲🌟"],
    "alhamdulillah": ["Alhamdulillah {name}! 🤲"],
    "tabrik":     ["Tabriklayman {name}! 🎉🎊", "Muborak bo'lsin {name}! 🎉"],
    "tug'ilgan kun": ["Tug'ilgan kun muborak {name}! 🎂🎉🎊"],
    "❤️":  ["❤️ Rahmat {name}!", "🥰 Siz ham {name}!"],
    "👍":  ["👍 Zo'r {name}!", "✅ Yaxshi {name}!"],
    "🔥":  ["🔥🔥 {name}, zo'r!"],
    "🎉":  ["🎉🎊 {name}, tabriklayman!"],
    "привет": ["Привет {name}! 😊", "Привет-привет {name}! Как дела? 😄"],
    "hello":  ["Hello {name}! 👋 Welcome!", "Hi {name}! Salom! 🌟"],
    "hi":     ["Hi {name}! 👋", "Hey {name}! 😊"],
}

def get_auto_reply(text: str, user_name: str):
    t = text.lower().strip()
    for kw in sorted(RESPONSES, key=len, reverse=True):
        if kw in t:
            return random.choice(RESPONSES[kw]).replace("{name}", user_name)
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
        [InlineKeyboardButton("📊 Statistika",  callback_data="stats"),
         InlineKeyboardButton("👥 Guruhlar",    callback_data="groups_0")],
        [InlineKeyboardButton("🚫 Taqiqlangan", callback_data="banned"),
         InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings")],
        [InlineKeyboardButton("📢 Broadcast",   callback_data="broadcast_ask")],
        [InlineKeyboardButton("🔴 Efir holati", callback_data="live_status")],
    ])

def user_kb(bot_username):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Guruhga qo'shish", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("❓ Qo'llanma",        callback_data="how_to_add")],
        [InlineKeyboardButton("🆘 Adminga yozish",  callback_data="contact_admin")],
    ])


# ═══════════════════════════════════════════════════════
#   👥 A'ZO QO'SHISH — TAKLIF TUGMASI
# ═══════════════════════════════════════════════════════
async def handle_invite_button(query, context: ContextTypes.DEFAULT_TYPE, gid: int):
    user = query.from_user

    try:
        link_obj = await context.bot.create_chat_invite_link(
            chat_id=gid,
            name=f"Inv_{user.id}_{int(datetime.now().timestamp())}",
        )
        link_str = link_obj.invite_link
        invite_links_db[link_str] = (user.id, user.first_name, gid)
    except TelegramError as e:
        logger.error(f"Invite link xato: {e}")
        await query.message.reply_text(
            "❌ Havola yaratishda xato!\n"
            "Bot guruhda ADMIN ekanligini va 'Invite Users' ruxsati borligini tekshiring."
        )
        return

    try:
        chat = await context.bot.get_chat(gid)
        group_title = chat.title or "Guruh"
    except TelegramError:
        group_title = "Guruh"

    # tg://add?slug= — kontaktlardan tanlash oynasini ochadi
    try:
        if "/+" in link_str:
            slug = link_str.split("/+")[-1]
        elif "joinchat/" in link_str:
            slug = link_str.split("joinchat/")[-1]
        else:
            slug = link_str.split("/")[-1].lstrip("+")
        add_members_url = f"tg://add?slug={slug}"
    except Exception:
        add_members_url = link_str

    share_text = (
        f"Assalom! 👋 Men sizni \"{group_title}\" guruhiga taklif qilmoqchiman!\n"
        f"Qo'shiling, zo'r guruh! 💪"
    )
    share_url = (
        f"https://t.me/share/url?"
        f"url={urllib.parse.quote(link_str)}"
        f"&text={urllib.parse.quote(share_text)}"
    )

    await query.message.reply_text(
        f"🔗 <b>{user.first_name}, sizning taklif havolangiz tayyor!</b>\n\n"
        f"📌 Guruh: <b>{group_title}</b>\n\n"
        f"👇 <b>Quyidagilardan birini tanlang:</b>\n\n"
        f"1️⃣ <b>A'zo qo'shish</b> — Telegramdagi kontaktlaringizni ko'rib, "
        f"belgilab, to'g'ridan guruhga qo'shing\n\n"
        f"2️⃣ <b>Havola ulashish</b> — Linkni do'stlaringizga yuboring\n\n"
        f"🎉 Kim qo'shilsa, bot guruhda <b>sizni maqtaydi!</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "👥 A'zo qo'shish (kontaktdan tanlash)",
                url=add_members_url
            )],
            [InlineKeyboardButton(
                "📤 Havola ulashish (do'stlarga yuborish)",
                url=share_url
            )],
        ])
    )


# ═══════════════════════════════════════════════════════
#               🔴 MONITORING VA AUTO-RESTART
# ═══════════════════════════════════════════════════════
async def monitor_live_stream(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Har 30 sekundda jonli efirni tekshiradi, o'chsa qayta yoqadi."""
    if context.bot_data.get("live_paused", False):
        return

    for gid in LIVE_GROUP_IDS:
        try:
            active = await pyro_is_video_chat_active(gid)
        except Exception as e:
            logger.error(f"Tekshirishda xato ({gid}): {e}")
            continue

        if not active:
            logger.warning(f"⚠️ Jonli efir o'chgan ({gid}), qayta yoqilmoqda...")
            try:
                ok = await pyro_create_video_chat(gid, LIVE_TITLE)
                if ok:
                    try:
                        await context.bot.send_message(
                            chat_id=gid,
                            text="🔴 <b>Jonli efir avtomatik qayta yoqildi!</b>\n📡 24/7 ishlaydi!",
                            parse_mode=ParseMode.HTML
                        )
                    except Exception:
                        pass
                else:
                    logger.warning(f"⚠️ Ruxsat yo'q, o'tkazib yuborildi: {gid}")
            except Exception as e:
                logger.error(f"❌ Monitor xato ({gid}): {e}")
        else:
            logger.info(f"✅ Jonli efir faol: {gid}")


async def on_video_chat_ended(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Jonli efir o'chishi bilanoq 3 soniya kutib qayta yoqadi."""
    if context.bot_data.get("live_paused", False):
        return
    chat_id = update.effective_chat.id
    if chat_id not in LIVE_GROUP_IDS:
        return
    logger.warning(f"🔴 Jonli efir O'CHDI ({chat_id})! Qayta yoqilmoqda...")
    await asyncio.sleep(3)
    ok = await pyro_create_video_chat(chat_id, LIVE_TITLE)
    if ok:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🔴 <b>Jonli efir qayta yoqildi!</b> 📡",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass


async def post_init(application: Application) -> None:
    """Bot ishga tushgandan keyin jonli efirni yoqadi."""
    global pyro_app
    logger.info("🔌 Pyrogram ulanmoqda...")
    pyro_app = PyroClient(
        name="guruhbot_session",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING,
    )
    await pyro_app.start()
    logger.info("✅ Pyrogram ulandi!")

    await asyncio.sleep(3)
    logger.info("🔴 Jonli efirlar yoqilmoqda...")
    results = await start_all_video_chats()
    ok = sum(1 for v in results.values() if v)
    logger.info(f"📡 Jonli efir: {ok}/{len(LIVE_GROUP_IDS)} guruhda yoqildi")


async def post_shutdown(application: Application) -> None:
    """Bot to'xtaganda Pyrogram'ni yopadi."""
    global pyro_app
    if pyro_app and pyro_app.is_connected:
        await pyro_app.stop()
        logger.info("✅ Pyrogram to'xtatildi")


# ═══════════════════════════════════════════════════════
#          📢 TAKLIF XABARI
# ═══════════════════════════════════════════════════════
async def send_group_invite_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    for gid in LIVE_GROUP_IDS:
        try:
            await context.bot.send_message(
                chat_id=gid,
                text=INVITE_MESSAGE,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("➕ Taklif qilish", callback_data=f"invite_{gid}")
                ]])
            )
        except Exception as e:
            logger.error(f"Taklif xabari xato ({gid}): {e}")


# ═══════════════════════════════════════════════════════
#     🎉 YANGI A'ZO — KIM TAKLIF QILGANINI ANIQLASH
# ═══════════════════════════════════════════════════════
async def track_new_member_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = update.chat_member
    if not result: return
    old_status = result.old_chat_member.status
    new_status  = result.new_chat_member.status
    if old_status in (ChatMember.LEFT, ChatMember.BANNED) and \
       new_status in (ChatMember.MEMBER, ChatMember.ADMINISTRATOR):
        new_member       = result.new_chat_member.user
        chat_id          = result.chat.id
        invite_link_used = getattr(result, "invite_link", None)
        if invite_link_used and hasattr(invite_link_used, "invite_link"):
            link_str = invite_link_used.invite_link
            if link_str in invite_links_db:
                inviter_id, inviter_name, _ = invite_links_db[link_str]
                inviter_m = f'<a href="tg://user?id={inviter_id}">{inviter_name}</a>'
                new_m     = f'<a href="tg://user?id={new_member.id}">{new_member.first_name}</a>'
                maqtovlar = [
                    f"🎉 <b>BARAKALLA!</b> {inviter_m} birodar {new_m}ni guruhga qo'shdi! 🤝\nGuruh kengaymoqda! 💪🌟",
                    f"👏 <b>ZO'R!</b> {inviter_m} guruhimizga {new_m}ni olib keldi!\nBarakalla! 🔥",
                    f"🌟 {inviter_m} — <b>GURUH QAHRAMONI!</b>\n{new_m}ni qo'shdi! 💪🎊",
                    f"✨ <b>RAHMAT</b> {inviter_m}!\nYangi a'zo {new_m} xush kelibsiz! 🎉",
                ]
                try:
                    await context.bot.send_message(
                        chat_id=chat_id, text=random.choice(maqtovlar), parse_mode=ParseMode.HTML)
                except Exception as e:
                    logger.error(f"Maqtov xabarida xato: {e}")


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
        live_text = "⏸ To'xtatilgan" if paused else "🔴 Faol (24/7)"
        await update.message.reply_text(
            f"👑 Xush kelibsiz, <b>{user.first_name}</b>!\n\n"
            f"🤖 <b>{BOT_NAME}</b> — Admin Panel\n\n"
            f"📊 <b>Holat:</b>\n"
            f"  ✅ Faol guruhlar: <b>{active}</b>\n"
            f"  🚫 Taqiqlangan:   <b>{banned}</b>\n"
            f"  💬 Jami xabarlar: <b>{total}</b>\n"
            f"  📅 Bugun:         <b>{today}</b>\n"
            f"  📡 Jonli efir:    <b>{live_text}</b>\n"
            f"  🏠 Guruhlar:      <b>{len(LIVE_GROUP_IDS)} ta</b>\n\n"
            f"👇 Boshqarish uchun:",
            parse_mode=ParseMode.HTML, reply_markup=admin_kb())
    else:
        await update.message.reply_text(
            f"✨ <b>Assalomu alaykum, {user.first_name}!</b>\n\n"
            f"🤖 Men <b>{BOT_NAME}</b>man!\n\n"
            "🎯 <b>Funksiyalarim:</b>\n"
            "  💬 Salomlashuvlarga javob beraman\n"
            "  🎉 Yangi a'zolarni kutib olaman\n"
            "  🔴 Guruhda 24/7 jonli efir yoqaman\n"
            "  👥 Do'stlaringizni taklif qilishga yordam beraman\n\n"
            "👇 Tanlang:",
            parse_mode=ParseMode.HTML, reply_markup=user_kb(bot_info.username))

async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text("🛠 <b>Admin Panel</b>", parse_mode=ParseMode.HTML, reply_markup=admin_kb())

async def cmd_start_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Faqat adminlar uchun!"); return
    await update.message.reply_text("⏳ Jonli efir yoqilmoqda (2 guruhda)...")
    results = await start_all_video_chats()
    ok  = sum(1 for v in results.values() if v)
    err = sum(1 for v in results.values() if not v)
    text = f"✅ Jonli efir yoqildi!\n\n🟢 Muvaffaqiyat: {ok} ta\n"
    if err: text += f"🔴 Xato: {err} ta (ruxsatlarni tekshiring)\n"
    text += "\n📡 Monitoring faol (har 30 sekund)"
    context.bot_data["live_paused"] = False
    await update.message.reply_text(text)

async def cmd_stop_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Faqat adminlar uchun!"); return
    context.bot_data["live_paused"] = True
    stopped = 0
    for gid in LIVE_GROUP_IDS:
        ok = await pyro_end_video_chat(gid)
        if ok: stopped += 1
    await update.message.reply_text(
        f"⛔ {stopped} ta guruhda jonli efir o'chirildi.\nMonitoring to'xtatildi.\n\nQayta yoqish: /resume_live")

async def cmd_resume_live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Faqat adminlar uchun!"); return
    context.bot_data["live_paused"] = False
    await update.message.reply_text("▶️ Monitoring qayta boshlandi!")
    await start_all_video_chats()

async def track_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = update.my_chat_member
    if not r: return
    chat = r.chat
    status = r.new_chat_member.status
    if status in (ChatMember.MEMBER, ChatMember.ADMINISTRATOR):
        if chat.type in ("group", "supergroup"):
            add_group(chat.id, chat.title, chat.username)
            if chat.id in LIVE_GROUP_IDS and not context.bot_data.get("live_paused", False):
                await asyncio.sleep(5)
                await pyro_create_video_chat(chat.id, LIVE_TITLE)

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot: continue
        mn = f'<a href="tg://user?id={member.id}">{member.first_name}</a>'
        greets = [
            f"🎉 Xush kelibsiz {mn}! Guruhimizga xush kelibsiz! 😊🌟",
            f"👋 Salom {mn}! Guruhimizga marhamat! 🎊",
            f"✨ {mn} bilan guruh yanada jonlandi! Xush kelibsiz! 🎉💫",
            f"💫 Xush kelibsiz {mn}! Savollaringiz bo'lsa so'rang! 😊",
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

async def handle_admin_pm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id) or update.effective_chat.type != "private": return
    action = context.user_data.get("action")
    text = update.message.text or ""
    if action == "ban_id":
        try:
            cid = int(text.strip()); ban_group(cid, "Admin taqiqladi")
            context.user_data.pop("action", None)
            await update.message.reply_text(
                f"✅ Guruh <code>{cid}</code> taqiqlandi!", parse_mode=ParseMode.HTML, reply_markup=admin_kb())
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID!")
    elif action == "unban_id":
        try:
            cid = int(text.strip()); unban_group(cid)
            context.user_data.pop("action", None)
            await update.message.reply_text(
                f"✅ Guruh <code>{cid}</code> tiklandi!", parse_mode=ParseMode.HTML, reply_markup=admin_kb())
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID!")
    elif action == "broadcast":
        groups = [g for g in get_all_groups() if g[5] == 0]
        sent = failed = 0
        for g in groups:
            try:
                await context.bot.send_message(g[0], f"📢 <b>E'lon:</b>\n\n{text}", parse_mode=ParseMode.HTML)
                sent += 1
            except Exception:
                failed += 1
        context.user_data.pop("action", None)
        await update.message.reply_text(
            f"📢 <b>Yuborildi!</b>\n✅ {sent} ta\n❌ {failed} ta",
            parse_mode=ParseMode.HTML, reply_markup=admin_kb())


# ═══════════════════════════════════════════════════════
#                   🔘 CALLBACK HANDLERLAR
# ═══════════════════════════════════════════════════════
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query
    await q.answer()
    d   = q.data
    uid = q.from_user.id
    bot_info = await context.bot.get_me()

    if d.startswith("invite_"):
        gid = int(d.split("_")[1])
        await handle_invite_button(q, context, gid); return

    if d == "how_to_add":
        await q.edit_message_text(
            "📖 <b>Botni guruhga qo'shish</b>\n\n"
            "1️⃣ «Guruhga qo'shish» tugmasini bosing\n"
            "2️⃣ Ro'yxatdan guruhingizni tanlang\n"
            "3️⃣ Tasdiqlang\n"
            "4️⃣ Guruh sozlamalari → Adminlar → Botni toping\n"
            "5️⃣ <b>Barcha ruxsatlarni bering</b> (ayniqsa Video Chats)\n\n"
            "✅ Tayyor! Bot ishlaydi!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Guruhga qo'shish",
                    url=f"https://t.me/{bot_info.username}?startgroup=true")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_user")],
            ])); return

    if d == "contact_admin":
        await q.edit_message_text(
            "🆘 <b>Adminga murojaat</b>\n\n📩 Quyidagi tugmani bosing:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 Adminga yozish", url=f"tg://user?id={ADMIN_IDS[0]}")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_user")],
            ])); return

    if d == "back_user":
        await q.edit_message_text(
            f"✨ <b>🤖 {BOT_NAME}</b>\n\n👇 Tanlang:",
            parse_mode=ParseMode.HTML, reply_markup=user_kb(bot_info.username)); return

    if not is_admin(uid):
        await q.answer("❌ Ruxsat yo'q!", show_alert=True); return

    if d == "stats":
        active, banned, total, today = get_stats()
        await q.edit_message_text(
            "📊 <b>Statistika</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Faol guruhlar:    <b>{active}</b>\n"
            f"🚫 Taqiqlangan:      <b>{banned}</b>\n"
            f"💬 Jami xabarlar:    <b>{total}</b>\n"
            f"📅 Bugun:            <b>{today}</b>\n\n"
            f"🕐 <i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")]]))

    elif d == "live_status":
        paused = context.bot_data.get("live_paused", False)
        monitoring = "⏸ To'xtatilgan" if paused else "✅ Ishlayapti"
        lines = [f"🔴 <b>Jonli Efir Holati</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                 f"👁 Monitoring: {monitoring}\n⏱ Interval: {CHECK_INTERVAL} sek\n"]
        for i, gid in enumerate(LIVE_GROUP_IDS, 1):
            try:
                active = await pyro_is_video_chat_active(gid)
                chat_info = await pyro_app.get_chat(gid) if pyro_app else None
                title = chat_info.title if chat_info else str(gid)
                efir  = "🔴 FAOL" if active else "⚫ O'chiq"
            except Exception:
                efir = "❓ Xato"; title = str(gid)
            lines.append(f"{i}. <b>{title}</b>\n   {efir} | <code>{gid}</code>")
        toggle_label = "▶️ Yoqish" if paused else "⏸ To'xtatish"
        toggle_data  = "live_resume_cb" if paused else "live_pause_cb"
        await q.edit_message_text(
            "\n".join(lines), parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔴 Ikkalasini Yoq",   callback_data="live_start_cb"),
                 InlineKeyboardButton("⛔ Ikkalasini O'chir", callback_data="live_stop_cb")],
                [InlineKeyboardButton(toggle_label, callback_data=toggle_data)],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")],
            ]))

    elif d == "live_start_cb":
        results = await start_all_video_chats()
        context.bot_data["live_paused"] = False
        ok = sum(1 for v in results.values() if v)
        await q.edit_message_text(
            f"✅ Jonli efir yoqildi! ({ok}/{len(LIVE_GROUP_IDS)} guruh)\n📡 Monitoring faol!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="live_status")]]))

    elif d == "live_stop_cb":
        context.bot_data["live_paused"] = True
        stopped = 0
        for gid in LIVE_GROUP_IDS:
            if await pyro_end_video_chat(gid): stopped += 1
        await q.edit_message_text(
            f"⛔ {stopped} ta guruhda jonli efir o'chirildi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="live_status")]]))

    elif d == "live_pause_cb":
        context.bot_data["live_paused"] = True
        await q.edit_message_text("⏸ Monitoring to'xtatildi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="live_status")]]))

    elif d == "live_resume_cb":
        context.bot_data["live_paused"] = False
        await start_all_video_chats()
        await q.edit_message_text("▶️ Monitoring boshlandi! Jonli efir yoqilmoqda...",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="live_status")]]))

    elif d.startswith("groups_"):
        page = int(d.split("_")[1])
        groups = [g for g in get_all_groups() if g[5] == 0]
        per_page = 5
        pg = groups[page * per_page:(page + 1) * per_page]
        text = f"👥 <b>Faol Guruhlar</b> — {len(groups)} ta\n━━━━━━━━━━━━━━━━━━━━\n\n" if groups else "👥 Faol guruh yo'q."
        for g in pg:
            cid, title, uname, _, added, _, _ = g
            un = f"@{uname}" if uname else "—"
            text += f"📌 <b>{title}</b>\n   🆔 <code>{cid}</code>  {un}\n   📅 {added}\n\n"
        nav = []
        if page > 0: nav.append(InlineKeyboardButton("⬅️", callback_data=f"groups_{page-1}"))
        if (page+1)*per_page < len(groups): nav.append(InlineKeyboardButton("➡️", callback_data=f"groups_{page+1}"))
        rows = []
        if nav: rows.append(nav)
        rows += [
            [InlineKeyboardButton("🚫 Guruh taqiqlash", callback_data="ask_ban")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")],
        ]
        await q.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows))

    elif d == "banned":
        groups = [g for g in get_all_groups() if g[5] == 1]
        text = f"🚫 <b>Taqiqlangan</b> — {len(groups)} ta\n\n" if groups else "✅ Taqiqlangan guruh yo'q!"
        for g in groups:
            cid, title, _, _, _, _, reason = g
            text += f"🔴 <b>{title}</b>\n   <code>{cid}</code>\n   📝 {reason or '—'}\n\n"
        await q.edit_message_text(text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Tiklash", callback_data="ask_unban")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")],
            ]))

    elif d == "settings":
        paused = context.bot_data.get("live_paused", False)
        # ✅ TUZATILDI: f-string ichida backslash ishlatilmaydi
        monitoring_status = "To'xtatilgan" if paused else "Faol"
        await q.edit_message_text(
            "⚙️ <b>Bot Sozlamalari</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🤖 Bot nomi:           <b>{BOT_NAME}</b>\n"
            f"👑 Adminlar:           <b>{len(ADMIN_IDS)}</b>\n"
            f"💬 Kalit so'zlar:      <b>{len(RESPONSES)}</b>\n\n"
            f"📡 Jonli efir guruhlar: <b>{len(LIVE_GROUP_IDS)} ta</b>\n"
            f"   1️⃣ <code>-1002823910957</code>\n\n"
            f"🔴 Efir monitoring:    <b>{monitoring_status}</b>\n"
            f"⏱ Tekshirish:         <b>har {CHECK_INTERVAL} sek</b>\n"
            f"📢 Taklif xabari:      <b>har {INVITE_INTERVAL} sek</b>\n\n"
            "⚡ Barcha funksiyalar faol!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")]]))

    elif d == "broadcast_ask":
        context.user_data["action"] = "broadcast"
        groups = [g for g in get_all_groups() if g[5] == 0]
        await q.edit_message_text(
            f"📢 <b>Broadcast</b>\n\nGuruhlar: <b>{len(groups)}</b>\n\n✍️ Xabarni yozing:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))

    elif d == "ask_ban":
        context.user_data["action"] = "ban_id"
        await q.edit_message_text(
            "🚫 Guruh <b>ID</b>sini yuboring:\n<i>Misol: -1001234567890</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="groups_0")]]))

    elif d == "ask_unban":
        context.user_data["action"] = "unban_id"
        await q.edit_message_text(
            "✅ Tiklanadigan guruh <b>ID</b>sini yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="banned")]]))

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
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("panel",       cmd_panel))
    app.add_handler(CommandHandler("start_live",  cmd_start_live))
    app.add_handler(CommandHandler("stop_live",   cmd_stop_live))
    app.add_handler(CommandHandler("resume_live", cmd_resume_live))

    app.add_handler(ChatMemberHandler(track_bot,               ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(track_new_member_invite, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.VIDEO_CHAT_ENDED, on_video_chat_ended))

    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_admin_pm))
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, handle_group_message))

    app.job_queue.run_repeating(monitor_live_stream,      interval=CHECK_INTERVAL,  first=20)
    app.job_queue.run_repeating(send_group_invite_message, interval=INVITE_INTERVAL, first=30)

    logger.info("=" * 60)
    logger.info(f"🚀 {BOT_NAME} ISHGA TUSHDI!")
    logger.info(f"📡 Pyrogram MTProto orqali jonli efir")
    logger.info(f"⏱  Tekshirish: har {CHECK_INTERVAL} sekund")
    logger.info("=" * 60)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
