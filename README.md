# 🤖 Telegram Bot — Fly.io Deployment

## 📋 Tayyorgarlik

### 1. Fly.io ro'yxatdan o'ting
- https://fly.io/app/sign-up — bepul akkaunt
- Karta ulash kerak (lekin bepul tier bor — pul yechilmaydi)

### 2. flyctl o'rnating

**Windows (PowerShell):**
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

**Mac/Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

### 3. Login qiling
```bash
fly auth login
```

---

## 🚀 Botni ishga tushirish

### 1. ZIP ni oching va shu papkaga kiring
```bash
cd bot-fly
```

### 2. App yarating
```bash
fly launch --no-deploy
```
- App nomi: `obmen-bot` (yoki o'z nomingiz)
- Region: `fra` (Frankfurt — eng yaqin)
- Postgres: **No**
- Redis: **No**
- Deploy hozir: **No**

### 3. Disk yarating (SQLite uchun)
```bash
fly volumes create bot_data --region fra --size 1
```

### 4. Maxfiy o'zgaruvchilarni qo'shing
```bash
fly secrets set BOT_TOKEN="8298808352:AAH..."
fly secrets set ADMIN_ID="8537782289"
fly secrets set API_ID="37366974"
fly secrets set API_HASH="08d09c7ed8b7cb414ed6a99c104f1bd6"
fly secrets set SESSION_STRING="..."  # create_session.py dan oling
```

### 5. Deploy qiling
```bash
fly deploy
```

### 6. Loglarni ko'ring
```bash
fly logs
```

---

## 🔑 SESSION_STRING qanday olinadi?

1. Lokal kompyuterda:
```bash
pip install pyrogram==2.0.106 tgcrypto
python create_session.py
```

2. Yoki Google Colab da `create_session_colab.py` ni ishga tushiring.

3. Chiqgan stringni `fly secrets set SESSION_STRING="..."` ga qo'shing.

---

## 🛠 Foydali buyruqlar

```bash
fly status              # Bot holati
fly logs                # Real-time loglar
fly ssh console         # Serverga kirish
fly apps restart        # Qayta ishga tushirish
fly scale count 1       # 1 ta instance
fly scale memory 1024   # RAM ni 1GB ga oshirish
```

---

## ⚠️ Muhim eslatmalar

- **bot.py** ichida `BOT_TOKEN`, `ADMIN_ID` o'zgaruvchilari `os.environ` dan o'qilishi kerak
- SQLite bazasi `/data/bot.db` da saqlanadi (doimiy disk)
- Bepul tier: 3 ta shared-cpu-1x mashina, 3GB disk
