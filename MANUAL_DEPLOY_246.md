# 🚀 246服务器手动部署指南

## 📋 部署步骤

### 1. 连接到246服务器
```bash
ssh root@192.168.1.246
密码: 3646287
```

### 2. 安装系统依赖
```bash
# 更新系统
apt update
apt install -y python3-pip python3-dev python3-venv mysql-server libmysqlclient-dev nginx supervisor git

# 启动MySQL
systemctl start mysql
systemctl enable mysql

# 创建数据库
mysql -e "CREATE DATABASE IF NOT EXISTS phishing_detector CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS 'phishing_user'@'localhost' IDENTIFIED BY 'phishing_password';"
mysql -e "GRANT ALL PRIVILEGES ON phishing_detector.* TO 'phishing_user'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"
```

### 3. 创建项目目录
```bash
mkdir -p /opt/phishing-detector
cd /opt/phishing-detector
```

### 4. 下载项目文件
```bash
# 从GitHub克隆（如果已上传）
git clone <your-repo-url> .

# 或者手动上传文件（推荐）
# 在本地执行：
scp -r /Users/sunyouyou/development/phishing-detector/* root@192.168.1.246:/opt/phishing-detector/
```

### 5. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

### 6. 安装CUDA和PyTorch（针对4090显卡）
```bash
# 安装CUDA工具包
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
dpkg -i cuda-keyring_1.1-1_all.deb
apt-get update
apt-get -y install cuda-toolkit-12-1

# 安装PyTorch（支持CUDA 12.1）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 7. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 8. 启动Web应用
```bash
# 启动Web应用
nohup python3 simple_app.py > web_app.log 2>&1 &
echo $! > web_app.pid

# 检查应用状态
ps aux | grep simple_app
tail -f web_app.log
```

### 9. 创建系统服务
```bash
# 创建systemd服务文件
cat > /etc/systemd/system/phishing-detector.service << 'EOF'
[Unit]
Description=Phishing Detector Web Application
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phishing-detector
Environment=PATH=/opt/phishing-detector/venv/bin
ExecStart=/opt/phishing-detector/venv/bin/python simple_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable phishing-detector
systemctl start phishing-detector
systemctl status phishing-detector
```

### 10. 配置Nginx（可选）
```bash
# 创建Nginx配置
cat > /etc/nginx/sites-available/phishing-detector << 'EOF'
server {
    listen 80;
    server_name 192.168.1.246;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 启用配置
ln -sf /etc/nginx/sites-available/phishing-detector /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试并重载Nginx
nginx -t
systemctl reload nginx
```

## 🎯 训练模型

### 1. 收集数据
```bash
cd /opt/phishing-detector
source venv/bin/activate

# 收集训练数据
python3 data_collection.py
```

### 2. 检查GPU状态
```bash
# 检查GPU状态
nvidia-smi

# 检查PyTorch是否识别GPU
python3 -c "import torch; print(f'GPU数量: {torch.cuda.device_count()}'); print(f'GPU名称: {torch.cuda.get_device_name(0)}')"
```

### 3. 开始训练
```bash
# 启动训练
python3 start_training.py

# 或者直接训练
python3 train_model.py --data phishing_dataset.csv --batch_size 128 --epochs 100 --lr 0.001
```

### 4. 监控训练
```bash
# 查看训练日志
tail -f training.log

# 查看GPU使用情况
watch -n 1 nvidia-smi

# 查看系统资源
htop
```

## 🌐 访问地址

部署完成后，您可以通过以下地址访问：

- **Web应用**: http://192.168.1.246:5000
- **健康检查**: http://192.168.1.246:5000/api/health
- **检测API**: http://192.168.1.246:5000/api/detect

## 🔧 管理命令

### 服务管理
```bash
# 启动服务
systemctl start phishing-detector

# 停止服务
systemctl stop phishing-detector

# 重启服务
systemctl restart phishing-detector

# 查看服务状态
systemctl status phishing-detector

# 查看服务日志
journalctl -u phishing-detector -f
```

### 训练管理
```bash
# 查看训练进程
ps aux | grep train_model

# 停止训练
pkill -f train_model.py

# 查看GPU使用
nvidia-smi
```

## 📊 训练结果

训练完成后，结果文件将保存在：
- `best_model.pth` - 最佳模型
- `training_results.json` - 训练指标
- `confusion_matrix.png` - 混淆矩阵
- `roc_curve.png` - ROC曲线

## 🚀 4090显卡优化

您的246服务器有2张4090显卡，训练时会自动：

- 使用混合精度训练（FP16）
- 启用多GPU训练（DataParallel）
- 优化内存使用
- 使用CUDA内核加速

## 🎉 部署完成

部署完成后，您的钓鱼网站检测器将：

1. ✅ 在246服务器上运行Web应用
2. ✅ 支持4090显卡加速训练
3. ✅ 提供RESTful API接口
4. ✅ 自动化数据处理和模型训练
5. ✅ 支持大规模并发检测

现在您可以通过Web界面或API使用钓鱼网站检测功能！