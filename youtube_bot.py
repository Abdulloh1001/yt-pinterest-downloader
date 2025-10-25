import os
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
from dotenv import load_dotenv
import instaloader
import requests

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
        "📌 <b>Pinterest</b> (pinterest.com, pin.it)\n"
        "📸 <b>Instagram</b> (instagram.com)\n"
        "   • Reels 🎬\n"
        "   • Posts 📷\n"
        "   • Carousel 🖼️\n"
        "   • Stories 📱\n"
        "   • Highlights ✨\n\n"
        "Men sizga video yoki audio formatida yuklab beraman!\n\n"
        "🎬 Video (MP4 format)\n"
        "🎵 Audio (MP3 format)",
        parse_mode='HTML'
    )


async def handle_instagram_with_instaloader(update: Update, url: str):
    """Instagram postlarni instaloader bilan yuklab beradi"""
    try:
        # Shortcode ni URL'dan ajratib olamiz
        # URL formatlar: /p/SHORTCODE/, /reel/SHORTCODE/, /stories/username/ID/
        shortcode = None
        
        if '/p/' in url or '/reel/' in url:
            parts = url.split('/')
            for i, part in enumerate(parts):
                if part in ['p', 'reel'] and i + 1 < len(parts):
                    shortcode = parts[i + 1].split('?')[0]  # Query parametrlarni olib tashlaymiz
                    break
        
        if not shortcode:
            logger.warning(f"Instagram shortcode topilmadi: {url}")
            return False
        
        logger.info(f"Instagram shortcode: {shortcode}")
        
        # Instaloader yaratish
        L = instaloader.Instaloader(
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
        )
        
        # Post olish
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        logger.info(f"Instagram post: {post.owner_username}, video={post.is_video}, media_count={post.mediacount}")
        
        # Carousel yoki bitta media?
        if post.mediacount > 1:
            # Carousel
            await update.message.reply_text(f"📸 Carousel: {post.mediacount} ta media yuklanmoqda...")
            
            count = 0
            for idx, node in enumerate(post.get_sidecar_nodes()):
                try:
                    if node.is_video:
                        # Video
                        video_url = node.video_url
                        await update.message.reply_video(video=video_url, caption=f"✅ {idx+1}/{post.mediacount}")
                        count += 1
                    else:
                        # Rasm
                        photo_url = node.display_url
                        await update.message.reply_photo(photo=photo_url)
                        count += 1
                except Exception as e:
                    logger.error(f"Carousel item {idx} yuborishda xatolik: {e}")
            
            if count > 0:
                await update.message.reply_text(f"✅ {count}/{post.mediacount} ta media yuklandi!")
                return True
        else:
            # Bitta media
            if post.is_video:
                # Video
                video_url = post.video_url
                await update.message.reply_video(video=video_url, caption="✅ Instagram video")
                return True
            else:
                # Rasm
                photo_url = post.url
                await update.message.reply_photo(photo=photo_url, caption="✅ Instagram rasmi")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Instaloader xatolik: {e}")
        return False


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Video linkini qabul qiladi va formatni tanlash tugmalarini ko'rsatadi"""
    url = update.message.text
    
    # Platform'ni aniqlash
    is_youtube = 'youtube.com' in url or 'youtu.be' in url
    is_pinterest = 'pinterest.com' in url or 'pin.it' in url
    # Instagram - turli URL formatlarini qo'llab-quvvatlash
    is_instagram = (
        'instagram.com' in url or 
        'instagr.am' in url or 
        'instagram.com/s/' in url or  # Highlights short URL
        'instagram.com/stories/' in url  # Stories/Highlights
    )
    
    if not (is_youtube or is_pinterest or is_instagram):
        await update.message.reply_text(
            "❌ Noto'g'ri link!\n\n"
            "Quyidagi platformalardan link yuboring:\n"
            "📺 YouTube (youtube.com, youtu.be)\n"
            "📌 Pinterest (pinterest.com, pin.it)\n"
            "📸 Instagram (instagram.com)"
        )
        return
    
    # URLni context'ga saqlash
    context.user_data['youtube_url'] = url
    
    # Platform nomini aniqlash
    if is_youtube:
        platform = "YouTube"
    elif is_pinterest:
        platform = "Pinterest"
    elif is_instagram:
        platform = "Instagram"
    else:
        platform = "Unknown"
    
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
    
    # Instagram uchun maxsus tekshirish - instaloader bilan yuklab berish
    if is_instagram:
        try:
            await update.message.reply_text("🔍 Instagram media tekshirilmoqda...")
            
            # Instaloader bilan yuklash
            success = await handle_instagram_with_instaloader(update, url)
            
            if success:
                logger.info("Instagram instaloader bilan muvaffaqiyatli yuklandi")
                return
            else:
                # Instaloader ishlamadi, yt-dlp bilan urinib ko'ramiz
                logger.warning("Instaloader ishlamadi, yt-dlp bilan sinab ko'rilmoqda...")
                await update.message.reply_text("⚠️ Instaloader ishlamadi, boshqa usul bilan sinab ko'ramiz...")
                
        except Exception as e:
            logger.error(f"Instagram instaloader xatolik: {e}")
            await update.message.reply_text("⚠️ Xatolik yuz berdi, boshqa usul bilan sinab ko'ramiz...")
            
            # Media type tekshirish (cookies bilan)
            ydl_opts_check = {
                'quiet': True,
                'no_warnings': True,
                'ignore_no_formats_error': True,  # Rasm postlar uchun xatolikni ignore qilish
            }
            
            # Cookies fayl mavjud bo'lsa ishlatamiz (Instagram uchun ham)
            cookies_file = os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt')
            if os.path.exists(cookies_file):
                ydl_opts_check['cookiefile'] = cookies_file
                # Instagram uchun cookies parameter ham kerak
                logger.info("Cookies fayli Instagram uchun ishlatilmoqda")
            
            with yt_dlp.YoutubeDL(ydl_opts_check) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Story/Highlights URL'larni avtomatik yuklash (format tanlash yo'q)
                is_story = '/stories/' in url or '/s/' in url
                
                if is_story:
                    # Story/Highlights - to'g'ridan-to'g'ri video sifatida yuklaymiz
                    await update.message.reply_text("📱 Story/Highlights yuklanmoqda...")
                    
                    # Video URL mavjudmi?
                    video_url = info.get('url')
                    if video_url and info.get('vcodec') != 'none':
                        # Video
                        try:
                            await update.message.reply_video(video=video_url, caption="✅ Instagram Story/Highlights")
                            return
                        except Exception as e:
                            logger.error(f"Story video yuborishda xatolik: {e}")
                    
                    # Rasm bo'lsa
                    photo_url = info.get('thumbnail') or info.get('url')
                    if photo_url:
                        try:
                            await update.message.reply_photo(photo=photo_url, caption="✅ Instagram Story/Highlights")
                            return
                        except Exception as e:
                            logger.error(f"Story rasm yuborishda xatolik: {e}")
                    
                    # Fallback: format selection
                    await update.message.reply_text("❌ Story/Highlights avtomatik yuklanmadi. Format tanlang:")
                    # Format selection'ga o'tamiz
                
                # Video formatlar mavjudligini tekshirish
                formats = info.get('formats', [])
                has_video = any(f.get('vcodec') != 'none' for f in formats)
                
                # Agar video yo'q (faqat rasm) bo'lsa
                if not has_video or info.get('ext') in ['jpg', 'jpeg', 'png', 'webp']:
                    # To'g'ridan-to'g'ri rasm sifatida yuklaymiz
                    await update.message.reply_text("📸 Instagram rasmini yuklayman...")
                    
                    # Rasm URL'ini olamiz
                    if 'entries' in info:
                        # Carousel - har bir rasmni yuklaymiz
                        count = 0
                        logger.info(f"Carousel topildi: {len(info['entries'])} ta entry")
                        
                        for idx, entry in enumerate(info['entries'][:10]):  # Maksimum 10 ta rasm
                            # Entry har xil formatda bo'lishi mumkin
                            photo_url = None
                            
                            # Debug: entry strukturasini log qilamiz
                            logger.info(f"Entry {idx} keys: {list(entry.keys())}")
                            
                            # 1. Direct URL
                            if entry.get('url'):
                                photo_url = entry.get('url')
                                logger.info(f"Entry {idx}: Direct URL topildi")
                            # 2. Thumbnails array ichida eng yuqori sifatli rasm
                            elif entry.get('thumbnails'):
                                thumbnails = entry.get('thumbnails', [])
                                if thumbnails:
                                    # Eng katta o'lchamdagi rasmni topamiz
                                    best_thumb = max(thumbnails, key=lambda t: t.get('width', 0) * t.get('height', 0))
                                    photo_url = best_thumb.get('url')
                                    logger.info(f"Entry {idx}: Thumbnail topildi (best quality)")
                            # 3. Bitta thumbnail
                            elif entry.get('thumbnail'):
                                photo_url = entry.get('thumbnail')
                                logger.info(f"Entry {idx}: Single thumbnail topildi")
                            
                            if photo_url:
                                try:
                                    await update.message.reply_photo(photo=photo_url)
                                    count += 1
                                    logger.info(f"Entry {idx}: Rasm muvaffaqiyatli yuborildi")
                                except Exception as e:
                                    logger.error(f"Entry {idx}: Rasm yuborishda xatolik: {e}")
                                    # URL'ni debug uchun log qilamiz
                                    logger.debug(f"Failed photo URL: {photo_url}")
                            else:
                                logger.warning(f"Entry {idx}: Hech qanday URL topilmadi")
                        
                        if count > 0:
                            await update.message.reply_text(f"✅ {count} ta rasm yuklandi!")
                            return  # Muvaffaqiyatli yuklandi, to'xtaymiz
                        else:
                            # Carousel rasm topilmadi - lekin xato bo'lmasa format selection'ga o'tmaymiz
                            logger.warning("Carousel entries mavjud lekin photo_url topilmadi")
                            # Fallback: entries ichidagi video formatlarni tekshiramiz
                            video_found = False
                            for entry in info['entries'][:1]:  # Birinchi entry'ni tekshiramiz
                                if entry.get('vcodec') != 'none':
                                    video_found = True
                                    break
                            
                            if not video_found:
                                await update.message.reply_text("❌ Carousel media topilmadi.")
                                return  # Format selection'ga o'tmaymiz
                            # Aks holda, format selection'ga o'tamiz
                    else:
                        # Bitta rasm
                        photo_url = (
                            info.get('url') or 
                            info.get('thumbnail') or
                            (info.get('thumbnails', [{}])[0].get('url') if info.get('thumbnails') else None)
                        )
                        if photo_url:
                            await update.message.reply_photo(photo=photo_url, caption="✅ Instagram rasmi")
                            return  # Muvaffaqiyatli yuklandi
                        else:
                            await update.message.reply_text("❌ Rasm URL topilmadi. Video formatni sinab ko'ring.")
                            # Videoga o'tishga ruxsat berish (return yo'q)
                    
        except Exception as e:
            logger.error(f"Instagram media type tekshirishda xatolik: {e}")
            # Xato bo'lsa, odatdagi formatga o'tamiz
    
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
        await download_video(query, url, quality, context)
    elif callback_data == 'audio':
        await query.edit_message_text("⏳ Audio yuklanmoqda... Iltimos kuting...")
        await download_audio(query, url, context)


async def show_quality_options(query, url, context):
    """Video sifatlarini ko'rsatadi va foydalanuvchi tanlaydi"""
    try:
        await query.edit_message_text("🔍 Mavjud sifatlar tekshirilmoqda...")
        
        # yt-dlp orqali mavjud formatlarni olish (format tanlash SHART EMAS)
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'age_limit': None,
            'noplaylist': True,
            # format belgisi yo'q - yt-dlp barcha formatlarni qaytaradi
        }
        
        # Cookies fayl mavjud bo'lsa ishlatamiz
        cookies_file = os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt')
        if os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
            logger.info("YouTube cookies fayli topildi va ishlatilmoqda")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            # Agar formatlar bo'lmasa, xato
            if not formats:
                await query.edit_message_text("❌ Video formatlar topilmadi. Havola noto'g'ri yoki video mavjud emas.")
                return
        
        # Video+Audio formatlarini filterlash (m3u8 ham qo'llab-quvvatlash)
        quality_map = {}
        for f in formats:
            height = f.get('height')
            filesize = f.get('filesize') or f.get('filesize_approx')
            
            # Faqat video formatlar (audio yo'q)
            if height and f.get('vcodec') != 'none':
                quality_key = f"{height}p"
                
                # Agar hajm ma'lum bo'lsa, eng kichik hajmli formatni saqlash
                if quality_key not in quality_map:
                    quality_map[quality_key] = {
                        'size': filesize if filesize else 0,
                        'height': height,
                        'protocol': f.get('protocol', 'https')
                    }
                elif filesize and filesize < quality_map[quality_key]['size']:
                    quality_map[quality_key] = {
                        'size': filesize,
                        'height': height,
                        'protocol': f.get('protocol', 'https')
                    }
        
        # Tugmalarni yaratish
        keyboard = []
        
        # Quality map'dan avtomatik sort qilib olish (pastdan yuqoriga)
        sorted_qualities = sorted(quality_map.items(), key=lambda x: x[1]['height'])
        
        for quality, info in sorted_qualities:
            size = info['size']
            
            # Hajm ma'lum bo'lsa tekshiramiz
            if size > 0:
                size_mb = size / (1024 * 1024)
                # Faqat 50MB dan kichik bo'lganlarni ko'rsatish
                if size_mb <= 50:
                    button_text = f"📹 {quality} • {size_mb:.1f} MB"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"video_{quality}")])
            else:
                # Hajm noma'lum (m3u8 format) - baribir ko'rsatamiz
                button_text = f"📹 {quality}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"video_{quality}")])
        
        if not keyboard:
            await query.edit_message_text(
                "❌ Afsuski, mavjud video formatlari topilmadi.\n"
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


async def download_video(query, url, quality='best', context=None):
    """Video formatda yuklab oladi"""
    try:
        await query.edit_message_text("🔍 Video ma'lumotlari olinmoqda...")
        
        # Pinterest/Instagram uchun DIRECT URL ishlatamiz (tezroq!)
        # YouTube uchun ishlamaydi (Telegram API rad etadi)
        is_pinterest = 'pinterest.com' in url or 'pin.it' in url
        is_instagram = 'instagram.com' in url or 'instagr.am' in url
        
        # Faqat Pinterest/Instagram uchun direct URL
        if context and (is_pinterest or is_instagram):
            try:
                # Video URL'ni olish (yuklab olmasdan)
                ydl_opts_info = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': f'best[height<={quality[:-1]}]' if quality != 'best' else 'best',
                }
                
                # Cookies fayl mavjud bo'lsa ishlatamiz
                cookies_file = os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt')
                if os.path.exists(cookies_file):
                    ydl_opts_info['cookiefile'] = cookies_file
                
                with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                    info = ydl.extract_info(url, download=False)
                    video_url = info.get('url')
                    title = info.get('title', 'Video')
                    filesize = info.get('filesize') or info.get('filesize_approx', 0)
                    
                    # Agar URL mavjud bo'lsa, direct yuboramiz
                    if video_url:
                        size_mb = filesize / (1024*1024) if filesize else 0
                        logger.info(f"Direct URL orqali yuborilmoqda: {title} ({size_mb:.1f}MB)")
                        await query.edit_message_text(
                            f"📤 Video to'g'ridan-to'g'ri yuborilmoqda...\n"
                            f"📊 Hajm: {size_mb:.1f} MB" if size_mb > 0 else "📤 Video yuborilmoqda..."
                        )
                        
                        user_id = query.message.chat_id
                        message_id = query.message.message_id
                        
                        # Direct URL orqali yuborish
                        await context.bot.send_video(
                            chat_id=user_id,
                            video=video_url,
                            caption=f"✅ {title}\n\n📊 Sifat: {quality}",
                            supports_streaming=True,
                            read_timeout=120,
                            write_timeout=120,
                        )
                        
                        # Eski xabarni o'chirish
                        await query.message.delete()
                        
                        # LOG_CHANNEL'ga yuborish
                        if LOG_CHANNEL:
                            username = query.from_user.username
                            user_link = f"@{username}" if username else f"User {query.from_user.id}"
                            await context.bot.send_message(
                                chat_id=LOG_CHANNEL,
                                text=f"📹 Video yuklandi (DIRECT)\n👤 {user_link}\n🔗 {url}\n📊 {quality}"
                            )
                        
                        logger.info(f"Video DIRECT URL orqali yuborildi: {title}")
                        return  # Direct ishlasa, keyingi kodga o'tmaymiz
                    
            except Exception as e:
                logger.warning(f"Direct URL yuborish ishlamadi, streaming'ga o'tilmoqda: {e}")
        
        # Agar DIRECT ishlamasa, STREAMING orqali yuklaymiz (eski usul)
        # Lekin AVVAL hajmni tekshiramiz!
        await query.edit_message_text("🔍 Video hajmi tekshirilmoqda...")
        
        # Video hajmini olish (yuklab olmasdan)
        ydl_opts_check = {
            'quiet': True,
            'no_warnings': True,
            'format': f'best[height<={quality[:-1]}]' if quality != 'best' else 'best',
        }
        
        cookies_file = os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt')
        if os.path.exists(cookies_file):
            ydl_opts_check['cookiefile'] = cookies_file
        
        with yt_dlp.YoutubeDL(ydl_opts_check) as ydl:
            info_check = ydl.extract_info(url, download=False)
            filesize_check = info_check.get('filesize') or info_check.get('filesize_approx', 0)
            
            # Agar 50MB dan katta bo'lsa, xabar beramiz
            if filesize_check > 50 * 1024 * 1024:
                size_mb = filesize_check / (1024 * 1024)
                await query.edit_message_text(
                    f"❌ Video juda katta!\n\n"
                    f"📊 Video hajmi: {size_mb:.1f} MB\n"
                    f"📊 Telegram limiti: 50 MB\n\n"
                    f"💡 Pastroq sifatni tanlang:\n"
                    f"• 480p yoki 360p ni sinab ko'ring"
                )
                logger.warning(f"Video juda katta: {size_mb:.1f}MB > 50MB")
                return
        
        await query.edit_message_text("⏳ Video serverga yuklanmoqda...")

        
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
                # Best format - faqat height bo'yicha
                ydl_opts['format'] = 'best'
            else:
                # Tanlangan sifat (240p, 360p, 480p, 720p, 1080p)
                height = quality.replace('p', '')  # '720p' -> '720'
                # Oddiy format selector - faqat height
                ydl_opts['format'] = f'best[height<={height}]'
        
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


async def download_audio(query, url, context=None):
    """Audio formatda (MP3) yuklab oladi"""
    try:
        await query.edit_message_text("🔍 Audio ma'lumotlari olinmoqda...")
        
        # Pinterest/Instagram uchun DIRECT URL ishlatamiz (tezroq!)
        # YouTube uchun ishlamaydi (Telegram API rad etadi)
        is_pinterest = 'pinterest.com' in url or 'pin.it' in url
        is_instagram = 'instagram.com' in url or 'instagr.am' in url
        
        # Faqat Pinterest/Instagram uchun direct URL
        if context and (is_pinterest or is_instagram):
            try:
                # Audio URL'ni olish (yuklab olmasdan)
                ydl_opts_info = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': 'bestaudio/best',
                }
                
                # Cookies fayl mavjud bo'lsa ishlatamiz
                cookies_file = os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt')
                if os.path.exists(cookies_file):
                    ydl_opts_info['cookiefile'] = cookies_file
                
                with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                    info = ydl.extract_info(url, download=False)
                    audio_url = info.get('url')
                    title = info.get('title', 'Audio')
                    filesize = info.get('filesize') or info.get('filesize_approx', 0)
                    
                    # Agar URL mavjud bo'lsa, DOIM direct yuboramiz (hajmga qaramay)
                    if audio_url:
                        size_mb = filesize / (1024*1024) if filesize else 0
                        logger.info(f"Direct URL orqali yuborilmoqda (audio): {title} ({size_mb:.1f}MB)")
                        await query.edit_message_text(
                            f"📤 Audio to'g'ridan-to'g'ri yuborilmoqda...\n"
                            f"📊 Hajm: {size_mb:.1f} MB" if size_mb > 0 else "📤 Audio yuborilmoqda..."
                        )
                        
                        user_id = query.message.chat_id
                        
                        # Direct URL orqali yuborish (audio)
                        await context.bot.send_audio(
                            chat_id=user_id,
                            audio=audio_url,
                            caption=f"✅ {title}",
                            title=title,
                            read_timeout=120,
                            write_timeout=120,
                        )
                        
                        # Eski xabarni o'chirish
                        await query.message.delete()
                        
                        # LOG_CHANNEL'ga yuborish
                        if LOG_CHANNEL:
                            username = query.from_user.username
                            user_link = f"@{username}" if username else f"User {query.from_user.id}"
                            await context.bot.send_message(
                                chat_id=LOG_CHANNEL,
                                text=f"🎵 Audio yuklandi (DIRECT)\n👤 {user_link}\n🔗 {url}"
                            )
                        
                        logger.info(f"Audio DIRECT URL orqali yuborildi: {title}")
                        return  # Direct ishlasa, keyingi kodga o'tmaymiz
                    
            except Exception as e:
                logger.warning(f"Direct URL yuborish ishlamadi (audio), streaming'ga o'tilmoqda: {e}")
        
        # Agar DIRECT ishlamasa, STREAMING orqali yuklaymiz (eski usul)
        # Lekin AVVAL hajmni tekshiramiz!
        await query.edit_message_text("🔍 Audio hajmi tekshirilmoqda...")
        
        # Audio hajmini olish (yuklab olmasdan)
        ydl_opts_check = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
        }
        
        cookies_file = os.path.join(os.path.dirname(__file__), 'youtube_cookies.txt')
        if os.path.exists(cookies_file):
            ydl_opts_check['cookiefile'] = cookies_file
        
        with yt_dlp.YoutubeDL(ydl_opts_check) as ydl:
            info_check = ydl.extract_info(url, download=False)
            filesize_check = info_check.get('filesize') or info_check.get('filesize_approx', 0)
            
            # Agar 50MB dan katta bo'lsa, xabar beramiz
            if filesize_check > 50 * 1024 * 1024:
                size_mb = filesize_check / (1024 * 1024)
                await query.edit_message_text(
                    f"❌ Audio juda katta!\n\n"
                    f"📊 Audio hajmi: {size_mb:.1f} MB\n"
                    f"📊 Telegram limiti: 50 MB\n\n"
                    f"💡 Bu video juda uzun.\n"
                    f"Qisqaroq qism linkini yuboring."
                )
                logger.warning(f"Audio juda katta: {size_mb:.1f}MB > 50MB")
                return
        
        await query.edit_message_text("⏳ Audio serverga yuklanmoqda...")
        
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Error handler
    application.add_error_handler(error_handler)
    # Railway uchun optimizatsiya - direct URL yuborish
        # Bu server orqali emas, to'g'ridan-to'g'ri foydalanuvchiga yuboradi
    application.bot_data['use_direct_download'] = True
    # Botni ishga tushirish
    print("Bot ishga tushdi! ✅")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
