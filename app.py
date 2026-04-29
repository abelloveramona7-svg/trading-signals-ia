from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import random
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Dados simulados
ASSETS = {
    'EUR/USD': {'entrada': 1.1705, 'take_profit': 1.1656, 'stop_loss': 1.1728, 'risk_reward': '1:2.08'},
    'BTC/USD': {'entrada': 95234, 'take_profit': 94500, 'stop_loss': 95800, 'risk_reward': '1:1.95'},
    'GBP/USD': {'entrada': 1.2750, 'take_profit': 1.2700, 'stop_loss': 1.2810, 'risk_reward': '1:2.00'},
    'JPY/USD': {'entrada': 0.00680, 'take_profit': 0.00675, 'stop_loss': 0.00685, 'risk_reward': '1:1.80'}
}

NOTICIAS = [
    {'hora': '11:00', 'moeda': 'USD', 'evento': 'CB Consumer Confidence', 'impacto': 'MÉDIO'},
    {'hora': '14:30', 'moeda': 'EUR', 'evento': 'Jobless Claims', 'impacto': 'ALTO'},
    {'hora': '09:00', 'moeda': 'GBP', 'evento': 'Retail Sales', 'impacto': 'MÉDIO'}
]

@app.route('/')
def index():
    return '''{HTML_CONTENT}'''

@app.route('/api/analise')
def get_analise():
    assets = list(ASSETS.keys())
    ativo = random.choice(assets)
    dados = ASSETS[ativo]
    
    return jsonify({
        'ativo': ativo,
        'entrada': dados['entrada'],
        'take_profit': dados['take_profit'],
        'stop_loss': dados['stop_loss'],
        'risk_reward': dados['risk_reward'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/noticias')
def get_noticias():
    return jsonify({'noticias': NOTICIAS})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Trading Signals IA is running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)), debug=False)

HTML_CONTENT = '''<!DOCTYPE html>
<html>
<!-- Seu HTML aqui -->
</html>
'''
