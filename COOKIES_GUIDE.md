# YouTube Cookies Qo'shish (YouTube Bot Detection'ni Bypass Qilish)

Agar Railway yoki boshqa cloud serverda YouTube videolar yuklanmasa, cookies yordamida muammoni hal qilishingiz mumkin.

## 📋 Qadamlar:

### 1️⃣ **Browser Extension O'rnatish**

**Chrome uchun:**
- [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) extension'ni o'rnating

**Firefox uchun:**
- [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) addon'ni o'rnating

### 2️⃣ **YouTube'ga Sign In Qiling**

1. Browser'da [youtube.com](https://youtube.com) ga kiring
2. Google account bilan sign in qiling
3. Bir necha video ochib ko'ring (YouTube sizni "trust" qilishi uchun)

### 3️⃣ **Cookies Export Qiling**

**Extension orqali:**
1. YouTube sahifasida extension ikonkasini bosing
2. "Export" yoki "Download" tugmasini bosing
3. `youtube_cookies.txt` nomi bilan saqlang

**Yoki yt-dlp orqali:**
```bash
# Chrome'dan
yt-dlp --cookies-from-browser chrome --cookies youtube_cookies.txt "https://www.youtube.com"

# Firefox'dan
yt-dlp --cookies-from-browser firefox --cookies youtube_cookies.txt "https://www.youtube.com"

# Edge'dan
yt-dlp --cookies-from-browser edge --cookies youtube_cookies.txt "https://www.youtube.com"
```

### 4️⃣ **Cookies Faylni Bot Papkasiga Joylashtiring**

**Lokal (o'z kompyuteringizda):**
```bash
# Bot papkasi ichiga
cp youtube_cookies.txt /home/ubuntu/Desktop/first_apk/youtube_cookies.txt
```

**Railway'da:**
1. Railway dashboard'ga kiring
2. Project > Variables > "Raw Editor"
3. Yangi environment variable qo'shing:
   ```
   YOUTUBE_COOKIES=<cookies fayl mazmuni>
   ```

### 5️⃣ **Botni Qayta Ishga Tushiring**

```bash
# Lokal
python youtube_bot.py

# Railway (avtomatik restart bo'ladi)
git push origin main
```

## ✅ **Tekshirish**

Bot loglarida ko'rinadi:
```
YouTube cookies fayli topildi va ishlatilmoqda
```

Endi YouTube videolar muammosiz yuklanishi kerak! 🎉

## ⚠️ **Muhim:**

- Cookies har 1-2 haftada yangilanishi kerak
- Cookies maxfiy - hech kimga ko'rsatmang!
- `.gitignore` da cookies fayl bor - GitHub'ga yuklanmaydi
- Agar ishlamas - yangi cookies export qiling

## 🔄 **Muqobil Usul: Browser'dan Manual**

1. YouTube'da `F12` bosing (Developer Tools)
2. `Application` > `Cookies` > `https://youtube.com`
3. Barcha cookies'ni ko'chirib oling
4. `youtube_cookies.txt` faylga Netscape formatida yozing

## 💡 **Maslahat:**

Agar cookies ham ishlamasa:
- VPN yoqib cookies oling
- Boshqa Google account ishlatib ko'ring  
- Proxy server qo'shing

---

**Yordam kerakmi?** [@abdulloh1001](https://github.com/Abdulloh1001) ga murojaat qiling.
