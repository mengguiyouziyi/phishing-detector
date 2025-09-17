#!/usr/bin/env python3
"""
钓鱼网站检测器训练脚本
针对4090显卡优化
"""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns
import json
import time
import logging
from typing import Dict, List, Any, Tuple
import argparse
from training_config import TrainingConfig, Trainer, AdvancedPhishingDetector, PhishingDataset

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataProcessor:
    """数据处理器"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_columns = []

    def load_data(self, filepath: str) -> pd.DataFrame:
        """加载数据"""
        try:
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filepath.endswith('.json'):
                df = pd.read_json(filepath)
            else:
                raise ValueError("不支持的数据格式")

            logger.info(f"数据加载完成，共 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            return pd.DataFrame()

    def preprocess_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """预处理数据"""
        # 选择特征列
        feature_columns = [col for col in df.columns if col not in ['is_phishing', 'source', 'url']]
        self.feature_columns = feature_columns

        # 提取特征和标签
        X = df[feature_columns].values
        y = df['is_phishing'].values

        # 处理缺失值
        X = np.nan_to_num(X)

        # 标准化
        X = self.scaler.fit_transform(X)

        logger.info(f"特征数量: {X.shape[1]}")
        logger.info(f"样本数量: {X.shape[0]}")
        logger.info(f"正样本比例: {y.mean():.3f}")

        return X, y

    def split_data(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2, val_size: float = 0.1) -> Tuple:
        """分割数据"""
        # 先分割出测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        # 再从训练集分割出验证集
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=val_size/(1-test_size), random_state=42, stratify=y_train
        )

        logger.info(f"训练集: {X_train.shape[0]} 样本")
        logger.info(f"验证集: {X_val.shape[0]} 样本")
        logger.info(f"测试集: {X_test.shape[0]} 样本")

        return X_train, X_val, X_test, y_train, y_val, y_test

    def create_features_dict(self, X: np.ndarray) -> List[Dict[str, Any]]:
        """创建特征字典"""
        features = []

        for i in range(X.shape[0]):
            # 将特征分成不同的组
            features.append({
                'url_features': X[i, :50].tolist(),  # URL特征
                'html_features': X[i, 50:150].tolist(),  # HTML特征
                'ssl_features': X[i, 150:170].tolist()  # SSL特征
            })

        return features

class ModelEvaluator:
    """模型评估器"""

    def __init__(self):
        self.metrics = {}

    def evaluate_model(self, model: nn.Module, test_loader: DataLoader, device: torch.device) -> Dict[str, float]:
        """评估模型"""
        model.eval()
        all_predictions = []
        all_labels = []
        all_probabilities = []

        with torch.no_grad():
            for batch in test_loader:
                url_features = batch['url_features'].to(device)
                html_features = batch['html_features'].to(device)
                ssl_features = batch['ssl_features'].to(device)
                labels = batch['label'].to(device)

                outputs = model(url_features, html_features, ssl_features)
                probabilities = torch.softmax(outputs, dim=1)[:, 1]
                _, predicted = torch.max(outputs, 1)

                all_predictions.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
                all_probabilities.extend(probabilities.cpu().numpy())

        # 计算评估指标
        metrics = {
            'accuracy': accuracy_score(all_labels, all_predictions),
            'precision': precision_score(all_labels, all_predictions),
            'recall': recall_score(all_labels, all_predictions),
            'f1_score': f1_score(all_labels, all_predictions),
            'roc_auc': roc_auc_score(all_labels, all_probabilities)
        }

        self.metrics = metrics
        return metrics

    def plot_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray):
        """绘制混淆矩阵"""
        from sklearn.metrics import confusion_matrix
        cm = confusion_matrix(y_true, y_pred)

        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('混淆矩阵')
        plt.xlabel('预测标签')
        plt.ylabel('真实标签')
        plt.savefig('confusion_matrix.png')
        plt.close()

    def plot_roc_curve(self, y_true: np.ndarray, y_prob: np.ndarray):
        """绘制ROC曲线"""
        from sklearn.metrics import roc_curve

        fpr, tpr, _ = roc_curve(y_true, y_prob)
        auc = roc_auc_score(y_true, y_prob)

        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, label=f'ROC曲线 (AUC = {auc:.3f})')
        plt.plot([0, 1], [0, 1], 'k--', label='随机分类器')
        plt.xlabel('假正率')
        plt.ylabel('真正率')
        plt.title('ROC曲线')
        plt.legend()
        plt.grid(True)
        plt.savefig('roc_curve.png')
        plt.close()

def main():
    parser = argparse.ArgumentParser(description='钓鱼网站检测器训练')
    parser.add_argument('--data', type=str, default='phishing_dataset.csv', help='数据文件路径')
    parser.add_argument('--batch_size', type=int, default=64, help='批次大小')
    parser.add_argument('--epochs', type=int, default=100, help='训练轮数')
    parser.add_argument('--lr', type=float, default=0.001, help='学习率')
    parser.add_argument('--save_model', type=str, default='best_model.pth', help='模型保存路径')

    args = parser.parse_args()

    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"使用设备: {device}")

    # 检查GPU
    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name()}")
        logger.info(f"GPU数量: {torch.cuda.device_count()}")
        logger.info(f"GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    # 数据处理
    logger.info("开始数据处理...")
    processor = DataProcessor()
    df = processor.load_data(args.data)

    if df.empty:
        logger.error("数据加载失败")
        return

    X, y = processor.preprocess_data(df)
    X_train, X_val, X_test, y_train, y_val, y_test = processor.split_data(X, y)

    # 创建数据集
    train_features = processor.create_features_dict(X_train)
    val_features = processor.create_features_dict(X_val)
    test_features = processor.create_features_dict(X_test)

    train_dataset = PhishingDataset(train_features, y_train)
    val_dataset = PhishingDataset(val_features, y_val)
    test_dataset = PhishingDataset(test_features, y_test)

    # 创建数据加载器
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)

    # 创建训练器
    logger.info("创建训练器...")
    config = TrainingConfig()
    config.training_config['batch_size'] = args.batch_size
    config.training_config['num_epochs'] = args.epochs
    config.optimizer_config['lr'] = args.lr

    trainer = Trainer(config)

    # 开始训练
    logger.info("开始训练...")
    start_time = time.time()

    trainer.train(train_loader, val_loader)

    training_time = time.time() - start_time
    logger.info(f"训练完成，耗时: {training_time:.2f} 秒")

    # 评估模型
    logger.info("评估模型...")
    evaluator = ModelEvaluator()
    metrics = evaluator.evaluate_model(trainer.model, test_loader, device)

    # 打印评估结果
    logger.info("=== 模型评估结果 ===")
    for metric_name, value in metrics.items():
        logger.info(f"{metric_name}: {value:.4f}")

    # 绘制评估图表
    logger.info("生成评估图表...")
    test_predictions = []
    test_labels = []
    test_probabilities = []

    trainer.model.eval()
    with torch.no_grad():
        for batch in test_loader:
            url_features = batch['url_features'].to(device)
            html_features = batch['html_features'].to(device)
            ssl_features = batch['ssl_features'].to(device)
            labels = batch['label'].to(device)

            outputs = trainer.model(url_features, html_features, ssl_features)
            probabilities = torch.softmax(outputs, dim=1)[:, 1]
            _, predicted = torch.max(outputs, 1)

            test_predictions.extend(predicted.cpu().numpy())
            test_labels.extend(labels.cpu().numpy())
            test_probabilities.extend(probabilities.cpu().numpy())

    evaluator.plot_confusion_matrix(np.array(test_labels), np.array(test_predictions))
    evaluator.plot_roc_curve(np.array(test_labels), np.array(test_probabilities))

    # 保存结果
    results = {
        'metrics': metrics,
        'training_time': training_time,
        'model_config': config.model_config,
        'training_config': config.training_config,
        'device': str(device),
        'gpu_info': {
            'name': torch.cuda.get_device_name() if torch.cuda.is_available() else 'CPU',
            'memory': torch.cuda.get_device_properties(0).total_memory / 1e9 if torch.cuda.is_available() else 0
        }
    }

    with open('training_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info("✅ 训练完成!")
    logger.info(f"📊 评估指标: {json.dumps(metrics, indent=2, ensure_ascii=False)}")
    logger.info(f"💾 模型保存至: {args.save_model}")
    logger.info(f"📈 混淆矩阵: confusion_matrix.png")
    logger.info(f"📈 ROC曲线: roc_curve.png")
    logger.info(f"📋 训练结果: training_results.json")

if __name__ == "__main__":
    main()