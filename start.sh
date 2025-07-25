#!/bin/bash
# CLI RPG Game 启动脚本

echo "CLI RPG Game - 启动中..."

# 检查Python版本
python3 --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "错误: 需要Python 3.8或更高版本"
    exit 1
fi

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "错误: 找不到 requirements.txt 文件"
    exit 1
fi

# 安装依赖（如果需要）
echo "检查依赖..."
pip3 install -r requirements.txt > /dev/null 2>&1

# 创建数据目录
mkdir -p data/scenes data/npcs data/items saves

# 启动游戏服务器
echo "启动游戏服务器..."
echo "连接方式: ssh -p 2222 player@localhost"
echo "默认密码: rpg2025"
echo "按 Ctrl+C 停止服务器"
echo ""

python3 main.py
