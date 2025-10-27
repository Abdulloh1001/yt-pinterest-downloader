# Local Bot API Service for Railway

Bu folder **telegram-local-api** service uchun.

## Railway Setup:

1. **Service Settings** → **Source**
2. **Root Directory:** `local-api`
3. **Builder:** Dockerfile (avtomatik)

## Environment Variables:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

## Port:

- Internal: 8081
- Private URL: `http://telegram-local-api.railway.internal:8081`
