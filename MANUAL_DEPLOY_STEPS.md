# 🔧 langchao6手动部署步骤

## 📋 当前状态
✅ **GitHub仓库**: https://github.com/mengguiyouziyi/phishing-detector (已更新)
✅ **部署包**: `/tmp/phishing_detector_langchao6.tar.gz` (已创建)
⚠️ **自动上传失败**: 需要手动上传到服务器

## 🚀 手动部署步骤

### 第一步：上传部署包
```bash
# 在本地执行 (需要输入密码: 3646287)
scp /tmp/phishing_detector_langchao6.tar.gz root@192.168.1.246:/tmp/
```

### 第二步：连接到服务器
```bash
ssh root@192.168.1.246
# 密码: 3646287
```

### 第三步：在服务器上执行部署
```bash
# 进入目录
cd /opt

# 备份现有部署 (可选)
if [ -d "phishing-detector-langchao6" ]; then
    mv phishing-detector-langchao6 phishing-detector-backup-$(date +%Y%m%d_%H%M%S)
fi

# 解压部署包
tar -xzf /tmp/phishing_detector_langchao6.tar.gz
cd phishing-detector-langchao6

# 查看文件
ls -la

# 执行一键启动
./langchao6_start.sh
```

### 第四步：验证部署
```bash
# 检查应用状态
ps aux | grep simple_app

# 检查端口占用
netstat -tlnp | grep :5000

# 查看启动日志
tail -f web_app.log

# 测试API
curl http://localhost:5000/api/health
```

### 第五步：访问应用
打开浏览器访问: http://192.168.1.246:5000

## 🎯 训练模型

### 方法1：一键训练
```bash
./train.sh
```

### 方法2：分步训练
```bash
# 激活虚拟环境
source venv/bin/activate

# 检查GPU状态
nvidia-smi

# 收集数据
python3 data_collection.py

# 开始训练
python3 train_model.py --data phishing_dataset.csv --batch_size 128 --epochs 100
```

## 📊 监控命令

### GPU监控
```bash
# 实时监控
watch -n 1 nvidia-smi

# 详细信息
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv
```

### 系统监控
```bash
# CPU和内存
htop

# 磁盘空间
df -h

# 网络连接
netstat -tlnp
```

### 应用监控
```bash
# 查看Python进程
ps aux | grep python

# 查看应用日志
tail -f web_app.log

# 查看训练日志
tail -f training.log
```

## 🌐 API接口

### 健康检查
```bash
curl http://192.168.1.246:5000/api/health
```

### URL检测
```bash
curl -X POST http://192.168.1.246:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### 批量检测
```bash
curl -X POST http://192.168.1.246:5000/api/batch_detect \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com", "https://test.com"]}'
```

## ⚠️ 故障排除

### 端口被占用
```bash
# 查看端口占用
netstat -tlnp | grep :5000

# 杀死占用进程
kill -9 <PID>
```

### GPU未被识别
```bash
# 检查GPU驱动
nvidia-smi

# 检查PyTorch CUDA支持
python3 -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}')"
```

### MySQL连接问题
```bash
# 检查MySQL状态
systemctl status mysql

# 重启MySQL
systemctl restart mysql

# 手动连接测试
mysql -u root -p
```

### 内存不足
```bash
# 减少训练batch size
python3 train_model.py --batch_size 64

# 清理GPU内存
nvidia-smi --gpu-reset -i 0
nvidia-smi --gpu-reset -i 1
```

## 🎉 部署完成后的预期效果

### Web界面
- 访问 http://192.168.1.246:5000
- 可以输入URL进行实时检测
- 显示检测结果和置信度

### 训练功能
- 使用2张RTX 4090并行训练
- 自动收集训练数据
- 实时监控训练进度
- 生成评估报告和可视化图表

### API服务
- RESTful API接口
- 支持单URL和批量检测
- 实时响应
- JSON格式返回结果

## 📞 快速操作指南

### 最常用的命令
```bash
# 连接服务器
ssh root@192.168.1.246

# 查看应用状态
ps aux | grep simple_app

# 查看GPU使用
nvidia-smi

# 查看日志
tail -f /opt/phishing-detector-langchao6/web_app.log

# 重启应用
cd /opt/phishing-detector-langchao6
pkill -f simple_app
nohup python3 simple_app.py > web_app.log 2>&1 &
```

### 训练相关
```bash
# 进入项目目录
cd /opt/phishing-detector-langchao6

# 激活环境
source venv/bin/activate

# 开始训练
./train.sh

# 监控训练
watch -n 1 nvidia-smi
tail -f training.log
```

---

🚀 **按照以上步骤，您就可以在langchao6上成功部署并使用钓鱼网站检测器了！**