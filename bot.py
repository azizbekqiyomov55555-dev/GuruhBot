import logging
import sqlite3
import random
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

# ===================== JAVOBLAR BAZASI =====================
# Format: "kalit so'z" : ["javob1", "javob2", "javob3", ...]
RESPONSES = {
    # --- SALOMLASHUVLAR ---
    "salom": [
        "Vaalaykum assalom! 😊",
        "Assalomu alaykum! Xush kelibsiz! 👋",
        "Salom-salom! Qandaysiz? 😄",
        "Vaalaykum! Yaxshi kunlar tilaman! ☀️",
        "Hey, salom! Nima gap? 😎",
    ],
    "assalom": [
        "Vaalaykum assalom! 🙏",
        "Assalomu alaykum! Yaxshi keldingiz! 😊",
        "Vaalaykum! Xush kelibsiz guruhga! 🌟",
        "Assalom! Xayrli kun! ☀️",
    ],
    "assalomu alaykum": [
        "Va alaykum assalom va rahmatulloh! 🤲",
        "Va alaykum assalom! Xayrli kun! 😊",
        "Vaalaykum assalom! Yaxshi keldingiz! 🌟",
    ],
    "xayrli kun": [
        "Sizga ham xayrli kun! ☀️😊",
        "Xayrli kun! Omad tilayman! 🌟",
        "Xayrli kun! Kayfiyatingiz yaxshi bo'lsin! 😄",
        "Rahmat! Sizga ham baxtli kun! 🌈",
    ],
    "xayrli kech": [
        "Sizga ham xayrli kech! 🌙✨",
        "Xayrli kech! Yaxshi dam oling! 😊",
        "Xayrli oqshom! 🌃",
    ],
    "xayrli tong": [
        "Sizga ham xayrli tong! ☀️🌸",
        "Xayrli tong! Yangi kun yangi imkoniyatlar! 🌅",
        "Tong muborak! Omadli kun bo'lsin! 😊",
    ],
    "привет": [
        "Привет! 😊 (Salom!)",
        "Здравствуйте! Xush kelibsiz! 👋",
        "Привет-привет! Как дела? 😄",
    ],
    "hello": [
        "Hello! 👋 Welcome!",
        "Hi there! 😊",
        "Hey! Salom! 🌟",
    ],
    "hi": [
        "Hi! 👋",
        "Hey! Salom! 😊",
        "Hello! Xush kelibsiz! 🌟",
    ],

    # --- XAYR AYTISH ---
    "xayr": [
        "Xayr! Ko'rishguncha! 👋",
        "Xayr-xayr! Eson-omon yuring! 😊",
        "Hayr! Yaxshi keting! 🌟",
        "Ko'rishguncha! Sog' bo'ling! 🙏",
    ],
    "hayr": [
        "Hayr! Ko'rishguncha! 👋",
        "Eson-omon yuring! 🌟",
        "Xayr! Yaxshi keting! 😊",
    ],
    "yaxshi kecha": [
        "Sizga ham yaxshi kecha! 🌙✨",
        "Yaxshi uxlang! Chiroyli tushlar! 😴🌙",
        "Yaxshi kecha! Tinch uxlang! 🌃",
    ],
    "bye": [
        "Bye! Ko'rishguncha! 👋",
        "See you! Xayr! 😊",
        "Bye-bye! 🌟",
    ],

    # --- HOLINI SO'RASH ---
    "qalaysiz": [
        "Yaxshi, rahmat! Siz-chi? 😊",
        "Ajoyib! Sizga ham yaxshilik tilayman! 🌟",
        "Hammasi zo'r! Siz qalaysiz? 😄",
        "Yaxshi-yaxshi! 😊 Siz-chi, yaxshimisiz?",
    ],
    "qalay": [
        "Yaxshi, rahmat! 😊 Siz-chi?",
        "Zo'r! Hammasi joyida! 💪",
        "Ajoyib kayfiyatda! 🌟 Siz-chi?",
    ],
    "yaxshimisiz": [
        "Yaxshi, rahmat! Siz ham yaxshi bo'ling! 😊",
        "Ha, juda yaxshi! Rahmat! 🌟",
        "Yaxshi! Sizga ham yaxshilik! 💫",
    ],
    "nima gap": [
        "Hech gap yo'q, tinch! 😄",
        "Hammasi yaxshi, siz-chi? 😊",
        "Gap yo'q! Yaxshi kunlar! ☀️",
        "Tinchlik! Nima yangiliklar? 🌟",
    ],
    "как дела": [
        "Отлично! Спасибо! 😊 (Zo'r!)",
        "Всё хорошо! 🌟 (Hammasi yaxshi!)",
        "Хорошо, спасибо! А у вас? 😄",
    ],
    "how are you": [
        "I'm great, thanks! 😊",
        "Fine, thank you! And you? 🌟",
        "Doing well! Thanks for asking! 😄",
    ],

    # --- MINNATDORLIK ---
    "rahmat": [
        "Arzimaydi! 😊",
        "Marhamat! 🌟",
        "Iltimos! Doimo xizmatda! 💫",
        "Xursand bo'ldim! 😄",
        "Hech gap emas! 👍",
    ],
    "raxmat": [
        "Arzimaydi! 😊",
        "Marhamat! 🌟",
        "Iltimos! 💫",
    ],
    "спасибо": [
        "Пожалуйста! 😊 (Marhamat!)",
        "Не за что! 🌟",
        "Всегда пожалуйста! 💫",
    ],
    "thank you": [
        "You're welcome! 😊",
        "No problem! 🌟",
        "Anytime! 💫",
    ],
    "thanks": [
        "Sure thing! 😊",
        "No worries! 🌟",
        "Welcome! 👍",
    ],

    # --- KECHIRASIZ ---
    "kechirasiz": [
        "Hech gap emas! 😊",
        "Ayb yo'q! 🌟",
        "Muammo yo'q! 😄",
    ],
    "uzr": [
        "Hech gap emas! 😊",
        "Ayb yo'q, muammo yo'q! 🌟",
        "Mayli! 😄",
    ],
    "извини": [
        "Всё нормально! 😊 (Hech gap emas!)",
        "Не переживай! 🌟",
    ],

    # --- MAQTOV / KOMPLIMENT ---
    "zo'r": [
        "Ha, rostdan ham zo'r! 💪🔥",
        "Ajoyib! 🌟",
        "Zo'r-zo'r! 👏",
    ],
    "super": [
        "Super-super! 🔥💯",
        "Juda zo'r! 🌟👏",
        "Ajoyib! Super! ✨",
    ],
    "yaxshi": [
        "Zo'r! 👍😊",
        "Juda yaxshi! 🌟",
        "Ajoyib! 😄",
    ],
    "bravo": [
        "Bravo-bravo! 👏🎉",
        "Zo'r! Tabriklayman! 🏆",
        "Juda ajoyib! 🌟👏",
    ],
    "ajoyib": [
        "Ha, chindan ham ajoyib! 🌟✨",
        "Zo'r! 😄",
        "Ajoyib-ajoyib! 💫",
    ],
    "молодец": [
        "Спасибо! 😊 Juda yaxshi!",
        "Благодарю! 🌟",
        "Рад стараться! 💪",
    ],

    # --- HAZIL / KULGULARLAR ---
    "haha": [
        "😄😄 Ha-ha, kulgi yuqumli!",
        "🤣 Kulgidan yiqilib tushayapman!",
        "😂 Qiziq-qiziq!",
    ],
    "lol": [
        "😂 LOL!",
        "🤣 Juda kulgili!",
        "😄 Ha-ha!",
    ],
    "😂": [
        "😂😂 Kulgili ekan!",
        "🤣 Men ham kulyapman!",
        "😄 Qiziqchilik!",
    ],
    "хаха": [
        "😄 Ha-ha!",
        "🤣 Kulgili!",
        "😂",
    ],

    # --- SAVOL SO'ZLARI ---
    "nima": [
        "Nima haqida gaplashyapmiz? 🤔",
        "Yaxshilab tushuntiring, eshityapman! 👂",
        "Qiziqarli savol! 🤔 Aytib bering!",
    ],
    "kim": [
        "Kim haqida so'rayapsiz? 🤔",
        "Aniqroq aytsa bo'ladimi? 😊",
    ],
    "qachon": [
        "Vaqt haqida so'rayapsizmi? ⏰",
        "Aniqroq savolingiz bormi? 🤔",
    ],
    "qayerda": [
        "Joy haqida so'rayapsizmi? 📍",
        "Qayerda ekanligini bilmayman 😅",
    ],
    "qanday": [
        "Qanday qilib degani? 🤔",
        "Tushuntirib bering, eshityapman! 👂",
    ],
    "nega": [
        "Sababi... murakkab savol bu! 🤔",
        "Yaxshi savol! Menam o'ylayman 😄",
    ],
    "nimaga": [
        "Sababi bor albatta! 😄",
        "Qiziqarli savol! 🤔",
    ],

    # --- SPORT ---
    "futbol": [
        "Futbol — eng yaxshi sport! ⚽🔥",
        "Futbol sevaman! ⚽ Qaysi jamoa yoqadi?",
        "Futbol haqida gapirsak bo'ladi! ⚽😄",
    ],
    "basketball": [
        "Basketball! 🏀 Zo'r sport!",
        "NBA ko'rasizmi? 🏀😊",
    ],
    "sport": [
        "Sport — sog'liq! 💪🏃",
        "Qaysi sportni yoqtirasiz? 🤸",
        "Sport bilan shug'ullanish — zo'r! 💪",
    ],
    "gym": [
        "Gym — juda yaxshi! 💪🏋️",
        "Sog'lom tana — sog'lom aql! 💪",
        "Zo'r! Gym — mening ham sevgilim! 🏋️",
    ],

    # --- OVQAT ---
    "osh": [
        "O'zbek oshi — dunyoning eng mazali taomi! 🍚😋",
        "Osh desangiz, og'zim suv keldi! 🍚🔥",
        "Mmmm, osh! Eng yaxshi ovqat! 😄",
    ],
    "ovqat": [
        "Ovqat vaqti bo'ldimi? 😋🍽️",
        "Nima eyapsiz? 😊",
        "Qorin ochdi shekilli! 😄🍽️",
    ],
    "non": [
        "Non — baraka! 🍞🙏",
        "O'zbek noni — eng mazali! 😋",
    ],
    "shashlik": [
        "Shashlik! 🍖🔥 Og'zim suv keldi!",
        "Shashlik desangiz... boraman! 😄🔥",
    ],
    "pizza": [
        "Pizza! 🍕 Juda mazali!",
        "Pizza sevuvchilar — eng yaxshi odamlar! 🍕😄",
    ],
    "чай": [
        "Чой ичiмizmi? ☕😊",
        "Чой — umr barakasi! ☕",
    ],
    "чой": [
        "Choy ichinglar, mehribon bo'lasizlar! ☕😊",
        "Choy vaqti! ☕🌟",
    ],

    # --- TEXNOLOGIYA ---
    "telegram": [
        "Telegram — eng zo'r messenger! 📱✨",
        "Telegram bor ekan, yaxshi! 😄📱",
    ],
    "internet": [
        "Internet — zamonaviy hayot! 🌐💻",
        "Internet tezligi yaxshimi? 😄🌐",
    ],
    "telefon": [
        "Qaysi telefon ishlataysiz? 📱",
        "Telefon — zamonaviy do'st! 📱😊",
    ],
    "kompyuter": [
        "Kompyuter — zo'r asbob! 💻👨‍💻",
        "Dasturlash o'rganayapsizmi? 💻😄",
    ],

    # --- MUSIQA ---
    "musiqa": [
        "Musiqa — ruhning ozuqasi! 🎵❤️",
        "Qaysi musiqani yoqtirasiz? 🎵😊",
        "Musiqa tinglash — ajoyib! 🎶",
    ],
    "kino": [
        "Kino sevaman! 🎬😄",
        "Qaysi janrdagi kino yoqadi? 🎬🍿",
        "Kino kecha! 🎬🍿 Zo'r taklif!",
    ],

    # --- TABIIY JAVOBLAR ---
    "ok": [
        "Ok! 👍",
        "Zo'r! ✅",
        "Mayli! 😊",
        "Tushunarli! 👍",
    ],
    "okay": [
        "Okay! 👍😊",
        "Zo'r! ✅",
        "Mayli! 👌",
    ],
    "маъқул": [
        "Zo'r! 👍",
        "Mayli! 😊",
    ],
    "тушунарли": [
        "Yaxshi! 👍",
        "Zo'r! 😊",
    ],
    "ha": [
        "Ha, to'g'ri! 👍",
        "Albatta! 😊",
        "Ha-ha! 🌟",
    ],
    "yo'q": [
        "Mayli, muammo yo'q! 😊",
        "Tushunarli! 👍",
    ],
    "bilmadim": [
        "Hech gap emas, bilamiz! 😄",
        "Bilib olamiz! 💪",
        "Izlaymiz, topamiz! 🔍",
    ],
    "bilmayman": [
        "Menam bilmayman 😅 Birgalikda o'rganamiz!",
        "Google dost! 😄🔍",
    ],
    "🙏": [
        "🙏 Arzimaydi!",
        "🙏 Marhamat!",
        "😊 Xursand bo'ldim!",
    ],
    "❤️": [
        "❤️ Rahmat!",
        "🥰 Siz ham!",
        "💕 Xursand bo'ldim!",
    ],
    "👍": [
        "👍 Zo'r!",
        "✅ Yaxshi!",
        "💪 Barakalla!",
    ],

    # --- TASHVISH / MUAMMO ---
    "muammo": [
        "Qanday muammo? Yordam berishga harakat qilaman! 💪",
        "Muammo bo'lsa — birgalikda hal qilamiz! 🤝",
    ],
    "yordam": [
        "Yordam beraman! Nima kerak? 😊",
        "Xizmatda turaman! 💪",
        "Qanday yordam kerak? 🌟",
    ],
    "qiyin": [
        "Hamma narsa o'rganiladi! 💪😊",
        "Qiyin emas, shunchaki yangi! 😄",
        "Bardosh bering, bo'ladi! 💪",
    ],
    "charchad": [
        "Dam oling, sog'liq muhim! 😊💤",
        "Charchasangiz — dam olish vaqti! 🛋️",
        "Sog'liq — eng katta boylik! 💪",
    ],
    "uxlayman": [
        "Yaxshi uxlang! 😴🌙",
        "Chiroyli tushlar! 🌙✨",
        "Tinch uxlang! 😴",
    ],
    "yaxshimas": [
        "Nima bo'ldi? Aytib bering! 😊",
        "Muammo bo'lsa, gaplashsa bo'ladi! 🤝",
    ],

    # --- TABRIKLASH ---
    "tabrik": [
        "Tabriklayman! 🎉🎊",
        "Muborak bo'lsin! 🎉",
        "Baxt tilaman! 🌟🎊",
    ],
    "tug'ilgan kun": [
        "Tug'ilgan kun muborak! 🎂🎉🎊",
        "Ko'p yillar yashang! 🎂🎉",
        "Baxtli tug'ilgan kun! 🎊🌟",
    ],
    "muborak": [
        "Sizga ham muborak! 🎉😊",
        "Muborak bo'lsin! 🌟🎊",
    ],
    "baxt": [
        "Baxt hammaga nasib bo'lsin! 🌟😊",
        "Baxtli bo'ling! 🌈💫",
    ],
}

def get_auto_reply(text: str, user_name: str) -> str | None:
    """Kalit so'z bo'yicha javob topadi, topsa random birini qaytaradi"""
    text_lower = text.lower().strip()

    # To'liq mos
    for keyword, replies in RESPONSES.items():
        if keyword in text_lower:
            return random.choice(replies)

    return None

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
    message = update.message

    if not user or not message or chat.type not in ("group", "supergroup"):
        return

    if is_banned(chat.id):
        return

    add_group(chat.id, chat.title, chat.username)
    log_message(chat.id, user.id, user.username or user.first_name)

    text = message.text or ""
    if not text:
        return

    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    reply = get_auto_reply(text, user.first_name)

    if reply:
        await message.reply_text(f"{mention}, {reply}", parse_mode=ParseMode.HTML)

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
