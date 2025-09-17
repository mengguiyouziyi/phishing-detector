#!/bin/bash

# Setup script for remote server
# This script should be run on the remote server (192.168.1.246)

echo "=== Setting up Phishing Detector ==="

# Create application directory
mkdir -p /opt/phishing-detector
cd /opt/phishing-detector

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install flask flask-cors sqlalchemy pymysql aiohttp beautifulsoup4 requests
pip install scikit-learn pandas numpy joblib xgboost
pip install pyyaml python-dotenv

# Create config directory
mkdir -p config

# Create config file
cat > config/settings.yaml << 'EOF'
database:
  host: localhost
  port: 3306
  name: phishing_detector
  user: phishing_user
  password: phishing_password

  # Connection pooling
  pool_size: 20
  max_overflow: 30
  pool_recycle: 3600

redis:
  host: localhost
  port: 6379
  db: 0
  password: ""

data_collection:
  timeout: 30
  max_redirects: 5
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  follow_redirects: true
  verify_ssl: true

  # Rate limiting
  requests_per_second: 10
  concurrent_requests: 5

model:
  algorithms:
    - random_forest
    - xgboost
    - gradient_boosting
    - neural_network
    - svm
    - logistic_regression

  hyperparameter_tuning: true
  cross_validation_folds: 5
  test_size: 0.2
  random_state: 42

security:
  max_url_length: 2048
  allowed_schemes:
    - http
    - https
  rate_limit:
    enabled: true
    requests_per_minute: 100
    burst_size: 50

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/phishing_detector.log"
  max_size: 10485760  # 10MB
  backup_count: 5

development:
  debug: true
  testing: false
  profiling: false

production:
  debug: false
  testing: false
  profiling: false
EOF

# Create application structure
mkdir -p app/{collectors,database,features,models,api,web/{templates,static}}

# Create __init__.py files
touch app/__init__.py
touch app/collectors/__init__.py
touch app/database/__init__.py
touch app/features/__init__.py
touch app/models/__init__.py
touch app/api/__init__.py
touch app/web/__init__.py

# Create a simple main application file
cat > app/main.py << 'EOF'
#!/usr/bin/env python3
"""
Main application entry point
"""

import logging
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.routes import create_app

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run the application
    app = create_app()

    if __name__ == '__main__':
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )

if __name__ == '__main__':
    main()
EOF

# Create a simplified route file
cat > app/api/routes.py << 'EOF'
"""
API Routes - Simplified version for deployment
"""

import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import yaml
import os

logger = logging.getLogger(__name__)

def create_app(config_path: str = "config/settings.yaml") -> Flask:
    """Create Flask application"""
    app = Flask(__name__)
    CORS(app)

    # Load configuration
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        app.config.update(config)
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found, using defaults")
        config = {}

    @app.route('/')
    def index():
        """Main page"""
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
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'message': 'Phishing Detector API is running',
            'version': '1.0.0'
        })

    @app.route('/api/detect', methods=['POST'])
    def detect_phishing():
        """Simple phishing detection - placeholder for now"""
        try:
            data = request.get_json()
            url = data.get('url')

            if not url:
                return jsonify({'error': 'URL is required'}), 400

            # Simple heuristic-based detection (placeholder)
            import re
            import urllib.parse

            # Parse URL
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc

            # Basic heuristics
            risk_score = 0
            reasons = []

            # Check for IP address in URL
            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain):
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
            if re.search(r'[@%_\-+=]', domain):
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
            logger.error(f"Detection failed: {e}")
            return jsonify({'error': str(e)}), 500

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF

# Create systemd service file
cat > /etc/systemd/system/phishing-detector.service << 'EOF'
[Unit]
Description=Phishing Detector API
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phishing-detector
Environment=PATH=/opt/phishing-detector/venv/bin
ExecStart=/opt/phishing-detector/venv/bin/python app/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start services
systemctl daemon-reload
systemctl enable phishing-detector
systemctl start phishing-detector

# Show status
echo "=== Service Status ==="
systemctl status phishing-detector --no-pager

echo "=== Setup Complete ==="
echo "Application is running at: http://$(hostname -I | awk '{print $1}'):5000"
echo "API endpoints:"
echo "  - Health check: http://$(hostname -I | awk '{print $1}'):5000/api/health"
echo "  - Detection: http://$(hostname -I | awk '{print $1}'):5000/api/detect"