"""
TakeTips IA API - Abel Version
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
import yfinance as yf
import time

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
        return app.open_resource('dashboard.html').read().decode(), 200, {'Content-Type': 'text/html'}

# Constantes
BINANCE_API = "https://fapi.binance.com/fapi/v1"
ALPACA_API_KEY = "pk_live_7890abcdef1234567890"
ALPACA_SECRET_KEY = "sk_live_1234567890abcdef7890"


# Funções de suporte
def get_crypto_price(symbol, interval='1h'):
    """Obtem preço e dados do mercado cripto"""
    url = f"{BINANCE_API}/klines"
    params = {
        'symbol': symbol.upper(),
        'interval': interval,
        'limit': 100
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        return df
    except Exception as e:
        return None

def calculate_indicators(df):
    """Calcula indicadores técnicos"""
    if df is None or df.empty:
        return None
    
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['ema_12'] = df['close'].ewm(span=12).mean()
    df['ema_26'] = df['close'].ewm(span=26).mean()
    df['macd'] = df['ema_12'] - df['ema_26']
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['rsi'] = 100 - (100 / (1 + df['close'].diff().clip(lower=0).rolling(window=14).mean() / 
                                df['close'].diff().clip(upper=0).abs().rolling(window=14).mean()))
    
    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + 2 * bb_std
    df['bb_lower'] = df['bb_middle'] - 2 * bb_std
    
    # ATR (Average True Range)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['atr'] = true_range.rolling(14).mean()
    
    return df

def find_support_resistance(df):
    """Identifica níveis de suporte e resistência"""
    if df is None or df.empty:
        return [], []
    
    # Pivot points
    pivots = []
    for i in range(1, len(df)-1):
        if df.iloc[i]['high'] > df.iloc[i-1]['high'] and df.iloc[i]['high'] > df.iloc[i+1]['high']:
            pivots.append({'type': 'resistance', 'price': df.iloc[i]['high'], 'time': df.iloc[i]['time']})
        elif df.iloc[i]['low'] < df.iloc[i-1]['low'] and df.iloc[i]['low'] < df.iloc[i+1]['low']:
            pivots.append({'type': 'support', 'price': df.iloc[i]['low'], 'time': df.iloc[i]['time']})
    
    return pivots

def generate_trading_signal(df):
    """Gera sinal de trading baseado em múltiplos indicadores"""
    if df is None or df.empty or len(df) < 50:
        return None
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    score = 0
    signals = []
    
    # RSI
    if pd.isna(last.get('rsi')):
        return None
    
    if last['rsi'] < 30:
        score += 2
        signals.append("RSI Sobrevendido (<30)")
    elif last['rsi'] > 70:
        score -= 2
        signals.append("RSI Sobrecomprado (>70)")
    
    # MACD
    if not pd.isna(last.get('macd')) and not pd.isna(last.get('macd_signal')):
        if last['macd'] > last['macd_signal'] and prev['macd'] <= prev['macd_signal']:
            score += 2
            signals.append("Cruzamento MACD Bullish")
        elif last['macd'] < last['macd_signal'] and prev['macd'] >= prev['macd_signal']:
            score -= 2
            signals.append("Cruzamento MACD Bearish")
    
    # Bollinger Bands
    if not pd.isna(last.get('bb_lower')):
        if last['close'] < last['bb_lower']:
            score += 1
            signals.append("Preço abaixo da BB Inferior")
        elif last['close'] > last['bb_upper']:
            score -= 1
            signals.append("Preço acima da BB Superior")
    
    # SMA Crossover
    if not pd.isna(last.get('sma_20')) and not pd.isna(last.get('sma_50')):
        if last['close'] > last['sma_20'] > last['sma_50']:
            score += 1
            signals.append("Tendência Bullish")
        elif last['close'] < last['sma_20'] < last['sma_50']:
            score -= 1
            signals.append("Tendência Bearish")
    
    # Determina o sinal final
    if score >= 4:
        action = "COMPRAR"
        strength = "FORTE"
    elif score >= 2:
        action = "COMPRAR"
        strength = "MODERADO"
    elif score <= -4:
        action = "VENDER"
        strength = "FORTE"
    elif score <= -2:
        action = "VENDER"
        strength = "MODERADO"
    else:
        action = "NEUTRO"
        strength = "FRA CO"
    
    # Níveis de entrada, take profit e stop loss
    atr = last.get('atr', 0) if not pd.isna(last.get('atr')) else (last['high'] - last['low']) * 2
    
    if action == "COMPRAR":
        entry = last['close']
        stop_loss = entry - (atr * 1.5)
        take_profit = entry + (atr * 3)
    elif action == "VENDER":
        entry = last['close']
        stop_loss = entry + (atr * 1.5)
        take_profit = entry - (atr * 3)
    else:
        entry = last['close']
        stop_loss = entry
        take_profit = entry
    
    risk_reward = abs(take_profit - entry) / abs(entry - stop_loss) if abs(entry - stop_loss) > 0 else 0
    
    return {
        'action': action,
        'strength': strength,
        'score': score,
        'signals': signals,
        'entry_price': round(entry, 2),
        'stop_loss': round(stop_loss, 2),
        'take_profit': round(take_profit, 2),
        'risk_reward': round(risk_reward, 2),
        'timestamp': datetime.now().isoformat()
    }

def get_crypto_data(symbol='BTCUSDT', interval='1h', limit=100):
    """Obtem dados de mercado de criptomoedas"""
    try:
        url = f"{BINANCE_API}/klines"
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Converte para DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_avg', 'trades', 'taker_buy_vol', 'taker_buy_quote', 'ignore'
            ])
            
            # Converte tipos
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calcula indicadores
            df = calculate_indicators(df)
            
            # Gera sinal
            signal = generate_trading_signal(df)
            
            # Encontra suporte/resistência
            pivots = find_support_resistance(df)
            
            # ADR (Average Daily Range)
            adr = df['high'].rolling(window=20).mean() - df['low'].rolling(window=20).mean()
            
            # Dados de sessão
            current_time = datetime.utcnow()
            session = "Asian"
            if current_time.hour >= 8 and current_time.hour < 12:
                session = "London"
            elif current_time.hour >= 13 and current_time.hour < 22:
                session = "New York"
            
            return {
                'symbol': symbol.upper(),
                'interval': interval,
                'timestamp': datetime.utcnow().isoformat(),
                'current_price': round(df.iloc[-1]['close'], 2),
                'price_change': round(df.iloc[-1]['close'] - df.iloc[-2]['close'], 2) if len(df) > 1 else 0,
                'price_change_pct': round((df.iloc[-1]['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close'] * 100, 2) if len(df) > 1 else 0,
                'high_24h': round(df['high'].max(), 2),
                'low_24h': round(df['low'].min(), 2),
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
                'signal': signal,
                'support_resistance': pivots[-10:] if pivots else [],
                'session': session,
                'chart_data': df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].to_dict('records')
            }
    except Exception as e:
        return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}

@app.route('/api/v1/analyze', methods=['GET'])
def analyze_crypto():
    """Endpoint para análise de criptomoedas"""
    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval', '1h')
    limit = int(request.args.get('limit', 100))
    
    result = get_crypto_data(symbol, interval, limit)
    return jsonify(result)

@app.route('/api/v1/market', methods=['GET'])
def get_market_overview():
    """Endpoint para visão geral do mercado"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT',
               'SOLUSDT', 'DOTUSDT', 'MATICUSDT', 'LINKUSDT', 'AVAXUSDT']
    
    results = []
    for symbol in symbols:
        try:
            url = f"{BINANCE_API}/ticker/24hr"
            params = {'symbol': symbol}
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            results.append({
                'symbol': symbol,
                'price': float(data.get('lastPrice', 0)),
                'change_24h': float(data.get('priceChangePercent', 0)),
                'volume_24h': float(data.get('volume', 0)),
                'high_24h': float(data.get('highPrice', 0)),
                'low_24h': float(data.get('lowPrice', 0))
            })
        except:
            continue
    
    return jsonify({
        'market_overview': results,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Endpoint de saúde da API"""
    return jsonify({
        'status': 'online',
        'service': 'TakeTips IA API',
        'developer': 'pspconta_01@outlook.com',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'

            @app.route('/analyze', methods=['GET'])
def analyze_page():
    """Página de análise de trading"""
    return app.open_resource('analyze.html').read().decode(), 200, {'Content-Type': 'text/html'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
