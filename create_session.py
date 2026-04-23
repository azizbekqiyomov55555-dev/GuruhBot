"""
╔══════════════════════════════════════════════════════╗
║   🔑 PYROGRAM SESSION YARATISH SKRIPTI              ║
║   Bu skriptni BIR MARTA ishlatib session yarating   ║
╚══════════════════════════════════════════════════════╝

QANDAY ISHLATILADI:
  1. pip install pyrogram==2.0.106 tgcrypto
  2. python create_session.py
  3. Telefon raqamingizni kiriting (xalqaro format: +998901234567)
  4. Telegram'dan kelgan kodni kiriting
  5. "music_session.session" fayli yaratiladi
  6. Bu fayl bot.py bilan BIR PAPKADA bo'lishi kerak!

DIQQAT:
  - Bu skript sizning SHAXSIY Telegram hisobingiz bilan ishlaydi
  - Session fayli boshqalarga bermang!
  - Faqat bir marta ishlatish kerak
"""

import asyncio
import os

# ══════════════════════════════════════════
#   BU YERGA O'Z API_ID va API_HASH QOYING
#   https://my.telegram.org dan olasiz
# ══════════════════════════════════════════
API_ID   = int(os.environ.get("API_ID", "37366974"))
API_HASH = os.environ.get("API_HASH", "08d09c7ed8b7cb414ed6a99c104f1bd6")

SESSION_NAME = "music_session"


async def main():
    try:
        from pyrogram import Client
    except ImportError:
        print("❌ Pyrogram o'rnatilmagan!")
        print("   pip install pyrogram==2.0.106 tgcrypto")
        return

    print("=" * 55)
    print("🔑 PYROGRAM SESSION YARATISH")
    print("=" * 55)
    print(f"📱 API_ID:   {API_ID}")
    print(f"🔑 API_HASH: {API_HASH[:8]}...")
    print(f"💾 Session:  {SESSION_NAME}.session")
    print("=" * 55)
    print()

    app = Client(
        SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
    )

    try:
        await app.start()
        me = await app.get_me()
        print()
        print("=" * 55)
        print(f"✅ SESSION MUVAFFAQIYATLI YARATILDI!")
        print(f"👤 Hisob: {me.first_name} (@{me.username})")
        print(f"🆔 ID: {me.id}")
        print(f"💾 Fayl: {SESSION_NAME}.session")
        print("=" * 55)
        print()
        print("✅ Endi bu papkada 'music_session.session' fayli bor.")
        print("✅ Botni ishga tushiring — tozalash to'liq ishlaydi!")
        print()
        await app.stop()
    except Exception as e:
        print(f"❌ Xato: {e}")
        print()
        print("📋 Tekshiring:")
        print("  1. API_ID va API_HASH to'g'riligini")
        print("  2. Internet aloqasini")
        print("  3. Telegram kod to'g'ri kiritilganini")


if __name__ == "__main__":
    asyncio.run(main())
