from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "<h1>TakeTips IA - Plataforma de Sinais de Trading</h1><p>Sistema está funcionando!</p>"

@app.route('/api/v1/health')
def health():
    return jsonify({
        'developer': 'pspconta_01@outlook.com',
        'service': 'TakeTips IA API',
        'status': 'online',
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
