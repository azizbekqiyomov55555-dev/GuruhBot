"""
╔══════════════════════════════════════════════════════╗
║   🔑 USERBOT SESSION YARATISH                       ║
║   Bu faylni faqat BIR MARTA ishga tushiring!        ║
╚══════════════════════════════════════════════════════╝

ISHLATISH:
    pip install pyrogram==2.0.106
    python create_session.py

Keyin:
1. Telefon raqam kiriting: +998777XXXXXX
2. Telegramga kelgan kodni kiriting
3. music_session.session fayli yaratiladi
4. Shu faylni Railway'ga yuklang
"""

import os
from pyrogram import Client

API_ID   = int(os.environ.get("API_ID", "37366974"))
API_HASH = os.environ.get("API_HASH", "08d09c7ed8b7cb414ed6a99c104f1bd6")

print("=" * 55)
print("🔑 USERBOT SESSION YARATISH")
print("=" * 55)
print()
print("⚠️  Bu yerga asosiy raqamingizni EMAS,")
print("    alohida SIM karta raqamini kiriting!")
print()

app = Client("music_session", api_id=API_ID, api_hash=API_HASH)

with app:
    me = app.get_me()
    print()
    print("=" * 55)
    print(f"✅ Session muvaffaqiyatli yaratildi!")
    print(f"👤 Ism: {me.first_name}")
    print(f"🆔 ID: {me.id}")
    print(f"📱 Username: @{me.username}" if me.username else "📱 Username yo'q")
    print()
    print("📁 music_session.session fayli yaratildi!")
    print("📤 Shu faylni Railway'ga yuklang.")
    print("=" * 55)
