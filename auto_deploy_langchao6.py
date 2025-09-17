#!/usr/bin/env python3
"""
自动部署钓鱼网站检测器到langchao6服务器
"""

import subprocess
import sys
import os
import time
import socket
import threading
import queue

def run_command(cmd, check=True, timeout=30):
    """运行命令并返回结果"""
    print(f"执行: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True, timeout=timeout)
        if result.stdout:
            print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")
        return result
    except subprocess.TimeoutExpired:
        print(f"命令超时: {cmd}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"命令失败: {e}")
        return None

def check_server_connection():
    """检查服务器连接"""
    print("🔍 检查langchao6服务器连接...")

    # 尝试ping服务器
    result = run_command("ping -c 3 192.168.1.246", check=False)
    if result and result.returncode == 0:
        print("✅ 服务器连接正常")
        return True
    else:
        print("❌ 服务器连接失败")
        return False

def create_deployment_package():
    """创建部署包"""
    print("📦 创建部署包...")

    # 重新创建部署包确保是最新的
    result = run_command("python3 deploy_to_langchao6.py", check=False)
    if result and result.returncode == 0:
        print("✅ 部署包创建成功")
        return "/tmp/phishing_detector_langchao6.tar.gz"
    else:
        print("❌ 部署包创建失败")
        return None

def upload_to_server():
    """上传部署包到服务器"""
    print("📤 上传部署包到langchao6服务器...")

    # 使用scp上传（需要密码）
    deploy_script = '''#!/bin/bash
echo "🚀 开始上传部署包..."
echo "请输入密码: 3646287"

# 使用scp上传
scp -o StrictHostKeyChecking=no /tmp/phishing_detector_langchao6.tar.gz root@192.168.1.246:/tmp/

if [ $? -eq 0 ]; then
    echo "✅ 上传成功"
    exit 0
else
    echo "❌ 上传失败"
    exit 1
fi
'''

    with open('/tmp/upload_script.sh', 'w') as f:
        f.write(deploy_script)

    os.chmod('/tmp/upload_script.sh', 0o755)

    print("🔧 请在弹出的窗口中输入密码: 3646287")
    result = run_command("/tmp/upload_script.sh", check=False)

    if result and result.returncode == 0:
        print("✅ 上传成功")
        return True
    else:
        print("❌ 上传失败")
        return False

def deploy_on_server():
    """在服务器上部署应用"""
    print("🔧 在langchao6服务器上部署应用...")

    # 创建远程部署脚本
    remote_script = '''#!/bin/bash
echo "=== 在langchao6服务器上部署钓鱼网站检测器 ==="

# 进入目录
cd /opt

# 备份现有部署
if [ -d "phishing-detector-backup" ]; then
    rm -rf phishing-detector-backup
fi
if [ -d "phishing-detector-langchao6" ]; then
    mv phishing-detector-langchao6 phishing-detector-backup
fi

# 解压新版本
tar -xzf /tmp/phishing_detector_langchao6.tar.gz
cd phishing-detector-langchao6

# 检查文件
echo "📁 检查部署文件..."
ls -la

# 运行启动脚本
echo "🚀 启动应用..."
./langchao6_start.sh > startup.log 2>&1 &
STARTUP_PID=$!

# 等待启动
echo "⏳ 等待应用启动..."
sleep 10

# 检查应用状态
echo "🔍 检查应用状态..."
ps aux | grep simple_app

# 检查端口
echo "🔍 检查端口占用..."
netstat -tlnp | grep :5000

# 检查日志
echo "📄 查看启动日志..."
tail -20 startup.log

echo "=== 部署完成 ==="
echo "🌐 访问地址: http://$(hostname -I | awk '{print $1}'):5000"
echo "📊 日志文件: tail -f web_app.log"
echo "🎯 训练命令: ./train.sh"
echo ""
echo "📋 下一步操作:"
echo "1. 访问 http://$(hostname -I | awk '{print $1}'):5000"
echo "2. 运行训练: ./train.sh"
echo "3. 监控GPU: watch -n 1 nvidia-smi"
'''

    with open('/tmp/remote_deploy.sh', 'w') as f:
        f.write(remote_script)

    os.chmod('/tmp/remote_deploy.sh', 0o755)

    # 使用ssh执行远程脚本
    print("🔧 开始远程部署，请输入密码...")
    deploy_cmd = "ssh -o StrictHostKeyChecking=no root@192.168.1.246 'bash -s' < /tmp/remote_deploy.sh"

    result = run_command(deploy_cmd, check=False, timeout=300)

    if result:
        print("📄 远程部署输出:")
        print(result.stdout)
        if result.stderr:
            print("⚠️ 部署警告:")
            print(result.stderr)

        # 检查部署是否成功
        if "部署完成" in result.stdout:
            print("✅ 部署成功")
            return True
        else:
            print("⚠️ 部署可能有问题，请检查输出")
            return False
    else:
        print("❌ 远程部署失败")
        return False

def test_deployment():
    """测试部署是否成功"""
    print("🧪 测试部署结果...")

    # 测试健康检查API
    test_script = '''#!/bin/bash
echo "🧪 测试应用响应..."
curl -s http://192.168.1.246:5000/api/health | head -5
echo ""
echo "🧪 测试Web界面..."
curl -s -I http://192.168.1.246:5000 | head -3
'''

    with open('/tmp/test_deploy.sh', 'w') as f:
        f.write(test_script)

    os.chmod('/tmp/test_deploy.sh', 0o755)

    # 等待几秒钟确保应用完全启动
    print("⏳ 等待应用启动...")
    time.sleep(5)

    result = run_command("/tmp/test_deploy.sh", check=False)

    if result and result.returncode == 0:
        print("✅ 应用响应正常")
        return True
    else:
        print("⚠️ 应用响应异常，请检查服务器状态")
        return False

def monitor_deployment():
    """监控部署状态"""
    print("📊 监控部署状态...")

    monitor_script = '''#!/bin/bash
echo "📊 langchao6服务器状态监控"
echo "================================"
echo "🔍 系统信息:"
uname -a
echo ""
echo "💾 内存使用:"
free -h
echo ""
echo "🖥️ CPU信息:"
lscpu | grep 'Model name' | cut -d: -f2 | xargs
echo ""
echo "🎮 GPU状态:"
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits
echo ""
echo "🌐 网络端口:"
netstat -tlnp | grep :5000
echo ""
echo "🏃 应用进程:"
ps aux | grep simple_app | grep -v grep
echo ""
echo "📄 最近日志:"
if [ -f "/opt/phishing-detector-langchao6/web_app.log" ]; then
    tail -5 /opt/phishing-detector-langchao6/web_app.log
else
    echo "日志文件未找到"
fi
'''

    with open('/tmp/monitor.sh', 'w') as f:
        f.write(monitor_script)

    os.chmod('/tmp/monitor.sh', 0o755)

    result = run_command("ssh -o StrictHostKeyChecking=no root@192.168.1.246 'bash -s' < /tmp/monitor.sh", check=False)

    if result:
        print("📊 监控信息:")
        print(result.stdout)

def main():
    """主函数"""
    print("🚀 钓鱼网站检测器 - 自动部署到langchao6服务器")
    print("=" * 60)

    # 步骤1: 检查服务器连接
    if not check_server_connection():
        print("❌ 服务器连接失败，请检查网络和服务器状态")
        return

    # 步骤2: 创建部署包
    deploy_package = create_deployment_package()
    if not deploy_package:
        print("❌ 部署包创建失败")
        return

    # 步骤3: 上传到服务器
    if not upload_to_server():
        print("❌ 上传失败")
        return

    # 步骤4: 在服务器上部署
    if not deploy_on_server():
        print("❌ 部署失败")
        return

    # 步骤5: 测试部署
    if not test_deployment():
        print("⚠️ 部署测试失败，但应用可能已启动")

    # 步骤6: 监控状态
    monitor_deployment()

    print("\n🎉 部署流程完成！")
    print("=" * 60)
    print("🌐 访问应用: http://192.168.1.246:5000")
    print("📊 健康检查: http://192.168.1.246:5000/api/health")
    print("🎯 训练模型: ssh root@192.168.1.246 'cd /opt/phishing-detector-langchao6 && ./train.sh'")
    print("📊 监控GPU: ssh root@192.168.1.246 'nvidia-smi'")
    print("")
    print("📋 下一步操作:")
    print("1. 打开浏览器访问 http://192.168.1.246:5000")
    print("2. 测试URL检测功能")
    print("3. 连接到服务器开始训练: ssh root@192.168.1.246")
    print("4. 运行训练命令: ./train.sh")

if __name__ == "__main__":
    main()