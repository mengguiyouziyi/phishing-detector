# 🚀 langchao6服务器部署命令

## 📋 服务器信息
- **主机名**: langchao6
- **IP地址**: 192.168.1.246
- **用户名**: root
- **密码**: 3646287
- **GPU**: 2x RTX 4090 (24GB each)

## 🚀 快速部署命令

### 在本地执行上传命令：
```bash
scp /tmp/phishing_detector_langchao6.tar.gz root@192.168.1.246:/tmp/
```

### 在langchao6服务器上执行：
```bash
# 1. 连接到服务器
ssh root@192.168.1.246
# 密码: 3646287

# 2. 进入目录并解压
cd /opt
tar -xzf /tmp/phishing_detector_langchao6.tar.gz
cd phishing-detector-langchao6

# 3. 运行一键启动脚本
./langchao6_start.sh
```

## 🎯 手动部署（可选）

如果自动脚本有问题，可以手动执行：

```bash
# 1. 安装系统依赖
apt update
apt install -y python3-pip python3-venv mysql-server

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装PyTorch (支持4090)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. 安装依赖
pip install -r requirements.txt

# 5. 启动MySQL
systemctl start mysql
systemctl enable mysql

# 6. 启动Web应用
python3 simple_app.py &
```

## 🌐 访问应用

部署完成后访问：
- **Web应用**: http://192.168.1.246:5000
- **API健康检查**: http://192.168.1.246:5000/api/health
- **检测API**: http://192.168.1.246:5000/api/detect

## 🎯 训练模型

### 一键训练：
```bash
./train.sh
```

### 手动训练：
```bash
# 激活环境
source venv/bin/activate

# 收集数据
python3 data_collection.py

# 开始训练
python3 train_model.py --data phishing_dataset.csv --batch_size 128 --epochs 100
```

## 📊 监控命令

```bash
# GPU使用情况
nvidia-smi
watch -n 1 nvidia-smi

# 应用日志
tail -f web_app.log

# 系统资源
htop

# 进程状态
ps aux | grep python
```

## 🔧 管理命令

```bash
# 查看应用状态
systemctl status phishing-detector

# 重启应用
systemctl restart phishing-detector

# 查看日志
journalctl -u phishing-detector -f

# MySQL状态
systemctl status mysql
```

## ⚠️ 故障排除

### 如果遇到端口占用：
```bash
netstat -tlnp | grep :5000
kill -9 <PID>
```

### 如果GPU未被识别：
```bash
nvidia-smi
python3 -c "import torch; print(torch.cuda.is_available())"
```

### 如果MySQL连接失败：
```bash
systemctl restart mysql
mysql -u root -p
```

---

🚀 **部署完成！** 现在您可以在langchao6上使用钓鱼网站检测器了！