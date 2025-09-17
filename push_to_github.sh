#!/bin/bash

# 推送到GitHub的脚本

echo "🚀 推送钓鱼网站检测器到GitHub"

# 请替换为您的GitHub仓库地址
GITHUB_REPO="https://github.com/your-username/phishing-detector.git"

# 添加远程仓库
git remote add origin $GITHUB_REPO

# 推送到GitHub
git push -u origin master

echo "✅ 代码已推送到GitHub!"
echo "🔗 仓库地址: $GITHUB_REPO"