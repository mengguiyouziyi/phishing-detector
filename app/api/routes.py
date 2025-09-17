"""
API路由
提供钓鱼网站检测的RESTful API
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import asyncio
import yaml
import os

from ..database.connection import db_manager
from ..models.phishing_detector import PhishingDetector
from ..collectors.web_collector import WebDataCollector, BatchDataCollector

logger = logging.getLogger(__name__)

def create_app(config_path: str = "config/settings.yaml") -> Flask:
    """创建Flask应用"""
    app = Flask(__name__)
    CORS(app)

    # 加载配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    app.config.update(config)

    # 初始化数据库
    db_manager.initialize()

    # 初始化检测器
    detector = PhishingDetector(config)

    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        """仪表板"""
        return render_template('dashboard.html')

    @app.route('/api/health')
    def health_check():
        """健康检查"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })

    @app.route('/api/detect', methods=['POST'])
    def detect_phishing():
        """检测单个URL"""
        try:
            data = request.get_json()
            url = data.get('url')

            if not url:
                return jsonify({'error': 'URL is required'}), 400

            # 异步收集网站数据
            async def collect_and_detect():
                async with WebDataCollector(config.get('data_collection', {})) as collector:
                    website_data = await collector.collect_website_data(url)
                    if website_data:
                        return detector.predict(url, website_data)
                    else:
                        return {'error': 'Failed to collect website data'}

            # 运行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(collect_and_detect())
            finally:
                loop.close()

            return jsonify(result)

        except Exception as e:
            logger.error(f"检测失败: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/batch_detect', methods=['POST'])
    def batch_detect():
        """批量检测URL"""
        try:
            data = request.get_json()
            urls = data.get('urls', [])

            if not urls:
                return jsonify({'error': 'URLs are required'}), 400

            if len(urls) > 100:
                return jsonify({'error': 'Maximum 100 URLs per batch'}), 400

            results = []

            # 异步批量收集和检测
            async def batch_collect_and_detect():
                async with BatchDataCollector(config.get('data_collection', {})) as collector:
                    website_data_list = await collector.collect_batch(urls)

                    for website_data in website_data_list:
                        result = detector.predict(website_data.url, website_data)
                        results.append(result)

            # 运行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(batch_collect_and_detect())
            finally:
                loop.close()

            return jsonify({
                'results': results,
                'total': len(results),
                'phishing_count': sum(1 for r in results if r.get('is_phishing', False))
            })

        except Exception as e:
            logger.error(f"批量检测失败: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/collect', methods=['POST'])
    def collect_website():
        """收集网站数据"""
        try:
            data = request.get_json()
            url = data.get('url')

            if not url:
                return jsonify({'error': 'URL is required'}), 400

            # 异步收集数据
            async def collect_data():
                async with WebDataCollector(config.get('data_collection', {})) as collector:
                    return await collector.collect_website_data(url)

            # 运行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                website_data = loop.run_until_complete(collect_data())
            finally:
                loop.close()

            if website_data:
                return jsonify({
                    'success': True,
                    'url': url,
                    'title': website_data.title,
                    'status_code': website_data.status_code,
                    'content_length': website_data.content_length,
                    'num_features': len(website_data.external_scripts) + len(website_data.external_stylesheets)
                })
            else:
                return jsonify({'error': 'Failed to collect website data'}), 500

        except Exception as e:
            logger.error(f"数据收集失败: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/train', methods=['POST'])
    def train_model():
        """训练模型"""
        try:
            data = request.get_json()
            hyperparameter_tuning = data.get('hyperparameter_tuning', True)

            # 训练模型
            results = detector.train(hyperparameter_tuning=hyperparameter_tuning)

            return jsonify({
                'success': True,
                'message': 'Model training completed',
                'results': results
            })

        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/predict', methods=['POST'])
    def predict():
        """预测（使用已收集的数据）"""
        try:
            data = request.get_json()
            url = data.get('url')
            features = data.get('features')

            if not url:
                return jsonify({'error': 'URL is required'}), 400

            result = detector.predict(url, features)
            return jsonify(result)

        except Exception as e:
            logger.error(f"预测失败: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/feature_importance')
    def get_feature_importance():
        """获取特征重要性"""
        try:
            if not detector.is_trained:
                return jsonify({'error': 'Model not trained'}), 400

            importance = detector.get_feature_importance()
            return jsonify({
                'feature_importance': importance,
                'total_features': len(importance)
            })

        except Exception as e:
            logger.error(f"获取特征重要性失败: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/model_status')
    def model_status():
        """获取模型状态"""
        try:
            with db_manager.get_session() as session:
                from ..database.models import Model

                # 获取最新模型
                latest_model = session.query(Model).order_by(Model.created_at.desc()).first()

                if latest_model:
                    return jsonify({
                        'is_trained': detector.is_trained,
                        'model_info': {
                            'name': latest_model.name,
                            'version': latest_model.version,
                            'algorithm': latest_model.algorithm,
                            'accuracy': latest_model.accuracy,
                            'precision': latest_model.precision,
                            'recall': latest_model.recall,
                            'f1_score': latest_model.f1_score,
                            'auc_score': latest_model.auc_score,
                            'created_at': latest_model.created_at.isoformat(),
                            'deployment_status': latest_model.deployment_status
                        }
                    })
                else:
                    return jsonify({
                        'is_trained': False,
                        'model_info': None
                    })

        except Exception as e:
            logger.error(f"获取模型状态失败: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/statistics')
    def get_statistics():
        """获取系统统计信息"""
        try:
            with db_manager.get_session() as session:
                from ..database.models import Website, Prediction

                # 网站统计
                total_websites = session.query(Website).count()
                phishing_websites = session.query(Website).filter_by(is_phishing=True).count()
                legitimate_websites = session.query(Website).filter_by(is_phishing=False).count()

                # 预测统计
                total_predictions = session.query(Prediction).count()
                recent_predictions = session.query(Prediction).filter(
                    Prediction.prediction_time >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                ).count()

                # 数据库统计
                db_stats = db_manager.get_table_stats()

                return jsonify({
                    'websites': {
                        'total': total_websites,
                        'phishing': phishing_websites,
                        'legitimate': legitimate_websites,
                        'unlabeled': total_websites - phishing_websites - legitimate_websites
                    },
                    'predictions': {
                        'total': total_predictions,
                        'today': recent_predictions
                    },
                    'database': db_stats
                })

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/recent_predictions')
    def get_recent_predictions():
        """获取最近的预测记录"""
        try:
            limit = request.args.get('limit', 10, type=int)
            offset = request.args.get('offset', 0, type=int)

            with db_manager.get_session() as session:
                from ..database.models import Prediction, Website

                predictions = session.query(
                    Prediction, Website
                ).join(
                    Website, Prediction.website_id == Website.id
                ).order_by(
                    Prediction.prediction_time.desc()
                ).offset(offset).limit(limit).all()

                results = []
                for prediction, website in predictions:
                    results.append({
                        'id': prediction.id,
                        'url': website.url,
                        'predicted_label': prediction.predicted_label,
                        'confidence_score': prediction.confidence_score,
                        'prediction_time': prediction.prediction_time.isoformat()
                    })

                return jsonify({
                    'predictions': results,
                    'total': len(results)
                })

        except Exception as e:
            logger.error(f"获取最近预测失败: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/label', methods=['POST'])
    def label_website():
        """标记网站"""
        try:
            data = request.get_json()
            url = data.get('url')
            is_phishing = data.get('is_phishing')

            if not url or is_phishing is None:
                return jsonify({'error': 'URL and is_phishing are required'}), 400

            with db_manager.get_session() as session:
                from ..database.models import Website

                website = session.query(Website).filter_by(url=url).first()
                if not website:
                    return jsonify({'error': 'Website not found'}), 404

                website.is_phishing = is_phishing
                website.last_updated = datetime.now()
                session.commit()

                return jsonify({
                    'success': True,
                    'message': f'Website labeled as {"phishing" if is_phishing else "legitimate"}'
                })

        except Exception as e:
            logger.error(f"标记网站失败: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/export_data')
    def export_data():
        """导出数据"""
        try:
            format_type = request.args.get('format', 'json')
            limit = request.args.get('limit', 1000, type=int)

            with db_manager.get_session() as session:
                from ..database.models import Website, WebsiteFeature

                query = session.query(
                    Website, WebsiteFeature
                ).join(
                    WebsiteFeature, Website.id == WebsiteFeature.website_id
                ).filter(
                    Website.is_phishing.isnot(None)
                ).limit(limit)

                data = []
                for website, feature in query:
                    data.append({
                        'url': website.url,
                        'title': website.title,
                        'is_phishing': website.is_phishing,
                        'confidence_score': website.confidence_score,
                        'collection_time': website.collection_time.isoformat(),
                        'features': {
                            'url_length': feature.url_length,
                            'domain_length': len(website.domain),
                            'has_ip_address': feature.has_ip_address,
                            'num_external_scripts': feature.num_external_scripts,
                            'has_password_form': feature.has_password_form,
                            'has_ssl': feature.has_ssl
                        }
                    })

                if format_type == 'json':
                    return jsonify(data)
                else:
                    return jsonify({'error': 'Unsupported format'}), 400

        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return jsonify({'error': str(e)}), 500

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app


if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(level=logging.INFO)

    # 创建应用
    app = create_app()

    # 运行应用
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )