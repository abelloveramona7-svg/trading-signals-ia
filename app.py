from flask import Flask, jsonify, render_template
from flask_cors import CORS
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Try to load HTML file content
html_content = None
try:
    # Try different possible locations
    possible_paths = [
        Path(__file__).parent / 'index.html',
        Path('/app/index.html'),
        Path('./index.html'),
    ]
    for path in possible_paths:
        if path.exists():
            html_content = path.read_text()
            break
except Exception as e:
    html_content = f"<h1>Error loading index.html: {str(e)}</h1>"

# Fallback HTML
if not html_content:
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>TakeTips IA - Trading Signals Platform</title>
</head>
<body>
    <h1>TakeTips IA - Plataforma de Sinais de Trading</h1>
    <p>Plataforma está funcionando!</p>
</body>
</html>"""

@app.route('/')
def index():
    return html_content, 200, {'Content-Type': 'text/html'}

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
