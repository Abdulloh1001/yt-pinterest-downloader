# Local Bot API Setup Guide (Railway)

## Nega Local Bot API?
- 10x tezroq upload (50-100 MB/s)
- 2GB gacha video inline play
- Telegram'ning direct connection

---

## Railway'da Setup (2 ta Service)

### Service 1: Local Bot API (yangi)
### Service 2: Your Bot (mavjud)

---

## Step-by-Step: Local API Service Yaratish

### 1. Railway Dashboard'ga Kiring
- [railway.app](https://railway.app) → Login
- Sizning project'ni oching

### 2. Yangi Service Qo'shing
1. **"+ New"** tugmasini bosing
2. **"Empty Service"** ni tanlang
3. Nom: **"telegram-local-api"**

### 3. GitHub'dan Deploy Qiling
1. **Service Settings** → **Source**
2. **"Connect Repo"** → `yt-pinterest-downloader`
3. **Root Directory:** `/` (default)
4. **Dockerfile Path:** `Dockerfile.localapi`

### 4. Environment Variables Qo'shing
Service Settings → Variables:

```
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
```

**❗ MUHIM:** Sizning haqiqiy API_ID va API_HASH'ni kiriting!

### 5. Port Settings
Service Settings → Networking:
- **Internal Port:** `8081`
- **Generate Domain** (ixtiyoriy, debugging uchun)

### 6. Deploy Qiling
- **Deploy** tugmasini bosing
- 3-5 daqiqa kutib turing

---

## Step 2: Bot Service'ni Yangilang

### 1. Bot Service'ni Oching
Railway → `yt-pinterest-downloader` service

### 2. Environment Variable Qo'shing
Service Settings → Variables:

```
LOCAL_API_URL=http://telegram-local-api.railway.internal:8081
```

**Yoki (agar domain yaratgan bo'lsangiz):**
```
LOCAL_API_URL=https://telegram-local-api.up.railway.app
```

### 3. Redeploy Qiling
- Bot kodi avtomatik yangilangan (github'dan)
- Local API'ga ulangan

---

## Test Qilish 🧪

1. **Telegram bot'ni oching**
2. **544MB video yuklang**
3. **Natija:**
   - Oldin: 5-10 daqiqa
   - Hozir: 30-60 soniya! 🚀

---

## Muammolar va Yechimlar 🔧

### Local API ishlamayotgan bo'lsa:
1. **Logs tekshiring:**
   - Railway → telegram-local-api service → Logs
   - "Telegram Bot API server is running" ko'rinishi kerak

2. **Environment variables to'g'ri kiritilganligini tekshiring:**
   - `TELEGRAM_API_ID` va `TELEGRAM_API_HASH` mavjud
   - Bo'sh joylar yo'q

3. **Internal URL to'g'ri:**
   - Bot service'da `LOCAL_API_URL` o'rnatilgan
   - Format: `http://telegram-local-api.railway.internal:8081`

### Bot ulanmayotgan bo'lsa:
1. **Bot logs tekshiring:**
   - "Using Local Bot API" yozuvi ko'rinishi kerak
   - Xato bo'lsa, URL'ni tekshiring

---

## Xarajatlar 💰

Railway Free Plan:
- 2 service (bot + local api)
- $5/month atrofida (500 soat/oy)
- Local API juda kam resurs ishlatadi

---

## Yoki Oddiy Variant (Local API'siz)

Agar juda murakkab bo'lsa:
- Bot'da 300MB limit qo'shamiz
- 300MB+ file sifatida yuboramiz
- Setup yo'q, darhol ishlaydi

---

**Qaysi variantni davom ettiramiz?**
