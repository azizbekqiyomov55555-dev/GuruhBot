FROM python:3.11-slim

# Tizim paketlari (ffmpeg musiqa uchun kerak)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python kutubxonalarini o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot fayllari
COPY . .

# Ma'lumotlar saqlanadigan papka (SQLite uchun)
RUN mkdir -p /data
ENV DB_PATH=/data/bot.db

# Botni ishga tushirish
CMD ["python", "-u", "bot.py"]
