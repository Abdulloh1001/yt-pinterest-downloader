import os
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot tokenini kiriting (bu yerga o'z bot tokeningizni qo'ying)
BOT_TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL = os.getenv('LOG_CHANNEL')

# Yuklab olingan fayllar uchun papka
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot ishga tushganda xabar beradi"""
    await update.message.reply_text(
        "Assalomu alaykum! 👋\n\n"
        "Men video va audio yuklovchi botman.\n\n"
        "Quyidagi platformalardan video link yuboring:\n\n"
        "📺 <b>YouTube</b> (youtube.com, youtu.be)\n"
        "📌 <b>Pinterest</b> (pinterest.com, pin.it)\n\n"
        "Men sizga video yoki audio formatida yuklab beraman!\n\n"
        "🎬 Video (MP4 format)\n"
        "🎵 Audio (MP3 format)",
        parse_mode='HTML'
    )


async def handle_youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Video linkini qabul qiladi va formatni tanlash tugmalarini ko'rsatadi"""
    url = update.message.text
    
    # YouTube yoki Pinterest linkini tekshirish
    is_youtube = 'youtube.com' in url or 'youtu.be' in url
    is_pinterest = 'pinterest.com' in url or 'pin.it' in url
    
    if not (is_youtube or is_pinterest):
        await update.message.reply_text(
            "❌ Bu YouTube yoki Pinterest link emas!\n\n"
            "Quyidagi platformalardan link yuboring:\n"
            "📺 YouTube (youtube.com, youtu.be)\n"
            "📌 Pinterest (pinterest.com, pin.it)"
        )
        return
    
    # URLni context'ga saqlash
    context.user_data['youtube_url'] = url
    
    # Platform nomini aniqlash
    platform = "YouTube" if is_youtube else "Pinterest"
    
    # Log kanaliga xabar yuborish
    if LOG_CHANNEL:
        try:
            user = update.message.from_user
            
            # Foydalanuvchi ma'lumotlarini tayyorlash
            if user.username:
                user_link = f'<a href="https://t.me/{user.username}">{user.full_name}</a> (@{user.username})'
            else:
                user_link = f'<a href="tg://user?id={user.id}">{user.full_name}</a>'
            
            log_message = (
                f"📊 <b>Yangi {platform} Link</b>\n\n"
                f"👤 User: {user_link}\n"
                f"🆔 ID: <code>{user.id}</code>\n"
                f"🔗 Link: {url}\n"
                f"⏰ Vaqt: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            await context.bot.send_message(
                chat_id=LOG_CHANNEL,
                text=log_message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Log kanalga yuborishda xatolik: {e}")
    
    # Inline klaviaturani yaratish
    keyboard = [
        [
            InlineKeyboardButton("📹 Video (MP4)", callback_data='video'),
            InlineKeyboardButton("🎵 Audio (MP3)", callback_data='audio')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Qanday formatda yuklab olmoqchisiz?",
        reply_markup=reply_markup
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugma bosilganda ishga tushadi"""
    query = update.callback_query
    await query.answer()
    
    url = context.user_data.get('youtube_url')
    
    if not url:
        await query.edit_message_text("❌ Xatolik yuz berdi. Iltimos, qaytadan link yuboring.")
        return
    
    callback_data = query.data
    
    # Agar orqaga tugmasi bosilgan bo'lsa
    if callback_data == 'back_to_format':
        keyboard = [
            [InlineKeyboardButton("📹 Video (MP4)", callback_data='video')],
            [InlineKeyboardButton("🎵 Audio (MP3)", callback_data='audio')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Qanday formatda yuklab olmoqchisiz?",
            reply_markup=reply_markup
        )
        return
    
    # Agar video tugmasi bosilgan bo'lsa - sifatlarni ko'rsat
    if callback_data == 'video':
        await show_quality_options(query, url, context)
    # Agar sifat tanlangan bo'lsa (video_720p kabi)
    elif callback_data.startswith('video_'):
        quality = callback_data.replace('video_', '')  # '720p' ni oladi
        await query.edit_message_text("⏳ Video yuklanmoqda... Iltimos kuting...")
        await download_video(query, url, quality)
    elif callback_data == 'audio':
        await query.edit_message_text("⏳ Audio yuklanmoqda... Iltimos kuting...")
        await download_audio(query, url)


async def show_quality_options(query, url, context):
    """Video sifatlarini ko'rsatadi va foydalanuvchi tanlaydi"""
    try:
        await query.edit_message_text("🔍 Mavjud sifatlar tekshirilmoqda...")
        
        # yt-dlp orqali mavjud formatlarni olish
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'mweb'],
                    'player_skip': ['webpage'],
                }
            },
            'age_limit': None,  # Age restriction'ni o'tkazib yuborish
        }
        
        # Cookies fayl mavjud bo'lsa ishlatamiz
        cookies_file = os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt')
        if os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
            logger.info("YouTube cookies fayli topildi va ishlatilmoqda")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
        
        # Video+Audio formatlarini filterlash
        quality_map = {}
        for f in formats:
            height = f.get('height')
            filesize = f.get('filesize') or f.get('filesize_approx') or 0
            
            # Faqat video bo'lgan va hajmi ma'lum formatlar
            if height and filesize and filesize > 0:
                quality_key = f"{height}p"
                
                # Eng kichik hajmli formatni saqlash
                if quality_key not in quality_map or filesize < quality_map[quality_key]['size']:
                    quality_map[quality_key] = {
                        'size': filesize,
                        'height': height
                    }
        
        # Tugmalarni yaratish
        keyboard = []
        qualities = ['240p', '360p', '480p', '720p', '1080p']
        
        for quality in qualities:
            if quality in quality_map:
                size_mb = quality_map[quality]['size'] / (1024 * 1024)
                
                # Faqat 50MB dan kichik bo'lganlarni ko'rsatish
                if size_mb <= 50:
                    button_text = f"📹 {quality} • {size_mb:.1f} MB"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"video_{quality}")])
        
        if not keyboard:
            await query.edit_message_text(
                "❌ Afsuski, 50 MB dan kichik sifatli video topilmadi.\n"
                "Telegram orqali 50 MB dan katta fayllarni yuborish mumkin emas."
            )
            return
        
        # Orqaga tugmasini qo'shish
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_format")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📊 Video sifatini tanlang:\n\n"
            "⚠️ Telegram limiti: maksimum 50 MB",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Sifat olishda xatolik: {e}")
        
        if "Sign in to confirm" in str(e) or ("bot" in str(e).lower() and "youtube" in str(e).lower()):
            await query.edit_message_text(
                "🤖 YouTube bot detection xatosi!\n\n"
                "YouTube bu videoni bot deb aniqladi.\n\n"
                "✅ Yechimlar:\n"
                "• Boshqa YouTube videoni sinab ko'ring\n"
                "• Bir necha daqiqa kutib qaytadan urinib ko'ring\n\n"
                "⚠️ Ba'zi videolar maxsus himoyalangan."
            )
        else:
            await query.edit_message_text(
                "❌ Sifatlarni olishda xatolik yuz berdi.\n"
                f"Xatolik: {str(e)[:100]}"
            )


async def download_video(query, url, quality='best'):
    """Video formatda yuklab oladi"""
    try:
        # Unique fayl nomi yaratish
        timestamp = int(time.time())
        temp_filename = f"video_{timestamp}"
        
        # Pinterest uchun maxsus format
        is_pinterest = 'pinterest.com' in url or 'pin.it' in url
        
        # Progress callback uchun o'zgaruvchilar
        last_progress_update = {'time': 0, 'percent': 0}
        
        def progress_hook(d):
            """Yuklanish jarayonini kuzatish"""
            if d['status'] == 'downloading':
                # Har 3 soniyada bir marta yangilansin
                current_time = time.time()
                if current_time - last_progress_update['time'] >= 3:
                    try:
                        # Foizni hisoblash
                        if 'total_bytes' in d:
                            percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                        elif 'total_bytes_estimate' in d:
                            percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                        else:
                            percent = 0
                        
                        # Faqat foiz o'zgarganda yangilansin
                        if abs(percent - last_progress_update['percent']) >= 5:
                            import asyncio
                            # Xabarni yangilash
                            asyncio.create_task(
                                query.message.edit_text(
                                    f"⏳ Video yuklanmoqda...\n\n"
                                    f"{'█' * int(percent/5)}{'░' * (20-int(percent/5))} {percent:.1f}%"
                                )
                            )
                            last_progress_update['time'] = current_time
                            last_progress_update['percent'] = percent
                    except Exception as e:
                        logger.error(f"Progress yangilashda xatolik: {e}")
        
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, f'{temp_filename}.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'socket_timeout': 60,
            'retries': 5,
            'fragment_retries': 5,
            'progress_hooks': [progress_hook],  # Progress callback
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'mweb'],
                    'player_skip': ['webpage'],
                }
            },
            'age_limit': None,
        }
        
        # Cookies fayl mavjud bo'lsa ishlatamiz
        cookies_file = os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt')
        if os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        
        # Pinterest va YouTube uchun turli formatlar
        if is_pinterest:
            # Pinterest uchun yangilanган sozlamalar
            ydl_opts['http_headers'] = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.pinterest.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            # Cookie qo'shish (Pinterest uchun kerak)
            ydl_opts['cookiefile'] = None  # Cookie file yo'q bo'lsa ham ishlaydi
        else:
            # YouTube uchun - sifatga qarab format tanlash
            if quality == 'best':
                ydl_opts['format'] = 'best[ext=mp4]/best'
            else:
                # Tanlangan sifat (240p, 360p, 480p, 720p, 1080p)
                height = quality.replace('p', '')  # '720p' -> '720'
                # Video+audio birgalikda yuklab olish
                ydl_opts['format'] = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'video')
            video_file = ydl.prepare_filename(info)
        
        # Fayl mavjudligini tekshirish
        if not os.path.exists(video_file):
            raise FileNotFoundError(f"Video fayl topilmadi: {video_file}")
        
        # Faylni yuborish
        with open(video_file, 'rb') as video:
            await query.message.reply_video(
                video=video,
                caption=f"📹 {video_title}",
                supports_streaming=True
            )
        
        # Faylni o'chirish
        os.remove(video_file)
        
        # "Yuklanmoqda" xabarini o'chirish
        await query.message.delete()
        
    except Exception as e:
        logger.error(f"Video yuklashda xatolik: {e}")
        
        # Xatolik turini aniqlash
        error_message = "❌ Video yuklashda xatolik yuz berdi."
        
        if "Sign in to confirm" in str(e) or "bot" in str(e).lower():
            error_message = (
                "🤖 YouTube bot detection xatosi!\n\n"
                "YouTube ba'zi videolarni bot deb aniqlayapti.\n\n"
                "✅ Yechimlar:\n"
                "• Boshqa YouTube videoni sinab ko'ring\n"
                "• Bir necha daqiqa kutib qaytadan urinib ko'ring\n"
                "• Video public (ochiq) ekanligiga ishonch hosil qiling\n\n"
                "⚠️ Ba'zi videolar maxsus himoyalangan bo'lishi mumkin."
            )
        elif "403" in str(e) or "forbidden" in str(e).lower():
            error_message = (
                "🚫 Ruxsat berilmadi (403 Forbidden)\n\n"
                "Pinterest ba'zan botlarni bloklashi mumkin.\n\n"
                "Yechimlari:\n"
                "• Biroz kutib qaytadan urinib ko'ring\n"
                "• Boshqa Pinterest link sinab ko'ring\n"
                "• YouTube linkini sinab ko'ring (ishlaydi)\n\n"
                "Pinterest qattiq himoyalangan!"
            )
        elif "timed out" in str(e).lower() or "timeout" in str(e).lower():
            error_message = (
                "⏱️ Video yuklanishida vaqt tugadi.\n\n"
                "Bu quyidagi sabablarga bog'liq bo'lishi mumkin:\n"
                "• Internet tezligi sekin\n"
                "• Server javob bermayapti\n"
                "• Video juda katta\n\n"
                "Iltimos, qaytadan urinib ko'ring yoki boshqa link yuboring."
            )
        elif "http" in str(e).lower():
            error_message = (
                "🌐 Serverga ulanishda muammo.\n\n"
                "Internet ulanishingizni tekshirib, qaytadan urinib ko'ring."
            )
        elif "format" in str(e).lower() or "available" in str(e).lower():
            error_message = (
                "🎬 Bu video uchun mos format topilmadi.\n\n"
                "Bu link ishlamasligi yoki video mavjud emasligi mumkin.\n"
                "Boshqa link yuboring."
            )
        
        await query.message.edit_text(error_message)


async def download_audio(query, url):
    """Audio formatda (MP3) yuklab oladi"""
    try:
        # Unique fayl nomi yaratish
        timestamp = int(time.time())
        temp_filename = f"audio_{timestamp}"
        
        # Pinterest uchun maxsus format
        is_pinterest = 'pinterest.com' in url or 'pin.it' in url
        
        # Progress callback uchun o'zgaruvchilar
        last_progress_update = {'time': 0, 'percent': 0}
        
        def progress_hook(d):
            """Yuklanish jarayonini kuzatish"""
            if d['status'] == 'downloading':
                # Har 3 soniyada bir marta yangilansin
                current_time = time.time()
                if current_time - last_progress_update['time'] >= 3:
                    try:
                        # Foizni hisoblash
                        if 'total_bytes' in d:
                            percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                        elif 'total_bytes_estimate' in d:
                            percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                        else:
                            percent = 0
                        
                        # Faqat foiz o'zgarganda yangilansin
                        if abs(percent - last_progress_update['percent']) >= 5:
                            import asyncio
                            # Xabarni yangilash
                            asyncio.create_task(
                                query.message.edit_text(
                                    f"⏳ Audio yuklanmoqda...\n\n"
                                    f"{'█' * int(percent/5)}{'░' * (20-int(percent/5))} {percent:.1f}%"
                                )
                            )
                            last_progress_update['time'] = current_time
                            last_progress_update['percent'] = percent
                    except Exception as e:
                        logger.error(f"Progress yangilashda xatolik: {e}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, f'{temp_filename}.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 60,
            'retries': 5,
            'fragment_retries': 5,
            'progress_hooks': [progress_hook],  # Progress callback
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'mweb'],
                    'player_skip': ['webpage'],
                }
            },
            'age_limit': None,
        }
        
        # Cookies fayl mavjud bo'lsa ishlatamiz
        cookies_file = os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt')
        if os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        
        
        # FFmpeg mavjud bo'lsa MP3 ga o'giramiz
        try:
            import subprocess
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            audio_ext = 'mp3'
        except:
            # FFmpeg yo'q bo'lsa - oddiy audio formatda yuklab olamiz
            logger.warning("FFmpeg topilmadi, oddiy audio formatda yuklanadi")
            audio_ext = None  # Asl formatda qoladi
        
        # Pinterest uchun qo'shimcha sozlamalar
        if is_pinterest:
            ydl_opts['http_headers'] = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.pinterest.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_title = info.get('title', 'audio')
            downloaded_file = ydl.prepare_filename(info)
        
        # Agar FFmpeg mavjud bo'lsa MP3 fayl, yo'q bo'lsa asl fayl
        if audio_ext == 'mp3':
            audio_file = os.path.join(DOWNLOAD_FOLDER, f"{temp_filename}.mp3")
        else:
            audio_file = downloaded_file
        
        # Fayl mavjudligini tekshirish
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio fayl topilmadi: {audio_file}")
        
        # Fayl hajmini tekshirish (50 MB limit)
        file_size = os.path.getsize(audio_file)
        if file_size > 50 * 1024 * 1024:  # 50 MB
            os.remove(audio_file)
            await query.message.edit_text(
                f"❌ Audio hajmi juda katta!\n\n"
                f"Fayl hajmi: {file_size / (1024*1024):.1f} MB\n"
                f"Telegram limiti: 50 MB\n\n"
                f"Iltimos, qisqaroq yoki past sifatli audio tanlang."
            )
            return
        
        # Faylni yuborish
        with open(audio_file, 'rb') as audio:
            await query.message.reply_audio(
                audio=audio,
                caption=f"🎵 {audio_title}",
                title=audio_title
            )
        
        # Faylni o'chirish
        os.remove(audio_file)
        
        # "Yuklanmoqda" xabarini o'chirish
        await query.message.delete()
        
    except Exception as e:
        logger.error(f"Audio yuklashda xatolik: {e}")
        
        # Xatolik turini aniqlash
        error_message = "❌ Audio yuklashda xatolik yuz berdi."
        
        if "Sign in to confirm" in str(e) or ("bot" in str(e).lower() and "youtube" in str(e).lower()):
            error_message = (
                "🤖 YouTube bot detection xatosi!\n\n"
                "YouTube ba'zi videolarni bot deb aniqlayapti.\n\n"
                "✅ Yechimlar:\n"
                "• Boshqa YouTube videoni sinab ko'ring\n"
                "• Bir necha daqiqa kutib qaytadan urinib ko'ring\n"
                "• Video public (ochiq) ekanligiga ishonch hosil qiling\n\n"
                "⚠️ Ba'zi videolar maxsus himoyalangan bo'lishi mumkin."
            )
        elif "403" in str(e) or "forbidden" in str(e).lower():
            error_message = (
                "🚫 Ruxsat berilmadi (403 Forbidden)\n\n"
                "Pinterest ba'zan botlarni bloklashi mumkin.\n\n"
                "Yechimlari:\n"
                "• Biroz kutib qaytadan urinib ko'ring\n"
                "• Boshqa Pinterest link sinab ko'ring\n"
                "• YouTube linkini sinab ko'ring (ishlaydi)\n\n"
                "Pinterest qattiq himoyalangan!"
            )
        elif "timed out" in str(e).lower() or "timeout" in str(e).lower():
            error_message = (
                "⏱️ Audio yuklanishida vaqt tugadi.\n\n"
                "Bu quyidagi sabablarga bog'liq bo'lishi mumkin:\n"
                "• Internet tezligi sekin\n"
                "• Server javob bermayapti\n"
                "• Fayl juda katta\n\n"
                "Iltimos, qaytadan urinib ko'ring yoki boshqa link yuboring."
            )
        elif "http" in str(e).lower():
            error_message = (
                "🌐 Serverga ulanishda muammo.\n\n"
                "Internet ulanishingizni tekshirib, qaytadan urinib ko'ring."
            )
        elif "ffmpeg" in str(e).lower():
            error_message = (
                "🔧 Audio konvertatsiya qilishda xatolik.\n\n"
                "FFmpeg o'rnatilmaganligidan bo'lishi mumkin.\n"
                "Video formatda yuklab ko'ring."
            )
        
        await query.message.edit_text(error_message)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xatoliklarni qayta ishlaydi"""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Botni ishga tushiradi"""
    # Application yaratish
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube_link))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Botni ishga tushirish
    print("Bot ishga tushdi! ✅")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
