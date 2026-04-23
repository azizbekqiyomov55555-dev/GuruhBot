# ╔══════════════════════════════════════════════════════════╗
# ║   Google Colab da ishga tushiring:                      ║
# ║   https://colab.research.google.com                     ║
# ║   → New notebook → bu kodni paste qiling → Run          ║
# ╚══════════════════════════════════════════════════════════╝

# 1-katak — kutubxona o'rnatish
import subprocess
subprocess.run(["pip", "install", "pyrogram==2.0.106", "tgcrypto", "-q"])

# 2-katak — session yaratish
import asyncio
from pyrogram import Client

API_ID   = 37366974
API_HASH = "08d09c7ed8b7cb414ed6a99c104f1bd6"

async def create_session():
    phone = input("📱 Telefon raqam (+998...): ").strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    app = Client(":memory:", api_id=API_ID, api_hash=API_HASH)
    await app.connect()

    print("⏳ Kod jo'natilmoqda...")
    try:
        sent = await app.send_code(phone)
    except Exception as e:
        print(f"❌ Xato: {e}")
        await app.disconnect()
        return

    print("✅ Kod yuborildi! Tez kiriting!")
    code = input("📩 Telegram kodi: ").strip().replace(" ", "")

    try:
        await app.sign_in(phone, sent.phone_code_hash, code)
    except Exception as e:
        err = str(e)
        if "SESSION_PASSWORD_NEEDED" in err or "password" in err.lower():
            password = input("🔐 2FA parol: ").strip()
            try:
                await app.check_password(password)
            except Exception as e2:
                print(f"❌ Noto'g'ri parol: {e2}")
                await app.disconnect()
                return
        else:
            print(f"❌ Xato: {err}")
            await app.disconnect()
            return

    me = await app.get_me()
    session_string = await app.export_session_string()
    await app.disconnect()

    print("\n" + "="*60)
    print(f"✅ Muvaffaqiyatli! Hisob: {me.first_name}")
    print("="*60)
    print("\n🔑 SESSION_STRING (quyidagini to'liq ko'chiring):\n")
    print(session_string)
    print("\n" + "="*60)
    print("📋 Railway → GuruhBot → Variables ga qo'shing:")
    print("   Key:   SESSION_STRING")
    print("   Value: yuqoridagi string")

await create_session()
