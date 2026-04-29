from flask import Flask, jsonify
from flask_cors import CORS

application = Flask(__name__)
CORS(application)

@application.route('/')
def index():
    return "<h1>TakeTips IA - Plataforma de Sinais de Trading</h1><p>Sistema online!</p>", 200

@application.route('/api/v1/health')
def health():
    return jsonify({
        'developer': 'pspconta_01@outlook.com',
        'service': 'TakeTips IA API',
        'status': 'online',
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'version': '1.0.0'
    })

app = application
