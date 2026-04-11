# ╔══════════════════════════════════════════════════════════════╗
# ║           🤖 YORDAMCHI GURUH BOT — TO'LIQ VERSIYA           ║
# ║                  Barcha funksiyalar yoqilgan                 ║
# ╚══════════════════════════════════════════════════════════════╝
#
# 💡 MASLAHATLAR:
#   1. Botni guruhga ADMIN sifatida qo'shing
#   2. @BotFather → Bot Settings → Group Privacy → DISABLE qiling
#   3. Token va Admin ID ni hech kimga bermang!
#   4. Yangi so'z qo'shish: RESPONSES lug'atiga qo'shing
#   5. {name} — foydalanuvchi ismiga avtomatik almashadi

import logging
import sqlite3
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ChatMemberHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

# ═══════════════════════════════════════════════════════
#                      ⚙️ SOZLAMALAR
# ═══════════════════════════════════════════════════════
BOT_TOKEN = "8780908767:AAEewN-jTc2_19hUZRu9mf-qudBTKM2A8Gk"
ADMIN_IDS = [8537782289]
BOT_NAME  = "Yordamchi Bot"

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
    "молодец": [
        "Спасибо {name}! 😊",
        "Благодарю {name}! 🌟",
    ],

    # ── HAZIL / KULGU ─────────────────────────────────────
    "haha": [
        "😄 {name}, ha-ha, kulgi yuqumli!",
        "🤣 {name}, kulgidan yiqilib tushayapman!",
        "😂 Qiziq-qiziq {name}!",
    ],
    "lol": [
        "😂 LOL {name}!",
        "🤣 {name}, juda kulgili!",
    ],
    "хаха": [
        "😄 Ha-ha {name}!",
        "🤣 Kulgili {name}!",
    ],

    # ── LICH / PM ─────────────────────────────────────────
    "lich yozing": [
        "Yozing {name}, eshityapman! 📩😊",
        "DM ochiq {name}! Yuboring! 📨✨",
        "Lichkaga yozing {name}, javob beraman! 💬",
        "{name}, xabar yuboring, kutib turaman! 💌",
    ],
    "lich": [
        "{name}, lichkaga yuboring! 📩😊",
        "DM ochiq {name}! Yozing! 💬✨",
        "Lich yuboring {name}! 📨",
    ],
    "dm": [
        "DM ochiq {name}! Yuboring! 📩😊",
        "{name}, direct message yuboring! 💬",
    ],

    # ── MEHRIBON SO'ZLAR ──────────────────────────────────
    "asalim": [
        "Asal kabi shirin bo'ling {name}! 🍯😊",
        "Voy {name}, asal! 🍯💕",
        "{name}, shirin so'z yurakka yoqdi! 🍯✨",
    ],
    "jonim": [
        "Jon bo'ling {name}! ❤️😊",
        "Jonginam {name}! 🥰",
        "{name}, yaxshi gaplar eshitish yoqadi! 😊❤️",
    ],
    "azizim": [
        "Aziz bo'ling {name}! 💙😊",
        "{name}, menga ham aziz bo'ldingiz! 🌟",
    ],
    "qo'zim": [
        "Qo'zichoq {name}! 🐑😄",
        "{name}, yoqimli so'z! 😊💕",
    ],
    "sevaman": [
        "Sevgi go'zal his {name}! ❤️😊",
        "Baxtli bo'ling {name}! 💕🌟",
    ],
    "sog'indim": [
        "Sog'inish yaxshi belgi {name}! 🥺😊",
        "{name}, biz ham sog'indik! 💕",
    ],
    "do'stim": [
        "Do'st eng katta boylik {name}! 🤝😊",
        "Do'stlik muqaddas {name}! 🤝🌟",
    ],
    "aka": [
        "Ha aka {name}! Nima gap? 😊",
        "Akam {name}! Aytingchi! 😄",
    ],
    "opa": [
        "Ha opa {name}! Nima gap? 😊",
        "Opam {name}! Aytingchi! 😄",
    ],
    "bro": [
        "Bro {name}! Nima gap? 😎",
        "Ha bro {name}! 🤜🤛",
    ],
    "sis": [
        "Sis {name}! Yaxshimisiz? 😊",
        "Ha sis {name}! 💕",
    ],
    "yaxshi ko'raman": [
        "Rahmat {name}! Bu so'z yurakka yoqdi! 🥰❤️",
        "{name}, siz ham yaxshi bo'ling! 💕",
    ],

    # ── KAYFIYAT ─────────────────────────────────────────
    "kayfiyat": [
        "Kayfiyat a'lo {name}! 🌟😄 Sizchi?",
        "Zo'r kayfiyatda {name}! 🎉 Siz-chi?",
        "{name}, kayfiyatingiz yaxshi bo'lsin! ☀️",
    ],
    "zerikdim": [
        "{name}, zerikmaslik uchun shu yerda gaplashamiz! 😄",
        "Zerikmang {name}, gaplashamiz! 😎",
        "{name}, zerikish yo'q, biz bormiz! 🎉",
    ],
    "xursand": [
        "{name}, xursandchilik yuqumli! 😄🎉",
        "Xursand bo'ling {name}, doim! 🌟",
    ],
    "xafa": [
        "{name}, xafa bo'lmang! 😊 Hamma yaxshi bo'ladi!",
        "Xafachilik ketsin {name}! 🌈",
        "{name}, yaxshi kunlar kutmoqda! ☀️💫",
    ],
    "g'amginman": [
        "{name}, g'am ketsin! 🌈 Yaxshi kunlar keladi!",
        "Sabr qiling {name}, o'tib ketadi! 💪😊",
        "{name}, biz yoningdamiz! 🤝❤️",
    ],
    "yolg'iz": [
        "{name}, yolg'iz emassiz, biz bormiz! 😊🤝",
        "Bu guruhda do'stlar ko'p {name}! 🌟",
    ],
    "charchad": [
        "{name}, dam oling, sog'liq muhim! 😊💤",
        "Charchasangiz dam olish vaqti {name}! 🛋️",
    ],
    "uxlayman": [
        "{name}, yaxshi uxlang! 😴🌙",
        "Chiroyli tushlar {name}! 🌙✨",
        "{name}, tinch uxlang! 😴",
    ],
    "yig'layapman": [
        "{name}, ko'z yoshi — kuchning belgisi! 💪",
        "Hamma narsa o'tadi {name}! 🌈 Sabr qiling!",
    ],

    # ── TABIIY JAVOBLAR ───────────────────────────────────
    "ok": [
        "Ok {name}! 👍",
        "Zo'r {name}! ✅",
        "Mayli {name}! 😊",
        "Tushunarli {name}! 👍",
    ],
    "okay": [
        "Okay {name}! 👍😊",
        "Mayli {name}! 👌",
    ],
    "ha": [
        "Ha, to'g'ri {name}! 👍",
        "Albatta {name}! 😊",
        "{name}, ha! 🌟",
    ],
    "albatta": [
        "Albatta-albatta {name}! ✅😊",
        "Ha albatta {name}! 🌟",
        "{name}, shubhasiz! 💫",
    ],
    "omad": [
        "Omad tilayman {name}! 🍀💫",
        "{name}, omad har doim sizda bo'lsin! 🍀",
        "Omadli bo'ling {name}! ✨🌟",
    ],
    "bilmadim": [
        "{name}, hech gap emas, bilamiz! 😄",
        "Bilib olamiz {name}! 💪",
        "Izlaymiz, topamiz {name}! 🔍",
    ],
    "bilmayman": [
        "{name}, menam bilmayman 😅 Birgalikda o'rganamiz!",
        "Google dost {name}! 😄🔍",
    ],
    "wow": [
        "Wow {name}! 😲✨ Ajoyib!",
        "WOW {name}! 🤩 Zo'r!",
    ],
    "voy": [
        "Voy {name}! 😮 Nima bo'ldi?",
        "{name}, qiziqarli! 😮✨",
    ],
    "ura": [
        "Ura {name}! 🎉💪",
        "Ura-ura {name}! 🎊🌟",
    ],
    "yey": [
        "Yey {name}! 🎉🎊",
        "Yey-yey {name}! 🥳",
    ],
    "yashasin": [
        "Yashasin {name}! 🥳🎉",
        "{name}, yashasin-yashasin! 🎊💫",
    ],
    "a'lo": [
        "A'lo {name}! 💯🌟",
        "A'lo natija {name}! 💯👏",
    ],

    # ── DUA SO'ZLARI ─────────────────────────────────────
    "inshalloh": [
        "Inshalloh, albatta bo'ladi {name}! 🤲🌟",
        "Inshalloh {name}! 🤲",
        "{name}, Alloh xohlasa bo'ladi! 🤲✨",
    ],
    "mashalloh": [
        "Mashalloh {name}! 🤲🌟",
        "Mashalloh, barakali bo'lsin {name}! 🤲",
    ],
    "alhamdulillah": [
        "Alhamdulillah {name}! 🤲 Yaxshilik doim bo'lsin!",
        "Alhamdulillah {name}! 🤲🌟",
    ],
    "subhanalloh": [
        "Subhanalloh {name}! 🤲✨",
        "Subhanalloh {name}, go'zal! 🤲",
    ],

    # ── TABRIKLASH ───────────────────────────────────────
    "tabrik": [
        "Tabriklayman {name}! 🎉🎊",
        "Muborak bo'lsin {name}! 🎉",
        "Baxt tilaman {name}! 🌟🎊",
    ],
    "tug'ilgan kun": [
        "Tug'ilgan kun muborak {name}! 🎂🎉🎊",
        "Ko'p yillar yashang {name}! 🎂🎉",
        "{name}, baxtli tug'ilgan kun! 🎊🌟",
    ],
    "muborak": [
        "Sizga ham muborak {name}! 🎉😊",
        "Muborak bo'lsin {name}! 🌟🎊",
    ],

    # ── SAVOL SO'ZLARI ────────────────────────────────────
    "nima": [
        "{name}, nima haqida gaplashyapmiz? 🤔",
        "{name}, yaxshilab tushuntiring! 👂",
        "Qiziqarli savol {name}! 🤔",
    ],
    "nega": [
        "{name}, sababi bor albatta! 😄",
        "Qiziqarli savol {name}! 🤔",
    ],
    "qanday": [
        "{name}, qanday qilib? 🤔",
        "Tushuntirib bering {name}! 👂",
    ],
    "kim": [
        "Kim haqida so'rayapsiz {name}? 🤔",
        "{name}, aniqroq aysangiz? 😊",
    ],
    "qachon": [
        "{name}, vaqt haqida? ⏰",
        "Aniqroq savolingiz bormi {name}? 🤔",
    ],
    "qayerda": [
        "{name}, joy haqida? 📍",
        "Aniqroq aytib bering {name}! 🤔",
    ],

    # ── SPORT ─────────────────────────────────────────────
    "futbol": [
        "Futbol — eng yaxshi sport {name}! ⚽🔥",
        "Futbol sevaman {name}! ⚽ Qaysi jamoa yoqadi?",
        "{name}, futbol haqida gapirsak bo'ladi! ⚽😄",
    ],
    "sport": [
        "Sport — sog'liq {name}! 💪🏃",
        "{name}, qaysi sportni yoqtirasiz? 🤸",
        "Sport bilan shug'ullanish zo'r {name}! 💪",
    ],
    "gym": [
        "Gym zo'r {name}! 💪🏋️",
        "{name}, sog'lom tana — sog'lom aql! 💪",
    ],
    "basketbol": [
        "Basketball {name}! 🏀 Zo'r sport!",
        "{name}, NBA ko'rasizmi? 🏀😊",
    ],

    # ── OVQAT ─────────────────────────────────────────────
    "osh": [
        "O'zbek oshi dunyoning eng mazali taomi {name}! 🍚😋",
        "{name}, osh desangiz og'zim suv keldi! 🍚🔥",
    ],
    "lag'mon": [
        "Lag'mon {name}! 🍜 Eng mazali! 😋",
        "{name}, lag'mon desangiz og'zim suv keldi! 🍜🔥",
    ],
    "somsa": [
        "Somsa {name}! 🥟 Issiq-issiq! 😋",
        "{name}, somsa vaqti bo'ldimi? 🥟😄",
    ],
    "pizza": [
        "Pizza {name}! 🍕 Juda mazali!",
        "{name}, pizza sevuvchilar eng yaxshi odamlar! 🍕😄",
    ],
    "qahva": [
        "Qahva {name}! ☕ Energiya beradi!",
        "{name}, qahva vaqti! ☕😊",
    ],
    "choy": [
        "{name}, choy — umr barakasi! ☕🙏",
        "Choy vaqti {name}! ☕😊",
        "{name}, issiq choy iching! ☕",
    ],
    "shashlik": [
        "Shashlik {name}! 🍖🔥 Og'zim suv keldi!",
        "{name}, shashlik desangiz boraman! 😄🔥",
    ],
    "ovqat": [
        "{name}, ovqat vaqti bo'ldimi? 😋🍽️",
        "Nima eyapsiz {name}? 😊",
    ],

    # ── TEXNOLOGIYA / TA'LIM ──────────────────────────────
    "telegram": [
        "Telegram — eng zo'r messenger {name}! 📱✨",
        "{name}, Telegram bor ekan, yaxshi! 😄📱",
    ],
    "dasturlash": [
        "Dasturlash zo'r kasb {name}! 💻👨‍💻",
        "{name}, dasturlash o'rganish tavsiya! 💻🚀",
    ],
    "maktab": [
        "Maktab bilim maskani {name}! 📚😊",
        "O'qing {name}, bilim kuch! 📚💪",
    ],
    "dars": [
        "{name}, dars o'qidingizmi? 📚😊",
        "Dars muhim {name}, o'qing! 📚💡",
    ],
    "imtihon": [
        "{name}, imtihon uchun omad! 📚🍀",
        "{name}, omad tilayman imtihonda! 🍀✨",
    ],
    "universitet": [
        "Universitet katta hayot maktabi {name}! 🎓😊",
        "Barakali o'qishlar {name}! 🎓🌟",
    ],

    # ── ISH / PUL ─────────────────────────────────────────
    "ish": [
        "{name}, ishda muvaffaqiyat! 💼💪",
        "Barakali ish bo'lsin {name}! 💼",
    ],
    "pul": [
        "Barakali pul tilayman {name}! 💰🌟",
        "{name}, pul topish uchun mehnat kerak! 💰💪",
    ],
    "biznes": [
        "{name}, biznes qiling, muvaffaq bo'ling! 💼🌟",
        "Zo'r {name}! Biznes uchun omad! 💼💪",
    ],

    # ── MUSIQA / KINO ─────────────────────────────────────
    "musiqa": [
        "Musiqa ruhning ozuqasi {name}! 🎵❤️",
        "{name}, qaysi musiqani yoqtirasiz? 🎵😊",
    ],
    "kino": [
        "Kino sevaman {name}! 🎬😄",
        "{name}, qaysi janrdagi kino yoqadi? 🎬🍿",
    ],

    # ── OB-HAVO ───────────────────────────────────────────
    "yomg'ir": [
        "{name}, yomg'ir baraka! 🌧️🙏",
        "{name}, yomg'irli kun — ichkarida choy! ☕🌧️",
    ],
    "quyosh": [
        "Quyosh kabi nur sochib yashang {name}! ☀️😊",
        "{name}, quyoshli kun! ☀️🌟",
    ],
    "issiq": [
        "{name}, issiqda ko'p suv iching! 💧😊",
        "{name}, issiqda ehtiyot bo'ling! ☀️💧",
    ],
    "sovuq": [
        "{name}, sovuqda iliq kiyining! 🧥❄️",
        "{name}, sovuqdan ehtiyot bo'ling! ❄️🧣",
    ],
    "bahor": [
        "Bahor yangilanish fasli {name}! 🌸😊",
        "Bahor xayrli bo'lsin {name}! 🌸🌷",
    ],
    "yoz": [
        "Yoz dam olish {name}! ☀️😄",
        "{name}, yozda suvga tush! 🏊☀️",
    ],
    "qish": [
        "{name}, qishda iliq bo'ling! ❄️🧣",
        "Qish sovuq lekin shinam {name}! ❄️☕",
    ],
    "kuz": [
        "Kuz rangli fasl {name}! 🍂😊",
        "{name}, kuzda baraka ko'p! 🍂🌟",
    ],

    # ── KUNDALIK ──────────────────────────────────────────
    "uyg'ondim": [
        "Xayrli tong {name}! ☀️ Yaxshi kun bo'lsin!",
        "{name}, uyg'oning muborak! ☀️😊",
        "Yangi kun yangi imkoniyat {name}! 🌅",
    ],
    "dam olaman": [
        "{name}, yaxshi dam oling! 🛋️😊",
        "Dam olish muhim {name}! 💆✨",
    ],
    "sayr": [
        "{name}, sayrda yaxshi dam oling! 🚶😊",
        "Sayr sog'liqqa yaxshi {name}! 🚶💚",
    ],

    # ── HAYOT / ILHOM ─────────────────────────────────────
    "hayot": [
        "Hayot go'zal {name}, undan bahramand bo'ling! 🌸",
        "{name}, hayot eng katta ne'mat! 🙏🌟",
        "Hayotni sevib yashang {name}! ❤️",
    ],
    "orzum": [
        "{name}, orzu qiling, intiling — bo'ladi! 💪🌟",
        "Orzular uchish uchun qanotdir {name}! 🦋",
        "{name}, orzuingiz amalga oshsin! 🌠",
    ],
    "maqsad": [
        "Maqsadga erishish uchun harakat kerak {name}! 💪",
        "{name}, maqsadli inson baxtli bo'ladi! 🌟",
    ],

    # ── HAYVONLAR ─────────────────────────────────────────
    "mushuk": [
        "Mushuk {name}! 🐱 Juda yoqimli!",
        "{name}, mushuklar eng muloyim hayvonlar! 🐱😊",
    ],
    "it": [
        "It sodiq do'st {name}! 🐕😊",
        "{name}, itingiz bormi? 🐕",
    ],

    # ── EMOJI JAVOBLARI ───────────────────────────────────
    "🙏": [
        "🙏 Arzimaydi {name}!",
        "🙏 Marhamat {name}!",
        "😊 Xursand bo'ldim {name}!",
    ],
    "❤️": [
        "❤️ Rahmat {name}!",
        "🥰 Siz ham {name}!",
        "💕 Xursand bo'ldim {name}!",
    ],
    "👍": [
        "👍 Zo'r {name}!",
        "✅ Yaxshi {name}!",
        "💪 Barakalla {name}!",
    ],
    "🔥": [
        "🔥🔥 {name}, zo'r!",
        "{name} 🔥 Zo'r!",
    ],
    "💪": [
        "💪💪 {name}, kuchli!",
        "Ha {name}, kuch-quvvat! 💪",
    ],
    "😍": [
        "😍 Yoqimli {name}!",
        "🥰 Zo'r {name}!",
    ],
    "🎉": [
        "🎉🎊 {name}, tabriklayman!",
        "Bayram {name}! 🎉",
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
        [InlineKeyboardButton("📊 Statistika", callback_data="stats"),
         InlineKeyboardButton("👥 Guruhlar",   callback_data="groups_0")],
        [InlineKeyboardButton("🚫 Taqiqlangan", callback_data="banned"),
         InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_ask")],
    ])

def user_kb(bot_username):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Guruhga qo'shish", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("❓ Qo'shilmadimi? — Qo'llanma", callback_data="how_to_add")],
        [InlineKeyboardButton("🆘 Adminga yozish", callback_data="contact_admin")],
    ])


# ═══════════════════════════════════════════════════════
#                     📨 HANDLERLAR
# ═══════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private": return
    user = update.effective_user
    bot_info = await context.bot.get_me()

    if is_admin(user.id):
        active, banned, total, today = get_stats()
        await update.message.reply_text(
            f"👑 Xush kelibsiz, <b>{user.first_name}</b>!\n\n"
            f"🤖 <b>{BOT_NAME}</b> — Admin Panel\n\n"
            "📊 <b>Hozirgi holat:</b>\n"
            f"  ✅ Faol guruhlar: <b>{active}</b>\n"
            f"  🚫 Taqiqlangan:   <b>{banned}</b>\n"
            f"  💬 Jami xabarlar: <b>{total}</b>\n"
            f"  📅 Bugun:         <b>{today}</b>\n\n"
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
            "  🎉 Yangi a'zolarni kutib olaman\n\n"
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
            f"🌈 {mn}, siz bilan guruhimiz to'ldi! Yaxshi vaqt o'tkazing! 😄🎉",
        ]
        await update.message.reply_text(random.choice(greets), parse_mode=ParseMode.HTML)

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.message
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

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
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
                [InlineKeyboardButton("➕ Guruhga qo'shish", url=f"https://t.me/{bot_info.username}?startgroup=true")],
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
                [InlineKeyboardButton("📩 Adminga yozish", url=f"tg://user?id={ADMIN_IDS[0]}")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_user")],
            ])
        ); return

    if d == "back_user":
        await q.edit_message_text(
            f"✨ <b>🤖 {BOT_NAME}</b>\n\n👇 Quyidagi tugmalardan birini tanlang:",
            parse_mode=ParseMode.HTML, reply_markup=user_kb(bot_info.username)
        ); return

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
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")]]))

    elif d.startswith("groups_"):
        page = int(d.split("_")[1])
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
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")],
            ]))

    elif d == "settings":
        total_words = len(RESPONSES)
        total_replies = sum(len(v) for v in RESPONSES.values())
        await q.edit_message_text(
            "⚙️ <b>Bot Sozlamalari</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 Kalit so'zlar: <b>{total_words}</b>\n"
            f"📝 Jami javoblar: <b>{total_replies}</b>\n\n"
            f"🤖 Bot nomi: <b>{BOT_NAME}</b>\n"
            f"👑 Adminlar: <b>{len(ADMIN_IDS)}</b>\n\n"
            "⚡ Barcha funksiyalar <b>faol</b>!\n\n"
            "💡 <i>Yangi so'z qo'shish uchun bot.py faylini tahrirlang</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")]]))

    elif d == "broadcast_ask":
        context.user_data["action"] = "broadcast"
        groups = [g for g in get_all_groups() if g[5] == 0]
        await q.edit_message_text(
            f"📢 <b>Broadcast</b>\n\n"
            f"📊 Guruhlar soni: <b>{len(groups)}</b>\n\n"
            "✍️ Yuboriladigan xabarni yozing:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))

    elif d == "ask_ban":
        context.user_data["action"] = "ban_id"
        await q.edit_message_text(
            "🚫 <b>Guruh taqiqlash</b>\n\nGuruh <b>ID</b>sini yuboring:\n<i>Misol: -1001234567890</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="groups_0")]]))

    elif d == "ask_unban":
        context.user_data["action"] = "unban_id"
        await q.edit_message_text(
            "✅ <b>Guruhni tiklash</b>\n\nGuruh <b>ID</b>sini yuboring:",
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
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("panel", cmd_panel))
    app.add_handler(ChatMemberHandler(track_bot, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_admin_pm))
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, handle_group_message))
    logger.info(f"🚀 {BOT_NAME} ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
