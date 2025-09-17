#!/usr/bin/env python3
"""
Quick deployment script using SSH
"""

import subprocess
import sys
import time

def run_command(cmd, check=True):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def main():
    server = "192.168.1.246"
    user = "root"
    password = "3646287"

    print(f"=== Quick Deploy to {server} ===")

    # Check if sshpass is available
    try:
        subprocess.run(["sshpass", "-V"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing sshpass...")
        run_command("brew install sshpass")

    # Upload the setup script
    print("Uploading setup script...")
    with open('/tmp/setup_remote.sh', 'w') as f:
        f.write('''#!/bin/bash
# Setup script for remote server

echo "=== Setting up Phishing Detector ==="

# Install dependencies
apt update
apt install -y python3-pip python3-venv mysql-server

# Create application directory
mkdir -p /opt/phishing-detector
cd /opt/phishing-detector

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install flask flask-cors pyyaml requests beautifulsoup4

# Create simple application
mkdir -p app/api
cat > app/api/routes.py << 'APP_EOF'
from flask import Flask, request, jsonify
from flask_cors import CORS
import yaml
import re
import urllib.parse

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Phishing Detector</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .input-group { margin: 20px 0; }
            input[type="text"] { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
            button { background-color: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background-color: #0056b3; }
            .result { margin-top: 20px; padding: 15px; border-radius: 5px; }
            .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ Phishing Website Detector</h1>
            <div class="input-group">
                <input type="text" id="urlInput" placeholder="Enter URL to check (e.g., https://example.com)">
            </div>
            <button onclick="detectPhishing()">Detect Phishing</button>
            <div id="result"></div>
        </div>

        <script>
            async function detectPhishing() {
                const url = document.getElementById('urlInput').value;
                const resultDiv = document.getElementById('result');

                if (!url) {
                    resultDiv.innerHTML = '<div class="result info">Please enter a URL</div>';
                    return;
                }

                resultDiv.innerHTML = '<div class="result info">Analyzing...</div>';

                try {
                    const response = await fetch('/api/detect', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ url: url })
                    });

                    const result = await response.json();

                    if (result.is_phishing) {
                        resultDiv.innerHTML = `<div class="result danger">
                            <h3>⚠️ Phishing Website Detected!</h3>
                            <p><strong>URL:</strong> ${url}</p>
                            <p><strong>Confidence:</strong> ${(result.confidence_score * 100).toFixed(2)}%</p>
                            <p><strong>Risk Level:</strong> ${result.risk_level}</p>
                        </div>`;
                    } else {
                        resultDiv.innerHTML = `<div class="result success">
                            <h3>✅ Safe Website</h3>
                            <p><strong>URL:</strong> ${url}</p>
                            <p><strong>Confidence:</strong> ${(result.confidence_score * 100).toFixed(2)}%</p>
                            <p><strong>Risk Level:</strong> ${result.risk_level}</p>
                        </div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="result info">Error: ${error.message}</div>`;
                }
            }
        </script>
    </body>
    </html>
    """

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Phishing Detector API is running',
        'version': '1.0.0'
    })

@app.route('/api/detect', methods=['POST'])
def detect_phishing():
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Simple heuristic-based detection
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc

        risk_score = 0
        reasons = []

        # Check for IP address in URL
        if re.match(r'^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$', domain):
            risk_score += 0.3
            reasons.append("IP address in URL")

        # Check for suspicious TLDs
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.xyz', '.top', '.click', '.download']
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            risk_score += 0.2
            reasons.append("Suspicious TLD")

        # Check URL length
        if len(url) > 100:
            risk_score += 0.1
            reasons.append("Very long URL")

        # Check for special characters
        if re.search(r'[@%_\\-+=]', domain):
            risk_score += 0.2
            reasons.append("Special characters in domain")

        # Determine result
        is_phishing = risk_score > 0.5
        confidence_score = min(risk_score, 1.0)

        if is_phishing:
            risk_level = "High" if confidence_score > 0.8 else "Medium"
        else:
            risk_level = "Low"

        return jsonify({
            'url': url,
            'is_phishing': is_phishing,
            'confidence_score': confidence_score,
            'risk_level': risk_level,
            'reasons': reasons,
            'detection_method': 'heuristic_analysis'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
APP_EOF

# Create systemd service
cat > /etc/systemd/system/phishing-detector.service << 'EOF'
[Unit]
Description=Phishing Detector API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phishing-detector
Environment=PATH=/opt/phishing-detector/venv/bin
ExecStart=/opt/phishing-detector/venv/bin/python app/api/routes.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start services
systemctl daemon-reload
systemctl enable phishing-detector
systemctl start phishing-detector

echo "=== Setup Complete ==="
echo "Application is running at: http://$(hostname -I | awk '{print $1}'):5000"
''')

    # Upload and execute the script
    print("Uploading and executing setup script...")
    result = run_command(f'sshpass -p "{password}" scp -o StrictHostKeyChecking=no /tmp/setup_remote.sh {user}@{server}:/tmp/')

    result = run_command(f'sshpass -p "{password}" ssh -o StrictHostKeyChecking=no {user}@{server} "bash /tmp/setup_remote.sh"')

    print("=== Deployment Complete ===")
    print(f"Application should be accessible at: http://{server}:5000")
    print("API endpoints:")
    print(f"  - Health check: http://{server}:5000/api/health")
    print(f"  - Detection: http://{server}:5000/api/detect")

if __name__ == "__main__":
    main()