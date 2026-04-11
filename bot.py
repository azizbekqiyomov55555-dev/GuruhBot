# ╔══════════════════════════════════════════════════════════════════╗
# ║        🤖 YORDAMCHI BOT — VERSIYA v5                           ║
# ║   ✅ Chat ID avtomatik aniqlanadi                               ║
# ║   ✅ Har 2 daqiqada taklif xabari                               ║
# ║   ✅ Taklif qilgan odam maqtaladi (tuzatildi)                   ║
# ║   ✅ Juda ko'p so'zlar va javoblar                              ║
# ╚══════════════════════════════════════════════════════════════════╝
#
# 💡 ISHGA TUSHIRISH:
#   pip install python-telegram-bot==20.7
#
# ⚙️ BOT SOZLAMALARI (@BotFather):
#   1. Bot Settings → Group Privacy → DISABLE
#   2. Botni guruhga ADMIN qiling
#   3. Admin ruxsatlari: ✅ Invite Users, ✅ Add Members
#   4. Bot Settings → Allow Groups → ✅

import logging
import sqlite3
import asyncio
import random
import urllib.parse
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
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
BOT_TOKEN       = "8780908767:AAEewN-jTc2_19hUZRu9mf-qudBTKM2A8Gk"
ADMIN_IDS       = [8537782289]
BOT_NAME        = "Yordamchi Bot"
INVITE_INTERVAL = 120    # har 2 daqiqada (120 sekund)

INVITE_MESSAGE = (
    "👋 <b>Assalom aleykum birodarlar!</b>\n\n"
    "🏆 Do'stlaringizni guruhga taklif qiling!\n"
    "Kim ko'p odam qo'shsa — guruh qahramoni bo'ladi! 💪\n\n"
    "👇 Tugmani bosing va taklif qiling!"
)

# In-memory: invite_link → (user_id, user_name, chat_id)
invite_links_db: dict = {}


# ═══════════════════════════════════════════════════════
#                  💬 AVTOMATIK JAVOBLAR (ko'p so'zlar)
# ═══════════════════════════════════════════════════════
RESPONSES = {
    # ── Salomlashuvlar ──────────────────────────────
    "assalomu alaykum": [
        "Va alaykum assalom va rahmatulloh, {name}! 🤲✨",
        "Va alaykum assalom, {name}! Xayrli kun! 😊",
        "Alaykum assalom {name} aka! Kayfiyat yaxshimi? 🤝",
        "Va alaykum assalom {name}! Xush kelibsiz! 🌟",
    ],
    "assalom": [
        "Va alaykum assalom, {name}! 🙏😊",
        "Va alaykum {name}! Xayrli kun! ☀️",
        "Assalomu alaykum {name}! Xush kelibsiz! 🌟",
        "Salom {name} aka! Qandaysiz? 😄",
        "Hey {name}! Assalom! Kayfiyat zo'rmi? 😎",
    ],
    "salom": [
        "Va alaykum assalom, {name}! 😊",
        "Salom-salom {name}! Qandaysiz? 😄",
        "Hey {name}, salom! Kayfiyat qanday? 😎",
        "Salom {name}! Bugun ham zo'r kun bo'lsin! ✨",
        "Salomlar {name}! Nima gap? 🌟",
        "Salom {name} aka! Yaxshimisiz? 🤝",
    ],
    "салом": [
        "Салом {name}! 😊",
        "Ва алайкум ассалом {name}! 🤲",
    ],
    "привет": [
        "Привет {name}! 😊",
        "Привет-привет {name}! Как дела? 😄",
        "Привет {name}! Salom! 🌟",
    ],
    "hello": [
        "Hello {name}! 👋 Welcome!",
        "Hi {name}! Salom! 🌟",
        "Hello {name}! Glad to see you! 😊",
    ],
    "hi": [
        "Hi {name}! 👋",
        "Hey {name}! 😊",
        "Hi-hi {name}! 🌟",
    ],

    # ── Xayrli vaqt ─────────────────────────────────
    "xayrli tong": [
        "Xayrli tong {name}! ☀️🌸 Omadli kun!",
        "Tong muborak {name}! ☀️",
        "Xayrli tong {name}! Bugun ajoyib kun bo'ladi! 🌅✨",
        "Tong xayrli bo'lsin {name}! ⚡☀️",
    ],
    "xayrli kun": [
        "Sizga ham xayrli kun {name}! ☀️😊",
        "Xayrli kun {name}! 🌟 Kayfiyat a'lo bo'lsin!",
        "Xayrli kun {name}! Hammasi zo'r bo'ladi! 💪",
    ],
    "xayrli kech": [
        "Xayrli kech {name}! 🌙✨",
        "Xayrli kech {name}! 🌙 Tinch tun bo'lsin!",
        "Kech xayrli bo'lsin {name}! Dam oling! 🌙😌",
    ],

    # ── Xayrlashuv ──────────────────────────────────
    "xayr": [
        "Xayr {name}! 👋 Eson-omon yuring!",
        "Xayr-xayr {name}! 🌟 Sog' bo'ling!",
        "Xayr {name}! Ko'rishguncha! 👋💫",
        "Sog'-omon {name}! Qaytib keling! 🤝",
    ],
    "hayr": ["Hayr {name}! Ko'rishguncha! 👋", "Hayr {name}! Eson yuring! 🌟"],
    "bye":  ["Bye {name}! Ko'rishguncha! 👋", "Bye-bye {name}! 🌟"],
    "uxlayman": ["Yaxshi uxlang {name}! 🌙😴", "Tinch uxlang {name}! 🌙✨"],
    "yotaman":  ["Yaxshi dam oling {name}! 🌙", "Tinch uxlang {name}! 🌙✨"],

    # ── Rahmat ──────────────────────────────────────
    "rahmat": [
        "Arzimaydi {name}! 😊 Doimo xizmatda!",
        "Marhamat {name}! 🌟",
        "Hech gap emas {name}! 👍",
        "Xizmat {name}! 😊 Har doim tayyor!",
        "Kerak bo'lsa aytavering {name}! 🤝",
    ],
    "raxmat": [
        "Arzimaydi {name}! 😊",
        "Marhamat {name}! 🌟",
        "Xizmat {name}! 👍",
    ],
    "спасибо": ["Пожалуйста {name}! 😊", "Не за что {name}! 🌟"],

    # ── Ahvol ───────────────────────────────────────
    "qalaysiz": [
        "Yaxshi rahmat! {name}, siz-chi? 😊",
        "Hammasi zo'r {name}! Siz qalaysiz? 😄",
        "Yaxshi alhamdulillah {name}! Siz qalaysiz? 🤲",
        "Juda zo'r {name}! O'zingiz? 💪",
    ],
    "qalaysan": [
        "Yaxshi rahmat {name}! O'zing-chi? 😊",
        "Zo'r {name}! Sen-chi? 😄",
        "Hammasi zo'r {name}! 💪",
    ],
    "qalay": [
        "Yaxshi rahmat {name}! Siz-chi? 😊",
        "Zo'r! {name}! 💪",
        "Yaxshi {name}! O'zingiz? 😄",
    ],
    "yaxshimisiz": [
        "Yaxshi rahmat {name}! Siz ham yaxshimisiz? 😊",
        "Hammasi joyida {name}! 🌟",
    ],
    "yaxshimisan": ["Yaxshi {name}! O'zing-chi? 😊", "Hammasi zo'r {name}! 💪"],

    # ── Savol so'zlar ────────────────────────────────
    "nima gap": [
        "{name}, hech gap yo'q, tinch! 😄",
        "Tinchlik {name}! Nima yangiliklar? 🌟",
        "Hamma yaxshi {name}! Siz-chi? 😊",
        "Gap ko'p {name}! Qo'shiling! 😄🎉",
    ],
    "nima bo'vopti": [
        "Hech nima {name}, hammasi tinch! 😊",
        "Hamma yaxshi {name}! 😄",
        "Tinchlik {name}, gap yo'q! 👍",
    ],
    "nima bvopti": [
        "Hech nima {name}, tinchlik! 😄",
        "Hammasi yaxshi {name}! 😊",
    ],
    "nima": [
        "Ha {name}, nima gap? 😊",
        "Aytingchi {name}? 🙂",
        "{name}, nima kerak? 😄",
        "Tinglayman {name}! 👂",
    ],
    "kim": [
        "Men — {BOT_NAME}! {name} aka! 🤖😊",
        "{name}, menmi? Yordamchi bot! 🤖",
        "Men botman {name}! Xizmatdaman! 🤖🌟",
    ],
    "qayer": [
        "Men guruhingizda {name}! 😄🌍",
        "Mana shu yerda {name}! 😊",
        "Guruhda! {name} aka! 🏠",
    ],
    "qaerda": [
        "Men shu yerda {name}! 😄",
        "Guruhingizda {name}! 🌍",
    ],
    "qo'toq": [
        "{name}, madaniyatli so'zlashing! 🙏😊",
        "Iltimos {name}, to'g'ri gaplashing! 🌟",
        "{name} aka, madaniyatli bo'ling! 🤝",
    ],
    "liboy": [
        "Liboy {name}? Nima gap? 😄",
        "Ha {name}, liboy! 😂🔥",
        "Liboy-liboy {name}! 😎",
        "{name} liboy dedi! 😂🎉",
        "Voy liboy {name}! 🤣",
    ],

    # ── Tasdiq / ijobiy ──────────────────────────────
    "zo'r": [
        "Ha {name}, rostdan ham zo'r! 💪🔥",
        "Ajoyib {name}! 🌟",
        "Zo'r-zo'r {name}! Davom eting! 💯",
        "{name} zo'r deydi — men ham qo'shilaman! 🔥",
    ],
    "super": ["Super-super {name}! 🔥💯", "{name}, juda zo'r! 🌟👏"],
    "barakalla": ["Barakalla {name}! 👏🌟", "{name}, zo'r! Barakalla! 💫", "Barakalla {name} aka! 🤲✨"],
    "ajoyib": ["Ajoyib {name}! 🌟✨", "Rostdan ajoyib {name}! 💪"],
    "yaxshi": ["Yaxshi {name}! 👍😊", "Zo'r {name}! 🌟"],
    "ok": ["Ok {name}! 👍", "Mayli {name}! 😊", "Ok-ok {name}! 👌"],
    "ha": ["Ha, to'g'ri {name}! 👍", "Albatta {name}! 😊", "Ha-ha {name}! 💯"],
    "albatta": ["Albatta {name}! 😊💯", "Bilasiz {name}! 🌟"],
    "tushunarli": ["Tushunarli {name}! 👌", "Yaxshi {name}! 😊"],
    "tushundim": ["Yaxshi {name}! Savollar bo'lsa so'rang! 😊", "Ok {name}! 👍"],

    # ── Salbiy / kulgili ────────────────────────────
    "yomon": ["Nima yomon {name}? 😟 Gapirsangiz bo'ladi!", "Tushunaman {name}... 😔"],
    "boring": ["Ha {name}, biroz jonlashtiramiz! 😄🔥", "{name}, bo'ling jonli bo'laylik! 🎉"],
    "charchadim": ["Dam oling {name}! 😴 Sog'lik muhim!", "Hordiq chiqaring {name}! 🌿😊"],
    "uxladim": ["Yaxshi uxladingizmi {name}? 😄☀️"],

    # ── Dua / diniy ─────────────────────────────────
    "omad": ["Omad tilayman {name}! 🍀💫", "Omad {name}! Uddalaysiz! 💪🍀"],
    "inshalloh": ["Inshalloh {name}! 🤲🌟", "Inshalloh {name} aka! 🤲"],
    "mashalloh": ["Mashalloh {name}! 🤲🌟", "Mashalloh {name}! Barakali bo'lsin! 🤲✨"],
    "alhamdulillah": ["Alhamdulillah {name}! 🤲", "Alhamdulillah {name}! Shukr! 🤲🌟"],
    "bismillah": ["Bismillah {name}! 🤲 Omad!", "Bismillah {name} aka! 🌟🤲"],
    "subhanalloh": ["Subhanalloh {name}! 🤲✨"],

    # ── Bayram / tabrik ──────────────────────────────
    "tabrik": ["Tabriklayman {name}! 🎉🎊", "Muborak bo'lsin {name}! 🎉"],
    "tug'ilgan kun": ["Tug'ilgan kun muborak {name}! 🎂🎉🎊 Ko'p yasha! 🌟"],
    "yangi yil": ["Yangi yil muborak {name}! 🎆🎇✨", "Baxtli yangi yil {name}! 🥳🎉"],
    "hayit": ["Hayit muborak {name}! 🤲🎊✨", "Hayitingiz muborak {name}! 🌙🎉"],

    # ── Ovqat / kun ─────────────────────────────────
    "ovqat": ["Ishtaha bilan {name}! 😋🍽️", "Mazali ovqat {name}! 🍽️😄"],
    "nonushta": ["Nonushta muborak {name}! 🍳☀️"],
    "tushlik": ["Tushlik muborak {name}! 🍽️😊"],
    "kechki ovqat": ["Kechki ovqat muborak {name}! 🍽️🌙"],
    "uxlay": ["Yaxshi uxlang {name}! 🌙😴"],

    # ── Emoji javoblar ───────────────────────────────
    "❤️":  ["❤️ Rahmat {name}!", "🥰 Siz ham {name}!", "💖 {name}! 🥰"],
    "👍":  ["👍 Zo'r {name}!", "✅ Yaxshi {name}!", "👍👍 {name}!"],
    "🔥":  ["🔥🔥 {name}, zo'r!", "🔥 {name} ishdagi! 💯"],
    "🎉":  ["🎉🎊 {name}, tabriklayman!", "🎊🎉 {name}!"],
    "😂":  ["😂😂 {name} kuldirib yubordi!", "Hahaha {name}! 😂🤣"],
    "🤣":  ["🤣🤣 {name}! Kuldingiz!", "Hahaha {name}! 😂"],
    "😍":  ["😍 {name} yoqtirdimi? 😄", "Ajoyib {name}! 😍🌟"],
    "💪":  ["💪💪 {name}, kuchli!", "Ha {name}, kuch bilan! 💪🔥"],
    "🙏":  ["🙏 Xudoga shukur {name}!", "🙏🌟 {name}!"],
    "👏":  ["👏👏 {name}! Zo'r!", "Bravo {name}! 👏🌟"],
    "🤔":  ["Ha {name}, o'ylab ko'rish kerak! 🤔💡"],
    "😎":  ["Zo'r {name}! 😎🔥", "Style bor {name}! 😎"],
    "🥰":  ["🥰 Rahmat {name}!", "Siz ham {name}! 🥰💖"],
}

def get_auto_reply(text: str, user_name: str) -> str | None:
    t = text.lower().strip()
    # "kim" so'zi uchun bot nomini to'g'ri ko'rsatish
    for kw in sorted(RESPONSES, key=len, reverse=True):
        if kw in t:
            reply = random.choice(RESPONSES[kw])
            reply = reply.replace("{name}", user_name)
            reply = reply.replace("{BOT_NAME}", BOT_NAME)
            return reply
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
        is_banned INTEGER DEFAULT 0, ban_reason TEXT DEFAULT '',
        invite_active INTEGER DEFAULT 1)""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER,
        user_id INTEGER, username TEXT, date TEXT)""")
    conn.commit(); conn.close()

def get_db(): return sqlite3.connect("bot_data.db")

def add_group(chat_id, title, username):
    conn = get_db(); c = conn.cursor()
    c.execute("""INSERT OR IGNORE INTO groups
        (chat_id, title, username, added_date, invite_active)
        VALUES (?, ?, ?, ?, 1)""",
        (chat_id, title, username or "", datetime.now().strftime("%Y-%m-%d %H:%M")))
    c.execute("UPDATE groups SET title=?, username=? WHERE chat_id=?",
              (title, username or "", chat_id))
    conn.commit(); conn.close()

def ban_group(chat_id, reason=""):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE groups SET is_banned=1, ban_reason=? WHERE chat_id=?", (reason, chat_id))
    conn.commit(); conn.close()

def unban_group(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE groups SET is_banned=0, ban_reason='' WHERE chat_id=?", (chat_id,))
    conn.commit(); conn.close()

def is_banned(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT is_banned FROM groups WHERE chat_id=?", (chat_id,))
    row = c.fetchone(); conn.close()
    return row and row[0] == 1

def get_all_groups():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT chat_id, title, username, member_count, added_date, is_banned, ban_reason FROM groups")
    rows = c.fetchall(); conn.close(); return rows

def get_active_groups():
    """Taklif xabari yuborilishi uchun barcha faol guruhlar."""
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT chat_id FROM groups WHERE is_banned=0 AND invite_active=1")
    rows = c.fetchall(); conn.close()
    return [r[0] for r in rows]

def get_stats():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM groups WHERE is_banned=0"); active = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM groups WHERE is_banned=1"); banned = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages"); total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages WHERE date >= date('now')"); today = c.fetchone()[0]
    conn.close(); return active, banned, total, today

def log_message(chat_id, user_id, username):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO messages (chat_id, user_id, username, date) VALUES (?, ?, ?, ?)",
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
         InlineKeyboardButton("⚙️ Sozlamalar",  callback_data="settings")],
        [InlineKeyboardButton("📢 Broadcast",   callback_data="broadcast_ask")],
    ])

def user_kb(bot_username):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Guruhga qo'shish", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("❓ Qo'llanma",        callback_data="how_to_add")],
        [InlineKeyboardButton("🆘 Adminga yozish",   callback_data="contact_admin")],
    ])


# ═══════════════════════════════════════════════════════
#   👥 TAKLIF TUGMASI — CHEKSIZ ODAM QO'SHISH
# ═══════════════════════════════════════════════════════
async def handle_invite_button(query, context: ContextTypes.DEFAULT_TYPE, gid: int):
    user = query.from_user

    # Guruh nomini olish
    try:
        chat = await context.bot.get_chat(gid)
        group_title = chat.title or "Guruh"
    except TelegramError:
        group_title = "Guruh"

    # Maxsus invite link yaratish (bu orqali kim qo'shganini bilamiz)
    try:
        link_obj = await context.bot.create_chat_invite_link(
            chat_id=gid,
            name=f"INV_{user.id}_{int(datetime.now().timestamp())}",
            creates_join_request=False,
        )
        link_str = link_obj.invite_link
        # Saqlash: link → (inviter_id, inviter_name, chat_id)
        invite_links_db[link_str] = (user.id, user.first_name, gid)
        logger.info(f"✅ Invite link yaratildi: {user.first_name} → {link_str}")
    except TelegramError as e:
        logger.error(f"Invite link xato: {e}")
        await query.message.reply_text(
            "❌ Havola yaratishda xato!\n"
            "Bot guruhda ADMIN ekanligini va 'Invite Users' ruxsati borligini tekshiring."
        )
        return

    # tg://add slug — kontaktlarni tanlab to'g'ridan qo'shish
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

    # Ulashish URL
    share_text = (
        f"Salom! 👋 \"{group_title}\" guruhiga taklif qilmoqchiman!\n"
        "Qo'shiling, ajoyib guruh! 💪🔥"
    )
    share_url = (
        f"https://t.me/share/url?"
        f"url={urllib.parse.quote(link_str)}"
        f"&text={urllib.parse.quote(share_text)}"
    )

    await query.message.reply_text(
        f"🔗 <b>{user.first_name}, havolangiz tayyor!</b>\n\n"
        f"📌 Guruh: <b>{group_title}</b>\n\n"
        f"👇 <b>Ikki usuldan birini tanlang:</b>\n\n"
        f"1️⃣ <b>Kontaktdan tanlash</b>\n"
        f"   → Telegramingizdan do'stlaringizni belgilab, cheksiz odam qo'shing\n\n"
        f"2️⃣ <b>Havola ulashish</b>\n"
        f"   → Linkni yuborib cheksiz odam taklif qiling\n\n"
        f"🏆 Kim qo'shilsa, guruhda <b>siz maqtalasiz!</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "👥 Kontaktdan tanlash (cheksiz)",
                url=add_members_url
            )],
            [InlineKeyboardButton(
                "📤 Havola ulashish",
                url=share_url
            )],
        ])
    )


# ═══════════════════════════════════════════════════════
#   🎉 YANGI A'ZO — KIM TAKLIF QILGANINI ANIQLASH
# ═══════════════════════════════════════════════════════
async def track_new_member_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = update.chat_member
    if not result:
        return

    old_status = result.old_chat_member.status
    new_status  = result.new_chat_member.status

    # Yangi a'zo qo'shildi
    if old_status in (ChatMember.LEFT, ChatMember.BANNED) and \
       new_status in (ChatMember.MEMBER, ChatMember.ADMINISTRATOR):

        new_member = result.new_chat_member.user
        chat_id    = result.chat.id

        # Usul 1: Invite link orqali (bot yaratgan link)
        invite_link_obj = getattr(result, "invite_link", None)
        if invite_link_obj:
            link_str = getattr(invite_link_obj, "invite_link", None)
            if link_str and link_str in invite_links_db:
                inviter_id, inviter_name, _ = invite_links_db[link_str]
                await _send_praise(context, chat_id, inviter_id, inviter_name, new_member)
                return

        # Usul 2: Kim qo'shdi (via_chat_folder_invite_link yoki inviter)
        inviter = getattr(result, "from_user", None)
        if inviter and inviter.id != new_member.id and not inviter.is_bot:
            await _send_praise(context, chat_id, inviter.id, inviter.first_name, new_member)


async def _send_praise(context, chat_id, inviter_id, inviter_name, new_member):
    """Taklif qilgan odamni maqtash."""
    inviter_m = f'<a href="tg://user?id={inviter_id}">{inviter_name}</a>'
    new_m     = f'<a href="tg://user?id={new_member.id}">{new_member.first_name}</a>'

    maqtovlar = [
        f"🎉 <b>BARAKALLA!</b> {inviter_m} birodar {new_m}ni guruhga qo'shdi! 🤝\nGuruh kengaymoqda! 💪🌟",
        f"👏 <b>ZO'R!</b> {inviter_m} guruhimizga {new_m}ni olib keldi!\nBarakalla! 🔥",
        f"🌟 {inviter_m} — <b>GURUH QAHRAMONI!</b>\n{new_m}ni qo'shdi! 💪🎊",
        f"✨ <b>RAHMAT</b> {inviter_m}!\nYangi a'zo {new_m} xush kelibsiz! 🎉",
        f"🏆 {inviter_m} guruhga yangi kuch qo'shdi!\n{new_m} xush kelibsiz! 🎊💫",
        f"💪 <b>AJOYIB!</b> {inviter_m} bizga {new_m}ni taklif qildi!\nBarakalla aka! 🌟🔥",
        f"🎊 {inviter_m} — bugunning yulduz taklif qiluvchisi!\n{new_m} guruhimizga marhamat! 🌟",
        f"🔥 {inviter_m} guruhni kengaytiryapti! {new_m}ni qo'shdi!\nSiz zo'rsiz {inviter_m}! 💯",
        f"⭐ {inviter_m} SUPERSTAR!\n{new_m}ni olib keldi! Barakalla! 👏🌟",
    ]
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=random.choice(maqtovlar),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Maqtov xabarida xato: {e}")


# ═══════════════════════════════════════════════════════
#          📢 TAKLIF XABARI — HAR 2 DAQIQADA
#          Chat ID lar AVTOMATIK olinadi DB dan
# ═══════════════════════════════════════════════════════
async def send_group_invite_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    group_ids = get_active_groups()   # DB dan avtomatik oladi
    for gid in group_ids:
        try:
            await context.bot.send_message(
                chat_id=gid,
                text=INVITE_MESSAGE,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("➕ Taklif qilish", callback_data=f"invite_{gid}")
                ]])
            )
        except TelegramError as e:
            err = str(e)
            if "bot was kicked" in err or "chat not found" in err or "bot is not a member" in err:
                # Guruhdan chiqarib yuborilgan — invite_active=0 qilish
                conn = get_db(); c = conn.cursor()
                c.execute("UPDATE groups SET invite_active=0 WHERE chat_id=?", (gid,))
                conn.commit(); conn.close()
                logger.warning(f"⚠️ Guruhdan chiqarib yuborildi, o'chirildi: {gid}")
            else:
                logger.error(f"Taklif xabari xato ({gid}): {e}")
        except Exception as e:
            logger.error(f"Taklif xabari xato ({gid}): {e}")


# ═══════════════════════════════════════════════════════
#                     📨 ASOSIY HANDLERLAR
# ═══════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    user     = update.effective_user
    bot_info = await context.bot.get_me()

    if is_admin(user.id):
        active, banned, total, today = get_stats()
        groups = get_active_groups()
        await update.message.reply_text(
            f"👑 Xush kelibsiz, <b>{user.first_name}</b>!\n\n"
            f"🤖 <b>{BOT_NAME}</b> — Admin Panel\n\n"
            f"📊 <b>Holat:</b>\n"
            f"  ✅ Faol guruhlar:  <b>{active}</b>\n"
            f"  🚫 Taqiqlangan:    <b>{banned}</b>\n"
            f"  💬 Jami xabarlar:  <b>{total}</b>\n"
            f"  📅 Bugun:          <b>{today}</b>\n"
            f"  🏠 Taklif guruhi:  <b>{len(groups)} ta (avtomatik)</b>\n\n"
            f"👇 Boshqarish uchun:",
            parse_mode=ParseMode.HTML,
            reply_markup=admin_kb()
        )
    else:
        await update.message.reply_text(
            f"✨ <b>Assalomu alaykum, {user.first_name}!</b>\n\n"
            f"🤖 Men <b>{BOT_NAME}</b>man!\n\n"
            "🎯 <b>Funksiyalarim:</b>\n"
            "  💬 Ko'p so'zlarga javob beraman\n"
            "  🎉 Yangi a'zolarni kutib olaman\n"
            "  👥 Do'stlaringizni taklif qilishga yordam beraman\n"
            "  🏆 Taklif qilganlarni maqtayman\n\n"
            "👇 Tanlang:",
            parse_mode=ParseMode.HTML,
            reply_markup=user_kb(bot_info.username)
        )

async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "🛠 <b>Admin Panel</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=admin_kb()
    )

async def track_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot guruhga qo'shilganda / chiqarilganda — chat ID ni avtomatik saqlaydi."""
    r = update.my_chat_member
    if not r:
        return
    chat   = r.chat
    status = r.new_chat_member.status
    if chat.type in ("group", "supergroup"):
        if status in (ChatMember.MEMBER, ChatMember.ADMINISTRATOR):
            add_group(chat.id, chat.title, chat.username)
            logger.info(f"✅ Yangi guruh qo'shildi: {chat.title} ({chat.id})")
        elif status in (ChatMember.LEFT, ChatMember.BANNED):
            conn = get_db(); c = conn.cursor()
            c.execute("UPDATE groups SET invite_active=0 WHERE chat_id=?", (chat.id,))
            conn.commit(); conn.close()
            logger.info(f"ℹ️ Bot guruhdan chiqdi: {chat.title} ({chat.id})")

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        mn = f'<a href="tg://user?id={member.id}">{member.first_name}</a>'
        greets = [
            f"🎉 Xush kelibsiz {mn}! Guruhimizga xush kelibsiz! 😊🌟",
            f"👋 Salom {mn}! Guruhimizga marhamat! 🎊",
            f"✨ {mn} bilan guruh yanada jonlandi! 🎉💫",
            f"💫 Xush kelibsiz {mn}! Savollaringiz bo'lsa so'rang! 😊",
            f"🌟 {mn} guruhimizga qo'shildi! Birga kuchli bo'lamiz! 💪",
            f"🎊 {mn}! Guruhimizga marhamat! Hush kelibsiz! 🤝",
        ]
        await update.message.reply_text(random.choice(greets), parse_mode=ParseMode.HTML)

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg  = update.message
    if not user or not msg or chat.type not in ("group", "supergroup"):
        return
    if is_banned(chat.id):
        return
    # Chat ID ni avtomatik qo'shib boradi
    add_group(chat.id, chat.title, chat.username)
    log_message(chat.id, user.id, user.username or user.first_name)
    text = msg.text or ""
    if not text:
        return
    reply = get_auto_reply(text, user.first_name)
    if reply:
        await msg.reply_text(reply, parse_mode=ParseMode.HTML)

async def handle_admin_pm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id) or update.effective_chat.type != "private":
        return
    action = context.user_data.get("action")
    text   = update.message.text or ""

    if action == "ban_id":
        try:
            cid = int(text.strip())
            ban_group(cid, "Admin taqiqladi")
            context.user_data.pop("action", None)
            await update.message.reply_text(
                f"✅ Guruh <code>{cid}</code> taqiqlandi!",
                parse_mode=ParseMode.HTML, reply_markup=admin_kb())
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID!")

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
        groups  = [g for g in get_all_groups() if g[5] == 0]
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
            f"📢 <b>Yuborildi!</b>\n✅ {sent} ta\n❌ {failed} ta",
            parse_mode=ParseMode.HTML, reply_markup=admin_kb())


# ═══════════════════════════════════════════════════════
#                   🔘 CALLBACK HANDLERLAR
# ═══════════════════════════════════════════════════════
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q        = update.callback_query
    await q.answer()
    d        = q.data
    uid      = q.from_user.id
    bot_info = await context.bot.get_me()

    # ── Invite tugmasi ──────────────────────────────
    if d.startswith("invite_"):
        gid = int(d.split("_")[1])
        await handle_invite_button(q, context, gid)
        return

    # ── Foydalanuvchi tugmalari ─────────────────────
    if d == "how_to_add":
        await q.edit_message_text(
            "📖 <b>Botni guruhga qo'shish</b>\n\n"
            "1️⃣ «Guruhga qo'shish» tugmasini bosing\n"
            "2️⃣ Ro'yxatdan guruhingizni tanlang\n"
            "3️⃣ Tasdiqlang\n"
            "4️⃣ Guruh sozlamalari → Adminlar → Botni toping\n"
            "5️⃣ <b>Barcha ruxsatlarni bering</b> (ayniqsa Invite Users)\n\n"
            "✅ Tayyor! Bot avtomatik ishlaydi!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Guruhga qo'shish",
                    url=f"https://t.me/{bot_info.username}?startgroup=true")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_user")],
            ]))
        return

    if d == "contact_admin":
        await q.edit_message_text(
            "🆘 <b>Adminga murojaat</b>\n\n📩 Quyidagi tugmani bosing:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 Adminga yozish", url=f"tg://user?id={ADMIN_IDS[0]}")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_user")],
            ]))
        return

    if d == "back_user":
        await q.edit_message_text(
            f"✨ <b>🤖 {BOT_NAME}</b>\n\n👇 Tanlang:",
            parse_mode=ParseMode.HTML, reply_markup=user_kb(bot_info.username))
        return

    # ── Admin tekshiruvi ────────────────────────────
    if not is_admin(uid):
        await q.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    # ── Admin tugmalari ─────────────────────────────
    if d == "stats":
        active, banned, total, today = get_stats()
        groups = get_active_groups()
        await q.edit_message_text(
            "📊 <b>Statistika</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Faol guruhlar:    <b>{active}</b>\n"
            f"🚫 Taqiqlangan:      <b>{banned}</b>\n"
            f"💬 Jami xabarlar:    <b>{total}</b>\n"
            f"📅 Bugun:            <b>{today}</b>\n"
            f"🏠 Taklif guruhi:    <b>{len(groups)} ta</b>\n\n"
            f"🕐 <i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")
            ]]))

    elif d == "settings":
        groups = get_active_groups()
        await q.edit_message_text(
            "⚙️ <b>Bot Sozlamalari</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🤖 Bot nomi:          <b>{BOT_NAME}</b>\n"
            f"👑 Adminlar:          <b>{len(ADMIN_IDS)}</b>\n"
            f"💬 Kalit so'zlar:     <b>{len(RESPONSES)}</b>\n\n"
            f"📢 Taklif xabari:     <b>har {INVITE_INTERVAL} sek (2 daqiqa)</b>\n"
            f"🏠 Faol guruhlar:     <b>{len(groups)} ta (avtomatik)</b>\n\n"
            "⚡ Barcha funksiyalar faol!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")
            ]]))

    elif d.startswith("groups_"):
        page   = int(d.split("_")[1])
        groups = [g for g in get_all_groups() if g[5] == 0]
        per_page = 5
        pg = groups[page * per_page:(page + 1) * per_page]
        text = (f"👥 <b>Faol Guruhlar</b> — {len(groups)} ta\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n") if groups else "👥 Faol guruh yo'q."
        for g in pg:
            cid, title, uname, _, added, _, _ = g
            un = f"@{uname}" if uname else "—"
            text += f"📌 <b>{title}</b>\n   🆔 <code>{cid}</code>  {un}\n   📅 {added}\n\n"
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️", callback_data=f"groups_{page-1}"))
        if (page + 1) * per_page < len(groups):
            nav.append(InlineKeyboardButton("➡️", callback_data=f"groups_{page+1}"))
        rows = []
        if nav: rows.append(nav)
        rows += [
            [InlineKeyboardButton("🚫 Guruh taqiqlash", callback_data="ask_ban")],
            [InlineKeyboardButton("🔙 Orqaga",          callback_data="back_admin")],
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
                [InlineKeyboardButton("✅ Tiklash",  callback_data="ask_unban")],
                [InlineKeyboardButton("🔙 Orqaga",   callback_data="back_admin")],
            ]))

    elif d == "broadcast_ask":
        context.user_data["action"] = "broadcast"
        groups = [g for g in get_all_groups() if g[5] == 0]
        await q.edit_message_text(
            f"📢 <b>Broadcast</b>\n\nGuruhlar: <b>{len(groups)}</b>\n\n✍️ Xabarni yozing:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")
            ]]))

    elif d == "ask_ban":
        context.user_data["action"] = "ban_id"
        await q.edit_message_text(
            "🚫 Guruh <b>ID</b>sini yuboring:\n<i>Misol: -1001234567890</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Bekor", callback_data="groups_0")
            ]]))

    elif d == "ask_unban":
        context.user_data["action"] = "unban_id"
        await q.edit_message_text(
            "✅ Tiklanadigan guruh <b>ID</b>sini yuboring:",
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

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("panel", cmd_panel))

    # Chat member tracking
    app.add_handler(ChatMemberHandler(track_bot,               ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(track_new_member_invite, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # Callback va xabarlar
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_admin_pm))
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, handle_group_message))

    # Har 2 daqiqada taklif xabari — chat ID lar avtomatik DB dan olinadi
    app.job_queue.run_repeating(
        send_group_invite_message,
        interval=INVITE_INTERVAL,
        first=30
    )

    logger.info("=" * 60)
    logger.info(f"🚀 {BOT_NAME} ISHGA TUSHDI!")
    logger.info(f"📢 Taklif xabari: har {INVITE_INTERVAL} sekund")
    logger.info(f"🏠 Chat ID lar avtomatik aniqlanadi (DB orqali)")
    logger.info(f"💬 So'zlar soni: {len(RESPONSES)}")
    logger.info("=" * 60)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
