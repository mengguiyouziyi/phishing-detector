#!/usr/bin/env python3
"""
创建246服务器部署包
"""

import os
import tarfile
import subprocess
import shutil
import sys

def create_deploy_package():
    """创建部署包"""
    print("📦 创建246服务器部署包...")

    # 创建临时目录
    os.makedirs('/tmp/phishing_deploy_246', exist_ok=True)

    # 复制核心文件
    core_files = [
        'simple_app.py',
        'requirements.txt',
        'data_collection.py',
        'training_config.py',
        'train_model.py',
        'start_training.py',
        'MANUAL_DEPLOY_246.md'
    ]

    for file_path in core_files:
        if os.path.exists(file_path):
            print(f"复制文件: {file_path}")
            if os.path.isdir(file_path):
                shutil.copytree(file_path, f'/tmp/phishing_deploy_246/{file_path}', dirs_exist_ok=True)
            else:
                # 确保目标目录存在
                target_dir = os.path.dirname(f'/tmp/phishing_deploy_246/{file_path}')
                os.makedirs(target_dir, exist_ok=True)
                shutil.copy2(file_path, f'/tmp/phishing_deploy_246/{file_path}')

    # 复制config目录
    if os.path.exists('config'):
        shutil.copytree('config', '/tmp/phishing_deploy_246/config', dirs_exist_ok=True)
        print("复制目录: config")

    # 创建应用目录结构
    os.makedirs('/tmp/phishing_deploy_246/app', exist_ok=True)

    # 创建启动脚本
    startup_script = '''#!/bin/bash
echo "=== 钓鱼网站检测器 - 246服务器部署 ==="

# 检查Python
python3 --version
pip3 --version

# 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装PyTorch（支持4090）
echo "安装PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 检查GPU
echo "检查GPU..."
python3 -c "import torch; print(f'GPU数量: {torch.cuda.device_count()}'); [print(f'GPU {i}: {torch.cuda.get_device_name(i)}') for i in range(torch.cuda.device_count())]"

# 启动Web应用
echo "启动Web应用..."
nohup python3 simple_app.py > web_app.log 2>&1 &
echo $! > web_app.pid

echo "✅ 部署完成！"
echo "🌐 访问地址: http://$(hostname -I | awk '{print $1}'):5000"
echo "📊 日志文件: tail -f web_app.log"
echo "🎯 训练命令: source venv/bin/activate && python3 start_training.py"
'''

    with open('/tmp/phishing_deploy_246/start.sh', 'w') as f:
        f.write(startup_script)

    # 创建训练脚本
    train_script = '''#!/bin/bash
echo "=== 开始训练钓鱼网站检测模型 ==="

# 激活虚拟环境
source venv/bin/activate

# 检查GPU
echo "GPU状态:"
nvidia-smi

# 收集数据
echo "收集训练数据..."
python3 data_collection.py

# 开始训练
echo "开始训练..."
python3 train_model.py --data phishing_dataset.csv --batch_size 128 --epochs 100 --lr 0.001

echo "✅ 训练完成！"
echo "📊 结果文件:"
echo "   - best_model.pth"
echo "   - training_results.json"
echo "   - confusion_matrix.png"
echo "   - roc_curve.png"
'''

    with open('/tmp/phishing_deploy_246/train.sh', 'w') as f:
        f.write(train_script)

    # 设置执行权限
    os.chmod('/tmp/phishing_deploy_246/start.sh', 0o755)
    os.chmod('/tmp/phishing_deploy_246/train.sh', 0o755)

    # 创建README
    readme_content = '''# 钓鱼网站检测器 - 246服务器部署

## 🚀 快速启动

```bash
# 1. 解压部署包
tar -xzf phishing_detector_246.tar.gz
cd phishing_detector_246

# 2. 运行启动脚本
./start.sh

# 3. 访问Web应用
# http://192.168.1.246:5000
```

## 🎯 训练模型

```bash
# 运行训练脚本
./train.sh

# 或手动训练
source venv/bin/activate
python3 start_training.py
```

## 📊 系统要求

- Ubuntu 20.04+
- Python 3.8+
- 2x RTX 4090 (24GB each)
- MySQL 8.0+
- 16GB+ RAM

## 🔧 功能特性

- ✅ Web界面钓鱼检测
- ✅ 4090显卡加速训练
- ✅ 混合精度训练
- ✅ 多GPU支持
- ✅ 实时API检测
- ✅ 自动数据收集
- ✅ 模型评估和可视化

## 📈 性能优化

- 针对RTX 4090优化
- 支持FP16混合精度
- 多GPU并行训练
- 内存高效数据加载
- 自动化特征提取

## 🌐 访问地址

- Web应用: http://192.168.1.246:5000
- API健康检查: http://192.168.1.246:5000/api/health
- 检测API: http://192.168.1.246:5000/api/detect

## 📞 支持

如有问题，请查看日志文件或联系技术支持。
'''

    with open('/tmp/phishing_deploy_246/README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)

    # 创建tar包
    tar_path = '/tmp/phishing_detector_246.tar.gz'
    with tarfile.open(tar_path, 'w:gz') as tar:
        tar.add('/tmp/phishing_deploy_246', arcname='phishing_detector_246')

    print(f"✅ 部署包创建完成: {tar_path}")
    print(f"📦 大小: {os.path.getsize(tar_path) / (1024*1024):.2f} MB")

    return tar_path

if __name__ == "__main__":
    package_path = create_deploy_package()

    print("\n🎯 部署说明:")
    print("1. 将部署包传输到246服务器:")
    print(f"   scp {package_path} root@192.168.1.246:/tmp/")
    print("2. 连接到246服务器:")
    print("   ssh root@192.168.1.246")
    print("3. 解压并运行:")
    print("   cd /opt")
    print("   tar -xzf /tmp/phishing_detector_246.tar.gz")
    print("   cd phishing_detector_246")
    print("   ./start.sh")
    print("4. 访问应用:")
    print("   http://192.168.1.246:5000")

    print(f"\n📦 部署包路径: {package_path}")
    print("🚀 部署包已准备就绪！")