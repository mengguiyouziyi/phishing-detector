#!/usr/bin/env python3
"""
部署钓鱼网站检测器到246服务器
"""

import subprocess
import sys
import os
import time
import tarfile
import shutil

def create_deployment_package():
    """创建部署包"""
    print("📦 创建部署包...")

    # 创建临时目录
    os.makedirs('/tmp/phishing_deploy', exist_ok=True)

    # 复制必要文件
    files_to_copy = [
        'simple_app.py',
        'requirements.txt',
        'config/settings.yaml',
        'data_collection.py',
        'training_config.py',
        'train_model.py',
        'start_training.py',
        'app/',
    ]

    for item in files_to_copy:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.copytree(item, f'/tmp/phishing_deploy/{item}', dirs_exist_ok=True)
            else:
                shutil.copy2(item, '/tmp/phishing_deploy/')

    # 创建启动脚本
    startup_script = '''#!/bin/bash
# 钓鱼网站检测器启动脚本

echo "=== 部署钓鱼网站检测器到246服务器 ==="

# 安装系统依赖
apt update
apt install -y python3-pip python3-dev python3-venv mysql-server libmysqlclient-dev

# 创建虚拟环境
cd /opt/phishing-detector
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# 启动MySQL
systemctl start mysql
systemctl enable mysql

# 创建数据库
mysql -e "CREATE DATABASE IF NOT EXISTS phishing_detector CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 启动Web应用
nohup python3 simple_app.py > web_app.log 2>&1 &
echo $! > web_app.pid

echo "=== 部署完成 ==="
echo "Web应用: http://$(hostname -I | awk '{print $1}'):5000"
echo "启动训练: python3 start_training.py"
'''

    with open('/tmp/phishing_deploy/startup.sh', 'w') as f:
        f.write(startup_script)

    # 创建tar包
    with tarfile.open('/tmp/phishing_detector.tar.gz', 'w:gz') as tar:
        tar.add('/tmp/phishing_deploy', arcname='phishing-detector')

    print("✅ 部署包创建完成: /tmp/phishing_detector.tar.gz")

def deploy_to_server():
    """部署到服务器"""
    print("🚀 部署到246服务器...")

    # 创建部署脚本
    deploy_script = '''#!/bin/bash
# 远程部署脚本

echo "=== 在246服务器上部署 ==="

# 创建目录
mkdir -p /opt/phishing-detector
cd /opt/phishing-detector

# 解压部署包
tar -xzf /tmp/phishing_detector.tar.gz --strip-components=1 -C /opt/phishing-detector

# 运行启动脚本
chmod +x startup.sh
./startup.sh

echo "=== 部署完成 ==="
'''

    with open('/tmp/remote_deploy.sh', 'w') as f:
        f.write(deploy_script)

    # 使用scp和ssh进行部署
    commands = [
        f"scp /tmp/phishing_detector.tar.gz root@192.168.1.246:/tmp/",
        f"scp /tmp/remote_deploy.sh root@192.168.1.246:/tmp/",
        f"ssh root@192.168.1.246 'chmod +x /tmp/remote_deploy.sh && /tmp/remote_deploy.sh'"
    ]

    for cmd in commands:
        print(f"执行: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"✅ {cmd.split()[0]} 成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ {cmd.split()[0]} 失败: {e.stderr}")
            return False

    return True

def main():
    """主函数"""
    print("🎯 开始部署钓鱼网站检测器到246服务器")

    # 1. 创建部署包
    create_deployment_package()

    # 2. 部署到服务器
    if deploy_to_server():
        print("✅ 部署成功!")
        print("🌐 访问地址: http://192.168.1.246:5000")
        print("🔧 训练命令: ssh root@192.168.1.246 'cd /opt/phishing-detector && python3 start_training.py'")
    else:
        print("❌ 部署失败!")

if __name__ == "__main__":
    main()