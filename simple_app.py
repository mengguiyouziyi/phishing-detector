#!/usr/bin/env python3
"""
简化的钓鱼网站检测器
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import urllib.parse

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>钓鱼网站检测器</title>
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
            <h1>🛡️ 钓鱼网站检测器</h1>
            <div class="input-group">
                <input type="text" id="urlInput" placeholder="输入要检测的URL (例如: https://example.com)">
            </div>
            <button onclick="detectPhishing()">开始检测</button>
            <div id="result"></div>
        </div>

        <script>
            async function detectPhishing() {
                const url = document.getElementById('urlInput').value;
                const resultDiv = document.getElementById('result');

                if (!url) {
                    resultDiv.innerHTML = '<div class="result info">请输入URL</div>';
                    return;
                }

                resultDiv.innerHTML = '<div class="result info">正在分析...</div>';

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
                            <h3>⚠️ 检测到钓鱼网站!</h3>
                            <p><strong>URL:</strong> ${url}</p>
                            <p><strong>置信度:</strong> ${(result.confidence_score * 100).toFixed(2)}%</p>
                            <p><strong>风险等级:</strong> ${result.risk_level}</p>
                        </div>`;
                    } else {
                        resultDiv.innerHTML = `<div class="result success">
                            <h3>✅ 安全网站</h3>
                            <p><strong>URL:</strong> ${url}</p>
                            <p><strong>置信度:</strong> ${(result.confidence_score * 100).toFixed(2)}%</p>
                            <p><strong>风险等级:</strong> ${result.risk_level}</p>
                        </div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="result info">错误: ${error.message}</div>`;
                }
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': '钓鱼网站检测器API正在运行',
        'version': '1.0.0'
    })

@app.route('/api/detect', methods=['POST'])
def detect_phishing():
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'error': 'URL是必需的'}), 400

        # 简单的启发式检测
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc

        risk_score = 0
        reasons = []

        # 检查IP地址
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain):
            risk_score += 0.3
            reasons.append("URL中包含IP地址")

        # 检查可疑TLD
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.xyz', '.top', '.click', '.download']
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            risk_score += 0.2
            reasons.append("可疑的顶级域名")

        # 检查URL长度
        if len(url) > 100:
            risk_score += 0.1
            reasons.append("URL过长")

        # 检查特殊字符
        if re.search(r'[@%_\-+=]', domain):
            risk_score += 0.2
            reasons.append("域名中包含特殊字符")

        # 确定结果
        is_phishing = risk_score > 0.5
        confidence_score = min(risk_score, 1.0)

        if is_phishing:
            risk_level = "高" if confidence_score > 0.8 else "中"
        else:
            risk_level = "低"

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