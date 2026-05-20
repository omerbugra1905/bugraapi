from flask import Flask, jsonify, request
from tvDatafeed import TvDatafeed, Interval
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# TradingView login (opsiyonel) - environment'tan al
TV_USERNAME = os.environ.get('TV_USERNAME', None)
TV_PASSWORD = os.environ.get('TV_PASSWORD', None)

# tv client - lazy init
tv = None

def get_tv():
    global tv
    if tv is None:
        if TV_USERNAME and TV_PASSWORD:
            tv = TvDatafeed(TV_USERNAME, TV_PASSWORD)
            logger.info("TV initialized WITH login")
        else:
            tv = TvDatafeed()
            logger.info("TV initialized WITHOUT login")
    return tv

# Sembol → (TV symbol, exchange) mapping
SYMBOLS = {
    'XAUUSD': ('XAUUSD', 'OANDA'),
    'XAGUSD': ('XAGUSD', 'OANDA'),
    'NDX':    ('NAS100USD', 'OANDA'),  # OANDA Nasdaq 100
}

# Alternatif Nasdaq fallback
NDX_ALTERNATIVES = [
    ('NAS100USD', 'OANDA'),
    ('US100',     'CAPITALCOM'),
    ('NQ1!',      'CME_MINI'),
    ('QQQ',       'NASDAQ'),
]

# Interval mapping
INTERVALS = {
    '1m':  Interval.in_1_minute,
    '5m':  Interval.in_5_minute,
    '15m': Interval.in_15_minute,
    '30m': Interval.in_30_minute,
    '1h':  Interval.in_1_hour,
    '2h':  Interval.in_2_hour,
    '4h':  Interval.in_4_hour,
    '1d':  Interval.in_daily,
}

def fetch_candles(sym_key, interval_str, n_bars=200):
    """Çekirdek fetch fonksiyonu — TradingView'dan veri çeker."""
    if interval_str not in INTERVALS:
        return None, f"Invalid interval: {interval_str}"
    
    iv = INTERVALS[interval_str]
    tv_client = get_tv()
    
    # NDX için fallback denemeleri
    if sym_key == 'NDX':
        attempts = NDX_ALTERNATIVES
    elif sym_key in SYMBOLS:
        attempts = [SYMBOLS[sym_key]]
    else:
        return None, f"Unknown symbol: {sym_key}"
    
    last_error = None
    for symbol, exchange in attempts:
        try:
            logger.info(f"Trying {symbol}@{exchange} interval={interval_str}")
            df = tv_client.get_hist(
                symbol=symbol,
                exchange=exchange,
                interval=iv,
                n_bars=n_bars
            )
            if df is None or df.empty:
                last_error = f"Empty data from {symbol}@{exchange}"
                continue
            
            # DataFrame → JSON friendly format
            df = df.reset_index()
            df['datetime'] = df['datetime'].astype(str)
            candles = df.to_dict(orient='records')
            
            return {
                'symbol': sym_key,
                'tv_symbol': symbol,
                'tv_exchange': exchange,
                'interval': interval_str,
                'count': len(candles),
                'values': candles
            }, None
        except Exception as e:
            last_error = f"{symbol}@{exchange}: {str(e)}"
            logger.warning(f"Failed: {last_error}")
            continue
    
    return None, last_error or "All attempts failed"

@app.route('/')
def index():
    return jsonify({
        'service': 'tvfeed-api',
        'status': 'running',
        'endpoints': {
            '/candles/<symbol>/<interval>': 'Single symbol candles (XAUUSD, XAGUSD, NDX)',
            '/all/<interval>': 'All 3 symbols (XAU + XAG + NDX) in one call',
            '/health': 'Health check'
        },
        'symbols': list(SYMBOLS.keys()),
        'intervals': list(INTERVALS.keys())
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/candles/<symbol>/<interval>')
def candles(symbol, interval):
    """Tek sembol için mum verisi."""
    n_bars = int(request.args.get('n', 200))
    n_bars = min(max(n_bars, 10), 5000)
    
    data, err = fetch_candles(symbol.upper(), interval, n_bars)
    if err:
        return jsonify({'error': err, 'symbol': symbol, 'interval': interval}), 404
    return jsonify(data)

@app.route('/all/<interval>')
def all_symbols(interval):
    """3 sembol birden tek call'da."""
    n_bars = int(request.args.get('n', 200))
    n_bars = min(max(n_bars, 10), 5000)
    
    results = {}
    errors = {}
    
    for sym_key in SYMBOLS.keys():
        data, err = fetch_candles(sym_key, interval, n_bars)
        if data:
            results[sym_key] = data
        else:
            errors[sym_key] = err
    
    return jsonify({
        'interval': interval,
        'success': len(results),
        'failed': len(errors),
        'data': results,
        'errors': errors if errors else None
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
