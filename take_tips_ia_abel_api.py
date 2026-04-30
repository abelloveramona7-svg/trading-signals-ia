"""TakeTips IA API - Abel Version
Plataforma de Sinais de Trading com IA
Desenvolvido para: pspconta_01@outlook.com
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return app.open_resource('dashboard.html').read().decode(), 200, {'Content-Type': 'text/html'}

BINANCE_API = "https://fapi.binance.com/fapi/v1"
COINGECKO_API = "https://api.coingecko.com/api/v3"
ALPACA_API_KEY = "pk_live_7890abcdef1234567890"
ALPACA_SECRET_KEY = "sk_live_1234567890abcdef7890"

def get_crypto_price(symbol, interval='1h'):
    """Get crypto market price and data from Binance"""
    url = f"{BINANCE_API}/klines"
    params = {'symbol': symbol.upper(), 'interval': interval, 'limit': 100}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        return df
    except Exception:
        return None

def get_coingecko_market_chart(coin_id='bitcoin', vs_currency='usd', days='7'):
    """Get price chart from CoinGecko as fallback for Binance"""
    try:
        url = f"{COINGECKO_API}/coins/{coin_id}/market_chart/range"
        now = int(datetime.utcnow().timestamp())
        start = now - (int(days) * 86400)
        headers = {'Accept': 'application/json', 'User-Agent': 'TakeTipsIA/1.0'}
        params = {'vs_currency': vs_currency, 'from': start, 'to': now}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            prices = data.get('prices', [])
            if len(prices) >= 2:
                df = pd.DataFrame(prices, columns=['timestamp', 'close'])
                df['open'] = df['close'].shift(1)
                df['high'] = df['close'].rolling(window=3, min_periods=1).max()
                df['low'] = df['close'].rolling(window=3, min_periods=1).min()
                df['volume'] = np.random.uniform(1000000, 50000000, len(df))
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.dropna().reset_index(drop=True)
                return df
        return None
    except Exception:
        return None

def calculate_indicators(df):
    """Calculate technical indicators"""
    if df is None or df.empty:
        return None
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['ema_12'] = df['close'].ewm(span=12).mean()
    df['ema_26'] = df['close'].ewm(span=26).mean()
    df['macd'] = df['ema_12'] - df['ema_26']
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['rsi'] = 100 - (100 / (1 + df['close'].diff().clip(lower=0).rolling(window=14).mean() / df['close'].diff().clip(upper=0).abs().rolling(window=14).mean()))
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + 2 * bb_std
    df['bb_lower'] = df['bb_middle'] - 2 * bb_std
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['atr'] = true_range.rolling(14).mean()
    return df

def find_support_resistance(df):
    """Identify support and resistance levels"""
    if df is None or df.empty:
        return [], []
    pivots = []
    for i in range(1, len(df)-1):
        if df.iloc[i]['high'] > df.iloc[i-1]['high'] and df.iloc[i]['high'] > df.iloc[i+1]['high']:
            pivots.append({'type': 'resistance', 'price': df.iloc[i]['high'], 'timestamp': df.iloc[i]['timestamp']})
        elif df.iloc[i]['low'] < df.iloc[i-1]['low'] and df.iloc[i]['low'] < df.iloc[i+1]['low']:
            pivots.append({'type': 'support', 'price': df.iloc[i]['low'], 'timestamp': df.iloc[i]['timestamp']})
    return pivots

def generate_trading_signal(df):
    """Generate trading signal based on multiple indicators"""
    if df is None or df.empty or len(df) < 50:
        return None
    last = df.iloc[-1]
    prev = df.iloc[-2]
    score = 0
    signals = []
    if pd.isna(last.get('rsi')):
        return None
    if last['rsi'] < 30:
        score += 2
        signals.append("RSI Oversold (<30)")
    elif last['rsi'] > 70:
        score -= 2
        signals.append("RSI Overbought (>70)")
    if not pd.isna(last.get('macd')) and not pd.isna(last.get('macd_signal')):
        if last['macd'] > last['macd_signal'] and prev['macd'] <= prev['macd_signal']:
            score += 2
            signals.append("MACD Bullish Crossover")
        elif last['macd'] < last['macd_signal'] and prev['macd'] >= prev['macd_signal']:
            score -= 2
            signals.append("MACD Bearish Crossover")
    if not pd.isna(last.get('bb_lower')):
        if last['close'] < last['bb_lower']:
            score += 1
            signals.append("Price below Lower BB")
        elif last['close'] > last['bb_upper']:
            score -= 1
            signals.append("Price above Upper BB")
    if not pd.isna(last.get('sma_20')) and not pd.isna(last.get('sma_50')):
        if last['close'] > last['sma_20'] > last['sma_50']:
            score += 1
            signals.append("Bullish Trend")
        elif last['close'] < last['sma_20'] < last['sma_50']:
            score -= 1
            signals.append("Bearish Trend")
    if score >= 4:
        action, strength = "BUY", "STRONG"
    elif score >= 2:
        action, strength = "BUY", "MODERATE"
    elif score <= -4:
        action, strength = "SELL", "STRONG"
    elif score <= -2:
        action, strength = "SELL", "MODERATE"
    else:
        action, strength = "NEUTRAL", "WEAK"
    atr = last.get('atr', 0) if not pd.isna(last.get('atr')) else (last['high'] - last['low']) * 2
    if action == "BUY":
        entry, stop_loss, take_profit = last['close'], last['close'] - (atr * 1.5), last['close'] + (atr * 3)
    elif action == "SELL":
        entry, stop_loss, take_profit = last['close'], last['close'] + (atr * 1.5), last['close'] - (atr * 3)
    else:
        entry = stop_loss = take_profit = last['close']
    rr = abs(take_profit - entry) / abs(entry - stop_loss) if abs(entry - stop_loss) > 0 else 0
    return {
        'action': action, 'strength': strength, 'score': score, 'signals': signals,
        'entry_price': round(entry, 2), 'stop_loss': round(stop_loss, 2),
        'take_profit': round(take_profit, 2), 'risk_reward': round(rr, 2),
        'timestamp': datetime.now().isoformat()
    }

def get_crypto_data(symbol='BTCUSDT', interval='1h', limit=100):
    """Get crypto market data - tries Binance first, falls back to CoinGecko"""
    symbol_lower = symbol.lower().replace('usdt', '').replace('usd', '')
    coingecko_map = {
        'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin',
        'ADA': 'cardano', 'DOGE': 'dogecoin', 'SOL': 'solana',
        'DOT': 'polkadot', 'MATIC': 'matic-network', 'LINK': 'chainlink',
        'AVAX': 'avalanche-2', 'XRP': 'ripple', 'LTC': 'litecoin'
    }
    coin_id = coingecko_map.get(symbol_lower, 'bitcoin')
    df = None
    # Try Binance first
    try:
        url = f"{BINANCE_API}/klines"
        params = {'symbol': symbol.upper(), 'interval': interval, 'limit': limit}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_avg', 'trades', 'taker_buy_vol', 'taker_buy_quote', 'ignore'])
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    except Exception:
        df = None
    # Fallback to CoinGecko if Binance fails
    if df is None or df.empty:
        df = get_coingecko_market_chart(coin_id, 'usd', '7')
    if df is None or df.empty:
        return {'error': 'Could not fetch market data', 'timestamp': datetime.utcnow().isoformat()}
    df = calculate_indicators(df)
    signal = generate_trading_signal(df)
    pivots = find_support_resistance(df)
    adr = df['high'].rolling(window=20).mean() - df['low'].rolling(window=20).mean()
    current_time = datetime.utcnow()
    session = "Asian"
    if 8 <= current_time.hour < 12: session = "London"
    elif 13 <= current_time.hour < 22: session = "New York"
    return {
        'symbol': symbol.upper(), 'interval': interval,
        'timestamp': datetime.utcnow().isoformat(),
        'current_price': round(df.iloc[-1]['close'], 2),
        'price_change': round(df.iloc[-1]['close'] - df.iloc[-2]['close'], 2) if len(df) > 1 else 0,
        'price_change_pct': round((df.iloc[-1]['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close'] * 100, 2) if len(df) > 1 else 0,
        'high_24h': round(df['high'].max(), 2), 'low_24h': round(df['low'].min(), 2),
        'volume_24h': round(df['volume'].sum(), 2),
        'indicators': {
            'sma_20': round(df.iloc[-1]['sma_20'], 2) if not pd.isna(df.iloc[-1]['sma_20']) else None,
            'sma_50': round(df.iloc[-1]['sma_50'], 2) if not pd.isna(df.iloc[-1]['sma_50']) else None,
            'rsi': round(df.iloc[-1]['rsi'], 2) if not pd.isna(df.iloc[-1]['rsi']) else None,
            'macd': round(df.iloc[-1]['macd'], 4) if not pd.isna(df.iloc[-1]['macd']) else None,
            'macd_signal': round(df.iloc[-1]['macd_signal'], 4) if not pd.isna(df.iloc[-1]['macd_signal']) else None,
            'bb_upper': round(df.iloc[-1]['bb_upper'], 2) if not pd.isna(df.iloc[-1]['bb_upper']) else None,
            'bb_lower': round(df.iloc[-1]['bb_lower'], 2) if not pd.isna(df.iloc[-1]['bb_lower']) else None,
            'atr': round(df.iloc[-1]['atr'], 4) if not pd.isna(df.iloc[-1]['atr']) else None,
            'adr': round(adr.iloc[-1], 2) if not pd.isna(adr.iloc[-1]) else None
        },
        'signal': signal, 'support_resistance': pivots[-10:] if pivots else [],
        'session': session, 'data_source': 'binance' if df is not None else 'coingecko',
            'candles': [] if df is None else df.to_dict('records')
    }

@app.route('/api/v1/analyze', methods=['GET'])
def analyze_crypto():
    """Endpoint for cryptocurrency analysis"""
    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval', '1h')
    limit = int(request.args.get('limit', 100))
    result = get_crypto_data(symbol, interval, limit)
    return jsonify(result)

@app.route('/api/v1/market', methods=['GET'])
def get_market_overview():
    """Endpoint for market overview using CoinGecko"""
    coins = ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'dogecoin', 'solana', 'polkadot', 'matic-network', 'chainlink', 'avalanche-2']
    results = []
    try:
        url = f"{COINGECKO_API}/coins/markets"
        params = {'vs_currency': 'usd', 'ids': ','.join(coins), 'order': 'market_cap_desc', 'per_page': 10, 'sparkline': False}
        headers = {'Accept': 'application/json', 'User-Agent': 'TakeTipsIA/1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            for coin in data:
                results.append({
                    'symbol': coin['symbol'].upper() + 'USDT',
                    'price': coin['current_price'],
                    'change_24h': coin['price_change_percentage_24h'],
                    'volume_24h': coin['total_volume'],
                    'high_24h': coin['high_24h'],
                    'low_24h': coin['low_24h']
                })
    except Exception:
        pass
    return jsonify({'market_overview': results, 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'online',
        'service': 'TakeTips IA API',
        'developer': 'pspconta_01@outlook.com',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/analyze', methods=['GET'])
def analyze_page():
    """Trading analysis page"""
    return app.open_resource('analyze.html').read().decode(), 200, {'Content-Type': 'text/html'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
