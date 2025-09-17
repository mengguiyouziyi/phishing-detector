#!/usr/bin/env python3
"""
启动钓鱼网站检测器训练
"""

import subprocess
import sys
import os
import time
import json
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """检查依赖项"""
    logger.info("检查依赖项...")

    required_packages = [
        'torch', 'torchvision', 'pandas', 'numpy', 'scikit-learn',
        'matplotlib', 'seaborn', 'requests', 'tqdm', 'transformers'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package}")
        except ImportError:
            logger.error(f"❌ {package} 未安装")
            missing_packages.append(package)

    if missing_packages:
        logger.info("安装缺失的依赖项...")
        for package in missing_packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

    logger.info("✅ 依赖项检查完成")

def check_gpu():
    """检查GPU"""
    logger.info("检查GPU...")

    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            logger.info(f"✅ 找到 {device_count} 个GPU")
            for i in range(device_count):
                device_name = torch.cuda.get_device_name(i)
                device_memory = torch.cuda.get_device_properties(i).total_memory / 1e9
                logger.info(f"   GPU {i}: {device_name} ({device_memory:.1f} GB)")
        else:
            logger.warning("⚠️ 未找到GPU，将使用CPU训练")
    except Exception as e:
        logger.error(f"GPU检查失败: {e}")

def collect_data():
    """收集训练数据"""
    logger.info("开始收集训练数据...")

    if os.path.exists('phishing_dataset.csv'):
        logger.info("✅ 数据集已存在，跳过收集")
        return True

    try:
        # 运行数据收集脚本
        result = subprocess.run([sys.executable, 'data_collection.py'], capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("✅ 数据收集完成")
            return True
        else:
            logger.error(f"❌ 数据收集失败: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"❌ 数据收集异常: {e}")
        return False

def train_model():
    """训练模型"""
    logger.info("开始训练模型...")

    try:
        # 检查是否存在数据集
        if not os.path.exists('phishing_dataset.csv'):
            logger.error("❌ 找不到训练数据集，请先运行数据收集")
            return False

        # 训练参数
        train_args = [
            sys.executable, 'train_model.py',
            '--data', 'phishing_dataset.csv',
            '--batch_size', '64',
            '--epochs', '100',
            '--lr', '0.001',
            '--save_model', 'best_model.pth'
        ]

        logger.info(f"训练命令: {' '.join(train_args)}")

        # 运行训练
        result = subprocess.run(train_args, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("✅ 模型训练完成")
            logger.info(f"训练输出: {result.stdout}")
            return True
        else:
            logger.error(f"❌ 模型训练失败: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"❌ 模型训练异常: {e}")
        return False

def validate_training():
    """验证训练结果"""
    logger.info("验证训练结果...")

    required_files = [
        'best_model.pth',
        'training_results.json',
        'confusion_matrix.png',
        'roc_curve.png'
    ]

    missing_files = []

    for file_path in required_files:
        if os.path.exists(file_path):
            logger.info(f"✅ {file_path}")
        else:
            logger.error(f"❌ {file_path} 不存在")
            missing_files.append(file_path)

    if missing_files:
        logger.error("训练验证失败")
        return False

    # 读取训练结果
    try:
        with open('training_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)

        logger.info("=== 训练结果摘要 ===")
        logger.info(f"准确率: {results['metrics']['accuracy']:.4f}")
        logger.info(f"精确率: {results['metrics']['precision']:.4f}")
        logger.info(f"召回率: {results['metrics']['recall']:.4f}")
        logger.info(f"F1分数: {results['metrics']['f1_score']:.4f}")
        logger.info(f"ROC AUC: {results['metrics']['roc_auc']:.4f}")
        logger.info(f"训练时间: {results['training_time']:.2f} 秒")

        logger.info("✅ 训练验证完成")
        return True

    except Exception as e:
        logger.error(f"❌ 训练结果读取失败: {e}")
        return False

def deploy_model():
    """部署模型"""
    logger.info("部署模型...")

    try:
        # 创建部署配置
        deploy_config = {
            'model_path': 'best_model.pth',
            'api_endpoint': 'http://localhost:5000/api/detect',
            'health_endpoint': 'http://localhost:5000/api/health',
            'features_file': 'phishing_dataset.csv',
            'training_results': 'training_results.json'
        }

        with open('deployment_config.json', 'w', encoding='utf-8') as f:
            json.dump(deploy_config, f, indent=2, ensure_ascii=False)

        logger.info("✅ 模型部署完成")
        return True

    except Exception as e:
        logger.error(f"❌ 模型部署失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动钓鱼网站检测器训练流程")

    # 检查依赖项
    check_dependencies()

    # 检查GPU
    check_gpu()

    # 收集数据
    if not collect_data():
        logger.error("❌ 数据收集失败，训练终止")
        return

    # 训练模型
    if not train_model():
        logger.error("❌ 模型训练失败")
        return

    # 验证训练结果
    if not validate_training():
        logger.error("❌ 训练验证失败")
        return

    # 部署模型
    if not deploy_model():
        logger.error("❌ 模型部署失败")
        return

    logger.info("🎉 钓鱼网站检测器训练流程完成!")
    logger.info("📊 训练结果:")
    logger.info("   - 模型文件: best_model.pth")
    logger.info("   - 评估报告: training_results.json")
    logger.info("   - 混淆矩阵: confusion_matrix.png")
    logger.info("   - ROC曲线: roc_curve.png")
    logger.info("   - 部署配置: deployment_config.json")

if __name__ == "__main__":
    main()