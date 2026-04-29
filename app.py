from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "<h1>TakeTips IA - Plataforma de Sinais de Trading</h1><p>Sistema online!</p>", 200

@app.route('/api/v1/health')
def health():
    return jsonify({
        'developer': 'pspconta_01@outlook.com',
        'service': 'TakeTips IA API',
        'status': 'online',
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'version': '1.0.0'
    })
