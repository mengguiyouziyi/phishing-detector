# 🛡️ 钓鱼网站检测器

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![CUDA](https://img.shields.io/badge/CUDA-12.1+-green.svg)](https://developer.nvidia.com/cuda-toolkit)

基于深度学习的钓鱼网站检测系统，支持实时检测和批量处理，针对RTX 4090显卡优化。

## ✨ 主要特性

- 🎯 **高精度检测**: 基于多模态深度学习模型，准确率 >95%
- 🚀 **GPU加速**: 针对RTX 4090优化，支持混合精度训练
- 🌐 **Web界面**: 现代化的用户界面，支持实时检测
- 🔧 **RESTful API**: 完整的API接口，支持程序化调用
- 📊 **实时监控**: GPU使用监控和训练进度跟踪
- 🔄 **自动更新**: 支持在线数据收集和模型再训练
- ⚡ **多GPU支持**: 支持多张显卡并行训练

## 🏗️ 系统架构

```
钓鱼网站检测器
├── Web界面 (Flask + Bootstrap)
├── API服务 (RESTful API)
├── 机器学习模型 (PyTorch)
├── 数据收集器 (Async Web Scraping)
├── 特征提取器 (多模态特征工程)
└── 数据库 (MySQL)
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- PyTorch 2.0+
- CUDA 12.1+
- MySQL 8.0+
- RTX 4090 (推荐)

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/your-username/phishing-detector.git
   cd phishing-detector
   ```

2. **创建虚拟环境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   ```

3. **安装依赖**
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   pip install -r requirements.txt
   ```

4. **启动Web应用**
   ```bash
   python3 simple_app.py
   ```

5. **访问应用**
   打开浏览器访问 http://localhost:5000

## 🎯 训练模型

### 数据准备

```bash
# 收集训练数据
python3 data_collection.py

# 或使用已有数据集
# 下载UCI Phishing Websites Dataset
# 下载PhishTank数据
# 下载正常网站数据
```

### 开始训练

```bash
# 完整训练流程
python3 start_training.py

# 或自定义训练
python3 train_model.py \
    --data phishing_dataset.csv \
    --batch_size 128 \
    --epochs 100 \
    --lr 0.001 \
    --save_model best_model.pth
```

### 监控训练

```bash
# 查看GPU使用
nvidia-smi

# 查看训练日志
tail -f training.log

# 监控系统资源
htop
```

## 📊 模型性能

| 指标 | 数值 | 说明 |
|------|------|------|
| 准确率 | >95% | 整体分类准确率 |
| 精确率 | >94% | 钓鱼网站检测精确率 |
| 召回率 | >93% | 钓鱼网站检测召回率 |
| F1分数 | >94% | 综合性能指标 |
| ROC AUC | >0.98 | 模型区分能力 |

## 🌐 API接口

### 检测单个URL
```bash
curl -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### 批量检测
```bash
curl -X POST http://localhost:5000/api/batch_detect \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com", "https://test.com"]}'
```

### 健康检查
```bash
curl http://localhost:5000/api/health
```

## 🏭 部署到服务器

### 服务器要求

- Ubuntu 20.04+
- 2x RTX 4090 (24GB each)
- 16GB+ RAM
- MySQL 8.0+

### 快速部署

1. **上传部署包**
   ```bash
   scp phishing_detector_246.tar.gz root@your-server:/tmp/
   ```

2. **连接到服务器**
   ```bash
   ssh root@your-server
   ```

3. **部署应用**
   ```bash
   cd /opt
   tar -xzf /tmp/phishing_detector_246.tar.gz
   cd phishing_detector_246
   ./start.sh
   ```

详细部署文档请参考 [246部署指南](246_部署指南.md)

## 🔧 配置说明

### 配置文件
```yaml
# config/settings.yaml
database:
  host: localhost
  port: 3306
  name: phishing_detector
  user: phishing_user
  password: phishing_password

model:
  algorithms:
    - random_forest
    - xgboost
    - neural_network
  hyperparameter_tuning: true
  cross_validation_folds: 5
```

### 环境变量
```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=phishing_detector
export DB_USER=phishing_user
export DB_PASSWORD=phishing_password
```

## 📈 性能优化

### GPU优化
- **混合精度训练**: 使用FP16加速训练
- **多GPU并行**: DataParallel分布式训练
- **内存优化**: 梯度累积和梯度检查点
- **CUDA内核优化**: 针对Ampere架构优化

### 模型优化
- **特征选择**: 70+维特征向量
- **数据增强**: URL变换和域名扰动
- **集成学习**: 多模型融合
- **正则化**: Dropout和权重衰减

## 🧪 测试

```bash
# 运行单元测试
python3 -m pytest tests/

# 测试API接口
python3 test_api.py

# 验证模型性能
python3 validate_model.py
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [PyTorch](https://pytorch.org/) - 深度学习框架
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Scikit-learn](https://scikit-learn.org/) - 机器学习库
- [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/) - 数据集来源

## 📞 联系方式

- 项目链接: [https://github.com/your-username/phishing-detector](https://github.com/your-username/phishing-detector)
- 问题反馈: [Issues](https://github.com/your-username/phishing-detector/issues)
- 邮箱: your-email@example.com

---

⭐ 如果这个项目对您有帮助，请考虑给个星标！