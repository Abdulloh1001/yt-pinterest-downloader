# 🚀 Railway da Deploy Qilish Qo'llanmasi

## 📋 Railway ga Deploy qilish bosqichlari:

### 1️⃣ Railway.app ga kirish
- [Railway.app](https://railway.app) ga o'ting
- GitHub akkaunt bilan login qiling

### 2️⃣ Yangi Proyekt Yaratish
1. **"New Project"** tugmasini bosing
2. **"Deploy from GitHub repo"** ni tanlang
3. Bu repository ni tanlang

### 3️⃣ Environment Variables Sozlash
Railway dashboard da **"Variables"** bo'limiga o'ting va quyidagilarni qo'shing:

```env
BOT_TOKEN=sizning_bot_tokeningiz
LOG_CHANNEL=-1001234567890
```

#### 🔑 BOT_TOKEN olish:
1. Telegram'da [@BotFather](https://t.me/botfather) ga o'ting
2. `/newbot` buyrug'ini yuboring
3. Bot nomini va username kiriting
4. Olingan tokenni `BOT_TOKEN` ga kiriting

#### 📊 LOG_CHANNEL ID olish:
1. Kanal yarating (yoki mavjud kanaldan foydalaning)
2. Botni kanalga admin qiling
3. [@userinfobot](https://t.me/userinfobot) yoki [@raw_data_bot](https://t.me/raw_data_bot) yordamida kanal ID sini oling
4. ID ni `LOG_CHANNEL` ga kiriting (masalan: `-1001234567890`)

### 4️⃣ Deploy Qilish
- Railway avtomatik ravishda deploy qiladi
- Logs bo'limida jarayonni kuzating
- ✅ "Bot ishga tushdi!" xabari ko'ringanda tayyor!

### 5️⃣ Botni Test Qilish
1. Telegram'da botingizni qidiring
2. `/start` buyrug'ini yuboring
3. YouTube yoki Pinterest link yuboring
4. Video yoki Audio tanlang va yuklab oling!

---

## 📁 Railway Uchun Kerakli Fayllar

Loyihada quyidagi fayllar mavjud:

### `Procfile`
Railway ga botni qanday ishga tushirish kerakligini aytadi:
```
web: python youtube_bot.py
```

### `runtime.txt`
Python versiyasini belgilaydi:
```
python-3.11.9
```

### `requirements.txt`
Kerakli Python paketlari:
```
python-telegram-bot==20.7
yt-dlp==2023.12.30
python-dotenv==1.0.0
```

### `railway.json`
Railway konfiguratsiyasi:
- Auto-restart yoqilgan
- Xatolik bo'lsa qayta ishga tushadi

---

## 🎯 Bot Xususiyatlari

✅ **YouTube** video va audio yuklab olish
✅ **Pinterest** video va audio yuklab olish
✅ **Progress bar** - yuklanish jarayonini ko'rsatish
✅ **Log kanal** - foydalanuvchilar faoliyatini kuzatish
✅ **Xatolik bilan ishlash** - tushunarli xatolik xabarlari

---

## 🔧 Texnik Ma'lumotlar

- **Platform:** Railway.app
- **Language:** Python 3.11.9
- **Framework:** python-telegram-bot 20.7
- **Downloader:** yt-dlp

---

## ⚠️ Muhim Eslatmalar

1. **FFmpeg:** Railway da FFmpeg avtomatik o'rnatiladi (audio konvertatsiya uchun)
2. **Storage:** Fayllar vaqtinchalik saqlanadi va yuborilgandan keyin o'chiriladi
3. **Limits:** Telegram 50MB gacha fayllarni qo'llab-quvvatlaydi
4. **Environment Variables:** `.env` fayldan emas, Railway Variables dan olinadi

---

## 🐛 Muammolar va Yechimlar

### Bot ishga tushmasa:
1. Logs bo'limini tekshiring
2. Environment variables to'g'ri kiritilganligini tekshiring
3. Bot tokenining amal qilish muddati o'tmaganligini tekshiring

### Video yuklanmasa:
1. Link to'g'riligini tekshiring
2. Video mavjudligini tekshiring
3. Internet tezligini tekshiring

---

## 📞 Qo'llab-quvvatlash

Muammolar yuz bersa:
- Railway logs ni tekshiring
- Bot loglarini o'qing
- GitHub Issues da savol bering

---

**Deploy qiling va foydalaning! 🚀**
