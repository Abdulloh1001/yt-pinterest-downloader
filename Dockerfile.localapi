# Telegram Local Bot API Server
# Bu Railway'da alohida service sifatida ishga tushadi

FROM aiogram/telegram-bot-api:latest

# Working directory
WORKDIR /app

# Port expose qilish
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Local API serverni ishga tushirish
# Railway environment variables avtomatik o'qiladi
CMD ["sh", "-c", "telegram-bot-api --api-id=${TELEGRAM_API_ID} --api-hash=${TELEGRAM_API_HASH} --local --http-port=8081 --verbosity=1"]
