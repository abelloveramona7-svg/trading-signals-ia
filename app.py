from flask import Flask, jsonify
from flask_cors import CORS

application = Flask(__name__)
CORS(application)

@app.route('/')
def index():
    html_content = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TakeTips IA - Plataforma de Sinais de Trading</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; margin: 0; padding: 20px; text-align: center; }
        h1 { color: #00d4ff; }
        p { color: #aaa; }
    </style>
</head>
<body>
    <h1>TakeTips IA - Plataforma de Sinais de Trading</h1>
    <p>Sistema online</p>
    <p>API: /api/v1/health</p>
</body>
</html>'''
    return html_content, 200

@app.route('/api/v1/health')
def health():
    return jsonify({
        'developer': 'pspconta_01@outlook.com',
        'service': 'TakeTips IA API',
        'status': 'online',
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'version': '1.0.0'
    })

app = application
