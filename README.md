# Video Yuklovchi Telegram Bot 🎥

YouTube, Pinterest va Instagram videolarini video (MP4) yoki audio (MP3) formatida yuklab beradi!

## 📱 Qo'llab-quvvatlanadigan platformalar:

### 📺 YouTube
- Video sifatini tanlash (144p-1080p)
- Audio (MP3) konvertatsiya
- Shorts qo'llab-quvvatlash

### 📌 Pinterest
- Video yuklab olish
- Audio ekstraktatsiya

### 📸 Instagram
- **Reels** 🎬 - Video content
- **Posts** 📷 - Bitta rasm yoki video
- **Carousel** 🖼️ - Ko'p rasmlar/videolar
- **Stories** 📱 - 24 soatlik kontent
- **Highlights** ✨ - Saqlangan stories

## ⚠️ YouTube Bot Detection Muammosi

**Railway/Cloud serverlarida YouTube ishlamasligi mumkin!** YouTube datacenter IP manzillarini bloklaydi.

**✅ Yechimlar:**
1. **Cookies qo'shish** - [COOKIES_GUIDE.md](COOKIES_GUIDE.md) ni o'qing
2. **O'z kompyuteringizda ishlatish** (eng oson)
3. VPS server (DigitalOcean, Linode)

**Pinterest va Instagram Railway'da ham ishlaydi!** ✅

## 🚀 O'rnatish

1. **Kerakli kutubxonalarni o'rnatish:**
```bash
pip install -r requirements.txt
```

2. **FFmpeg o'rnatish (audio konvertatsiya qilish uchun kerak):**

Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg
```

Windows:
- [FFmpeg yuklab olish](https://ffmpeg.org/download.html)
- PATH ga qo'shish

MacOS:
```bash
brew install ffmpeg
```

3. **Telegram Bot yaratish:**
- [@BotFather](https://t.me/botfather) ga boring
- `/newbot` buyrug'ini yuboring
- Bot nomini va username kiriting
- Olingan tokenni nusxalang

4. **Bot tokenini sozlash:**

`.env` faylini yarating:
```bash
BOT_TOKEN=sizning_bot_tokeningiz
```

Yoki `youtube_bot.py` faylida `BOT_TOKEN` o'zgaruvchisiga to'g'ridan-to'g'ri token kiriting.

## 📖 Ishlatish

1. **Botni ishga tushirish:**
```bash
python youtube_bot.py
```

2. **Telegram'da botni ishlatish:**
- Botingizni topib `/start` buyrug'ini yuboring
- YouTube video linkini yuboring
- Video yoki Audio tugmasini tanlang
- Fayl yuklanguncha kuting!

## 🎯 Xususiyatlar

- ✅ YouTube videolarini MP4 formatida yuklab olish
- ✅ YouTube videolaridan audioni MP3 formatida ajratib olish
- ✅ Oson foydalanish uchun tugmalar interfeysi
- ✅ Yuklanish jarayoni haqida xabarlar
- ✅ Xatoliklarni avtomatik qayta ishlash

## 📋 Talablar

- Python 3.8+
- python-telegram-bot
- yt-dlp
- FFmpeg

## ⚠️ Eslatmalar

- Katta videolar yuklash uchun vaqt talab qilishi mumkin
- Telegram API 50MB dan katta fayllarni yuborish chegarasiga ega
- Bot tokeningizni hech kimga ko'rsatmang!

## 🐛 Muammolar

Agar xatolik yuz bersa:
1. Internet ulanishini tekshiring
2. FFmpeg o'rnatilganligini tekshiring
3. Bot tokenini to'g'ri kiritilganligini tekshiring
4. Python va kutubxonalar versiyalarini tekshiring

## 📞 Yordam

Savollar bo'lsa, GitHub'da issue oching yoki pull request yuboring!

---
**Yaratuvchi:** [Sizning ismingiz]
**Litsenziya:** MIT
