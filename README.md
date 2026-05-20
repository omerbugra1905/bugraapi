# TVFeed API

TradingView verilerini REST API olarak sunan basit servis.

## Endpoints

- `GET /` - Servis bilgisi
- `GET /health` - Sağlık kontrolü
- `GET /candles/{symbol}/{interval}?n=200` - Tek sembol mum verisi
- `GET /all/{interval}?n=200` - 3 sembol birden (XAUUSD + XAGUSD + NDX)

## Semboller
- `XAUUSD` - Altın (OANDA)
- `XAGUSD` - Gümüş (OANDA)
- `NDX` - Nasdaq 100 (OANDA NAS100USD veya fallback)

## Interval'ler
1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d

## Örnek
```
GET /candles/XAUUSD/1h
GET /all/15m?n=100
```

## Deploy (Render.com)
1. GitHub'a push et
2. Render → New Web Service → bu repo'yu seç
3. Build: pip install -r requirements.txt
4. Start: gunicorn app:app
5. (Opsiyonel) Environment: TV_USERNAME, TV_PASSWORD

## Lokal çalıştır
```
pip install -r requirements.txt
python app.py
```
