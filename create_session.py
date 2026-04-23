"""
╔══════════════════════════════════════════════════════════╗
║   🔑 PYROGRAM SESSION YARATISH (LOKAL KOMPYUTER UCHUN)  ║
║                                                          ║
║   Bu faylni O'Z KOMPYUTERINGIZDA ishga tushiring!        ║
║   Railway da EMAS!                                       ║
╚══════════════════════════════════════════════════════════╝

O'RNATISH:
    pip install pyrogram==2.0.106 tgcrypto

ISHGA TUSHIRISH:
    python create_session.py

KEYIN:
    Chiqgan SESSION_STRING ni Railway → Variables ga qo'shing:
    Key:   SESSION_STRING
    Value: (chiqgan uzun string)
"""

import asyncio
from pyrogram import Client

# ══════════════════════════════════════════
#   ⚙️  Sozlamalar  (bot.py dagi bilan bir xil)
# ══════════════════════════════════════════
API_ID   = 37366974
API_HASH = "08d09c7ed8b7cb414ed6a99c104f1bd6"


async def main():
    print("=" * 55)
    print("  🔑 PYROGRAM SESSION YARATISH")
    print("=" * 55)
    print()
    print("⚠️  Bu sizning SHAXSIY Telegram hisobingiz uchun!")
    print("    Bot uchun alohida hisob ishlatish tavsiya etiladi.")
    print()

    phone = input("📱 Telefon raqamingizni kiriting (+998...): ").strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    app = Client(
        ":memory:",
        api_id=API_ID,
        api_hash=API_HASH,
    )

    await app.connect()

    print()
    print("⏳ Telegram ga kod jo'natilmoqda...")

    try:
        sent = await app.send_code(phone)
    except Exception as e:
        print(f"\n❌ Xato: {e}")
        print("\nTekshiring:")
        print("  • Telefon raqam to'g'rimi? (+998XXXXXXXXX)")
        print("  • Internet aloqasi bormi?")
        print("  • API_ID va API_HASH to'g'rimi?")
        await app.disconnect()
        return

    print("✅ Kod yuborildi!")
    print()

    # Kodni kiritish — 3 marta urinish huquqi
    signed_in = False
    for attempt in range(3):
        code = input("📩 Telegram dan kelgan kodni kiriting: ").strip().replace(" ", "")
        try:
            await app.sign_in(phone, sent.phone_code_hash, code)
            signed_in = True
            break
        except Exception as e:
            err = str(e)
            if "PHONE_CODE_EXPIRED" in err:
                print("\n❌ Kod muddati tugadi! Qaytadan ishga tushiring.")
                await app.disconnect()
                return
            elif "PHONE_CODE_INVALID" in err:
                remaining = 2 - attempt
                if remaining > 0:
                    print(f"❌ Noto'g'ri kod! Yana {remaining} ta urinish qoldi.")
                else:
                    print("❌ Noto'g'ri kod! Urinishlar tugadi.")
                    await app.disconnect()
                    return
            elif "SESSION_PASSWORD_NEEDED" in err or "password" in err.lower():
                print("\n🔐 2FA parol kerak!")
                password = input("🔑 2FA parolingizni kiriting: ").strip()
                try:
                    await app.check_password(password)
                    signed_in = True
                    break
                except Exception as e2:
                    print(f"\n❌ Noto'g'ri parol: {e2}")
                    await app.disconnect()
                    return
            else:
                print(f"\n❌ Xato: {err}")
                await app.disconnect()
                return

    if not signed_in:
        await app.disconnect()
        return

    # Session string eksport qilish
    try:
        me             = await app.get_me()
        session_string = await app.export_session_string()
        await app.disconnect()
    except Exception as e:
        print(f"\n❌ Session eksport xatosi: {e}")
        return

    print()
    print("=" * 55)
    print(f"✅ Muvaffaqiyatli! Hisob: {me.first_name} (@{me.username or 'username yoq'})")
    print("=" * 55)
    print()
    print("🔑 SESSION_STRING (quyidagi butun qatorni ko'chirib oling):")
    print()
    print(session_string)
    print()
    print("=" * 55)
    print()
    print("📋 KEYINGI QADAM — Railway ga qo'shing:")
    print()
    print("  1. railway.com → Loyiha → GuruhBot → Variables")
    print("  2. 'New Variable' bosing")
    print("  3. Key:   SESSION_STRING")
    print("  4. Value: yuqoridagi SESSION_STRING")
    print("  5. Deploy avtomatik boshlanadi")
    print()

    # Faylga ham saqlash
    try:
        with open("session_string.txt", "w") as f:
            f.write(session_string)
        print("💾 'session_string.txt' fayliga ham saqlandi.")
    except Exception:
        pass

    print()
    print("✅ Tayyor! Endi Railway da bot ishlaydi.")


if __name__ == "__main__":
    asyncio.run(main())
