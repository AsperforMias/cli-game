# CLI RPG Game

一个基于SSH的命令行RPG游戏，具备AI驱动的NPC对话系统。

## 特性

- 🎮 完整的RPG游戏机制（角色创建、升级、技能、装备）
- 🤖 AI驱动的NPC对话系统
- 🌍 丰富的游戏世界和场景
- ⚔️ 战斗系统
- 🛒 商店和交易系统
- 📋 任务系统
- 🎨 ASCII艺术渲染
- 🔐 SSH远程游戏

## 安装和运行

### 环境要求

- Python 3.8+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置AI服务（可选）

如果要使用AI功能，需要配置API密钥：

```bash
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选，默认为OpenAI
```

如果不配置，游戏将使用模拟的AI响应。

### 启动服务器

```bash
python main.py
```

### 连接游戏

```bash
ssh -p 2222 player@localhost
```

默认密码：`rpg2025`

## 游戏玩法

### 角色创建

首次连接时，你需要创建一个角色：
1. 输入角色名字
2. 选择职业（战士、法师、盗贼）

### 基本命令

- `look/l` - 查看周围环境
- `move/go <方向>` - 移动到指定方向
- `talk <NPC名字>` - 与NPC对话
- `inventory/inv` - 查看背包
- `status/stat` - 查看角色状态
- `help` - 显示帮助
- `quit` - 退出游戏

### 职业特色

#### 战士 (Warrior)
- 高生命值和攻击力
- 适合近战战斗
- 技能：剑术精通、盾牌格挡、战吼

#### 法师 (Mage)
- 高魔法值和智力
- 强大的魔法攻击
- 技能：火焰魔法、冰霜魔法、法力回复

#### 盗贼 (Rogue)
- 高敏捷和暴击
- 擅长潜行和偷袭
- 技能：潜行、背刺、开锁

### AI对话系统

- NPC具有情感状态，会影响对话态度
- AI会根据角色设定和当前情况响应
- 支持记忆系统，NPC会记住之前的对话
- 只讨论游戏相关内容，拒绝现实世界话题

## 游戏世界

### 场景介绍

- **新手村**: 安全的起始区域，有各种NPC和商店
- **森林入口**: 通往冒险区域的入口
- **森林深处**: 危险区域，有怪物和宝藏
- **水晶洞穴**: 神秘的洞穴，蕴含魔法能量
- **古代遗迹**: 失落文明的遗迹，隐藏着秘密

### NPC类型

- **村长**: 任务发布者，提供主线任务
- **铁匠**: 出售武器和护甲
- **药剂师**: 出售各种药水
- **商人**: 各种物品交易
- **训练师**: 技能学习和升级

## 技术架构

### 核心模块

- `main.py` - SSH服务器和主入口
- `game_engine.py` - 游戏核心引擎
- `ai_service.py` - AI对话服务
- `ascii_renderer.py` - ASCII渲染系统
- `player.py` - 玩家角色系统
- `npc.py` - NPC系统
- `world.py` - 游戏世界管理

### 数据结构

- `data/scenes/` - 场景数据
- `data/npcs/` - NPC数据
- `data/items/` - 物品数据

## 开发指南

### 添加新场景

编辑 `world.py` 中的 `create_default_scenes()` 方法，或在 `data/scenes/scenes.json` 中添加场景数据。

### 添加新NPC

在 `npc.py` 中创建NPC类，或在 `data/npcs/npcs.json` 中添加NPC数据。

### 添加新物品

在 `data/items/items.json` 中添加物品数据。

### 自定义AI响应

修改 `ai_service.py` 中的提示词和响应逻辑。

## 故障排除

### 连接问题

1. 确保防火墙允许2222端口
2. 检查SSH服务是否正常启动
3. 验证密码是否正确

### AI功能问题

1. 检查API密钥是否正确配置
2. 验证网络连接
3. 查看日志输出的错误信息

### 游戏数据问题

1. 检查 `data/` 目录是否存在
2. 验证JSON文件格式是否正确
3. 查看控制台错误日志

## 贡献

欢迎提交Issue和Pull Request来改进游戏！

## 许可证

MIT License - 详见 LICENSE 文件
