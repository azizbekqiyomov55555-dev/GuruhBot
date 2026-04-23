"""
╔══════════════════════════════════════════════════════════════╗
║   🔑 PYROGRAM SESSION YARATISH  (bir marta ishlatiladi)     ║
╚══════════════════════════════════════════════════════════════╝

QANDAY ISHLATILADI:
  1. pip install pyrogram==2.0.106 tgcrypto
  2. python create_session.py
  3. Telefon raqamingizni kiriting (+998901234567)
  4. Telegram'dan kelgan kodni kiriting
  5. SESSION_STRING chiqadi — uni .env ga yoki serverga qo'ying
"""

import asyncio
import os

API_ID   = int(os.environ.get("API_ID", "37366974"))
API_HASH = os.environ.get("API_HASH", "08d09c7ed8b7cb414ed6a99c104f1bd6")


async def main():
    try:
        from pyrogram import Client
    except ImportError:
        print("❌ Pyrogram o'rnatilmagan!")
        print("   pip install pyrogram==2.0.106 tgcrypto")
        return

    print("=" * 60)
    print("🔑 PYROGRAM SESSION YARATISH")
    print("=" * 60)

    # In-memory session (fayl yaratmaydi)
    app = Client(
        ":memory:",
        api_id=API_ID,
        api_hash=API_HASH,
    )

    try:
        await app.start()
        me = await app.get_me()

        # String session eksport
        session_str = await app.export_session_string()

        print()
        print("=" * 60)
        print(f"✅ MUVAFFAQIYAT! Hisob: {me.first_name} (@{me.username})")
        print("=" * 60)
        print()
        print("📋 Quyidagi SESSION_STRING ni nusxalab oling:")
        print()
        print(f"SESSION_STRING={session_str}")
        print()
        print("─" * 60)
        print("💡 Endi nima qilish kerak:")
        print()
        print("  📌 Railway/Render da:")
        print("     Variables → SESSION_STRING → yuqoridagi qiymat")
        print()
        print("  📌 .env fayl yozayotgan bo'lsangiz:")
        print("     Yuqoridagi SESSION_STRING=... qatorni .env ga qo'ying")
        print()
        print("  📌 Oddiy serverda (VPS):")
        print("     export SESSION_STRING='...'  # yoki .env ga yozing")
        print()
        print("  ✅ Keyin botni qayta ishga tushiring!")
        print("─" * 60)

        await app.stop()

    except Exception as e:
        print(f"❌ Xato: {e}")


if __name__ == "__main__":
    asyncio.run(main())
