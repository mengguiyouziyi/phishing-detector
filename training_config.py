#!/usr/bin/env python3
"""
钓鱼网站检测器训练配置
针对4090显卡优化
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import transformers
from transformers import AutoModel, AutoTokenizer
import numpy as np
from typing import Dict, List, Any
import yaml

# 4090显卡配置
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
GPU_MEMORY = 24  # 4090显存24GB
BATCH_SIZE = 64  # 根据显存调整
NUM_WORKERS = 8  # 多进程数据加载

class PhishingDataset(Dataset):
    """钓鱼网站数据集"""
    def __init__(self, features: List[Dict[str, Any]], labels: List[int]):
        self.features = features
        self.labels = labels

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return {
            'url_features': torch.tensor(self.features[idx]['url_features'], dtype=torch.float),
            'html_features': torch.tensor(self.features[idx]['html_features'], dtype=torch.float),
            'ssl_features': torch.tensor(self.features[idx]['ssl_features'], dtype=torch.float),
            'label': torch.tensor(self.labels[idx], dtype=torch.long)
        }

class AdvancedPhishingDetector(nn.Module):
    """高级钓鱼网站检测器 - 针对4090优化"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__()

        # URL处理分支
        self.url_embedding = nn.Sequential(
            nn.Linear(50, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Dropout(0.3)
        )

        # HTML特征处理分支
        self.html_processor = nn.Sequential(
            nn.Linear(100, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Dropout(0.3)
        )

        # SSL特征处理分支
        self.ssl_processor = nn.Sequential(
            nn.Linear(20, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Dropout(0.2)
        )

        # 融合层
        self.fusion_layer = nn.Sequential(
            nn.Linear(512 + 512 + 256, 1024),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 2)  # 二分类
        )

        # 注意力机制
        self.attention = nn.MultiheadAttention(embed_dim=512, num_heads=8)

    def forward(self, url_features, html_features, ssl_features):
        # 处理各分支特征
        url_out = self.url_embedding(url_features)
        html_out = self.html_processor(html_features)
        ssl_out = self.ssl_processor(ssl_features)

        # 特征融合
        combined = torch.cat([url_out, html_out, ssl_out], dim=1)

        # 注意力机制
        attn_out, _ = self.attention(combined.unsqueeze(0), combined.unsqueeze(0), combined.unsqueeze(0))
        attn_out = attn_out.squeeze(0)

        # 最终分类
        output = self.fusion_layer(attn_out)

        return output

class TrainingConfig:
    """训练配置"""

    def __init__(self):
        self.model_config = {
            'url_feature_dim': 50,
            'html_feature_dim': 100,
            'ssl_feature_dim': 20,
            'hidden_dim': 512,
            'num_classes': 2
        }

        self.training_config = {
            'batch_size': BATCH_SIZE,
            'learning_rate': 0.001,
            'num_epochs': 100,
            'early_stopping_patience': 10,
            'weight_decay': 0.0001,
            'gradient_clip_norm': 1.0,
            'warmup_epochs': 5,
            'mixup_alpha': 0.2,
            'label_smoothing': 0.1
        }

        self.optimizer_config = {
            'type': 'AdamW',
            'lr': 0.001,
            'weight_decay': 0.0001,
            'betas': (0.9, 0.999),
            'eps': 1e-8
        }

        self.scheduler_config = {
            'type': 'CosineAnnealingWarmRestarts',
            'T_0': 10,
            'T_mult': 2,
            'eta_min': 1e-6
        }

        self.augmentation_config = {
            'url_augmentation': True,
            'html_augmentation': True,
            'noise_level': 0.1,
            'dropout_rate': 0.3
        }

        self.multi_gpu_config = {
            'use_data_parallel': torch.cuda.device_count() > 1,
            'num_gpus': torch.cuda.device_count(),
            'sync_batchnorm': True
        }

class Trainer:
    """训练器 - 针对4090优化"""

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.device = DEVICE
        self.model = AdvancedPhishingDetector(config.model_config).to(self.device)

        # 多GPU支持
        if config.multi_gpu_config['use_data_parallel']:
            self.model = nn.DataParallel(self.model)

        # 优化器
        if config.optimizer_config['type'] == 'AdamW':
            self.optimizer = optim.AdamW(
                self.model.parameters(),
                lr=config.optimizer_config['lr'],
                weight_decay=config.optimizer_config['weight_decay'],
                betas=config.optimizer_config['betas'],
                eps=config.optimizer_config['eps']
            )

        # 学习率调度器
        if config.scheduler_config['type'] == 'CosineAnnealingWarmRestarts':
            self.scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
                self.optimizer,
                T_0=config.scheduler_config['T_0'],
                T_mult=config.scheduler_config['T_mult'],
                eta_min=config.scheduler_config['eta_min']
            )

        # 损失函数
        self.criterion = nn.CrossEntropyLoss(
            label_smoothing=config.training_config['label_smoothing']
        )

        # 混合精度训练
        self.scaler = torch.cuda.amp.GradScaler()

    def train_epoch(self, train_loader: DataLoader) -> float:
        """训练一个epoch"""
        self.model.train()
        total_loss = 0.0

        for batch_idx, batch in enumerate(train_loader):
            # 数据移动到GPU
            url_features = batch['url_features'].to(self.device)
            html_features = batch['html_features'].to(self.device)
            ssl_features = batch['ssl_features'].to(self.device)
            labels = batch['label'].to(self.device)

            # 梯度清零
            self.optimizer.zero_grad()

            # 混合精度训练
            with torch.cuda.amp.autocast():
                outputs = self.model(url_features, html_features, ssl_features)
                loss = self.criterion(outputs, labels)

            # 反向传播
            self.scaler.scale(loss).backward()

            # 梯度裁剪
            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(),
                self.config.training_config['gradient_clip_norm']
            )

            # 优化器步骤
            self.scaler.step(self.optimizer)
            self.scaler.update()

            total_loss += loss.item()

        return total_loss / len(train_loader)

    def validate(self, val_loader: DataLoader) -> Dict[str, float]:
        """验证模型"""
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for batch in val_loader:
                url_features = batch['url_features'].to(self.device)
                html_features = batch['html_features'].to(self.device)
                ssl_features = batch['ssl_features'].to(self.device)
                labels = batch['label'].to(self.device)

                outputs = self.model(url_features, html_features, ssl_features)
                loss = self.criterion(outputs, labels)

                total_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()

        accuracy = 100. * correct / total
        avg_loss = total_loss / len(val_loader)

        return {
            'val_loss': avg_loss,
            'val_accuracy': accuracy
        }

    def train(self, train_loader: DataLoader, val_loader: DataLoader):
        """完整训练流程"""
        best_val_accuracy = 0.0
        patience_counter = 0

        for epoch in range(self.config.training_config['num_epochs']):
            # 训练
            train_loss = self.train_epoch(train_loader)

            # 验证
            val_metrics = self.validate(val_loader)

            # 学习率调整
            self.scheduler.step()

            # 打印进度
            print(f'Epoch [{epoch+1}/{self.config.training_config["num_epochs"]}]')
            print(f'Train Loss: {train_loss:.4f}')
            print(f'Val Loss: {val_metrics["val_loss"]:.4f}')
            print(f'Val Accuracy: {val_metrics["val_accuracy"]:.2f}%')
            print(f'LR: {self.scheduler.get_last_lr()[0]:.6f}')
            print('-' * 50)

            # 早停
            if val_metrics['val_accuracy'] > best_val_accuracy:
                best_val_accuracy = val_metrics['val_accuracy']
                patience_counter = 0
                # 保存最佳模型
                torch.save(self.model.state_dict(), 'best_model.pth')
            else:
                patience_counter += 1
                if patience_counter >= self.config.training_config['early_stopping_patience']:
                    print(f'Early stopping at epoch {epoch+1}')
                    break

        print(f'Best validation accuracy: {best_val_accuracy:.2f}%')

def create_training_pipeline():
    """创建训练流水线"""

    # 加载配置
    config = TrainingConfig()

    # 打印GPU信息
    if torch.cuda.is_available():
        print(f"使用GPU: {torch.cuda.get_device_name()}")
        print(f"GPU数量: {torch.cuda.device_count()}")
        print(f"GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    # 创建训练器
    trainer = Trainer(config)

    return trainer

if __name__ == "__main__":
    # 创建训练流水线
    trainer = create_training_pipeline()

    print("🚀 钓鱼网站检测器训练器已准备就绪")
    print("📊 针对RTX 4090优化")
    print("🎯 支持混合精度训练和多GPU训练")
    print("📈 集成先进的训练策略和正则化技术")