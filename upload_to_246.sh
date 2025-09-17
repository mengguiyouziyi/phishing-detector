#!/bin/bash

# 上传钓鱼网站检测器到246服务器

SERVER="192.168.1.246"
USER="root"
REMOTE_DIR="/opt/phishing-detector"

echo "🚀 上传钓鱼网站检测器到246服务器"
echo "服务器: $SERVER"
echo "用户: $USER"
echo "远程目录: $REMOTE_DIR"
echo ""

# 创建压缩包
echo "📦 创建部署包..."
tar -czf /tmp/phishing_detector.tar.gz \
    --exclude=.git \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    --exclude=.DS_Store \
    --exclude="*.log" \
    --exclude="*.pth" \
    --exclude="*.png" \
    --exclude="*.json" \
    .

echo "✅ 部署包创建完成: /tmp/phishing_detector.tar.gz"

# 上传文件
echo "📤 上传文件到服务器..."
scp /tmp/phishing_detector.tar.gz $USER@$SERVER:/tmp/

if [ $? -eq 0 ]; then
    echo "✅ 文件上传成功"
else
    echo "❌ 文件上传失败"
    exit 1
fi

# 创建远程解压脚本
echo "🔧 创建远程部署脚本..."
cat > /tmp/deploy_remote.sh << 'EOF'
#!/bin/bash
echo "=== 在246服务器上部署钓鱼网站检测器 ==="

# 创建目录
mkdir -p /opt/phishing-detector
cd /opt/phishing-detector

# 备份现有部署
if [ -d "backup" ]; then
    rm -rf backup
fi
mkdir -p backup

# 备份重要文件
[ -f "best_model.pth" ] && cp best_model.pth backup/
[ -f "training_results.json" ] && cp training_results.json backup/
[ -f "phishing_dataset.csv" ] && cp phishing_dataset.csv backup/

# 解压新版本
tar -xzf /tmp/phishing_detector.tar.gz --strip-components=1

# 恢复备份的文件
[ -f "backup/best_model.pth" ] && cp backup/best_model.pth ./
[ -f "backup/training_results.json" ] && cp backup/training_results.json ./
[ -f "backup/phishing_dataset.csv" ] && cp backup/phishing_dataset.csv ./

# 设置权限
chmod +x *.py

echo "✅ 部署完成"
echo "📁 部署目录: /opt/phishing-detector"
echo "🔗 访问地址: http://$(hostname -I | awk '{print $1}'):5000"
echo ""

echo "📋 下一步操作："
echo "1. ssh root@192.168.1.246"
echo "2. cd /opt/phishing-detector"
echo "3. python3 -m venv venv"
echo "4. source venv/bin/activate"
echo "5. pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
echo "6. pip install -r requirements.txt"
echo "7. python3 simple_app.py &"
echo ""

EOF

# 上传部署脚本
scp /tmp/deploy_remote.sh $USER@$SERVER:/tmp/

# 执行远程部署
echo "🚀 执行远程部署..."
ssh $USER@$SERVER 'bash /tmp/deploy_remote.sh'

# 清理临时文件
rm -f /tmp/phishing_detector.tar.gz
rm -f /tmp/deploy_remote.sh

echo "✅ 部署完成！"
echo ""
echo "🔗 访问地址: http://$SERVER:5000"
echo "📖 详细说明: 请查看 MANUAL_DEPLOY_246.md"
echo ""
echo "🎯 下一步："
echo "1. 连接到服务器: ssh root@$SERVER"
echo "2. 进入目录: cd /opt/phishing-detector"
echo "3. 安装依赖: 按照上述步骤执行"
echo "4. 启动应用: python3 simple_app.py"
echo "5. 开始训练: python3 start_training.py"