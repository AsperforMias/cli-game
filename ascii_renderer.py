"""
ASCII Renderer - ASCII字符渲染系统
处理游戏画面的ASCII艺术渲染和UI显示
"""

import asyncio
from typing import List, Dict, Any, Optional

class ASCIIRenderer:
    """ASCII渲染器类"""
    
    def __init__(self, chan):
        self.chan = chan
        self.width = 120
        self.height = 30
        self.buffer = []
        self.cursor_x = 0
        self.cursor_y = 0
        
        # ANSI颜色代码
        self.colors = {
            'reset': '\x1b[0m',
            'bold': '\x1b[1m',
            'red': '\x1b[31m',
            'green': '\x1b[32m',
            'yellow': '\x1b[33m',
            'blue': '\x1b[34m',
            'magenta': '\x1b[35m',
            'cyan': '\x1b[36m',
            'white': '\x1b[37m',
            'bg_black': '\x1b[40m',
            'bg_red': '\x1b[41m',
            'bg_green': '\x1b[42m',
            'bg_yellow': '\x1b[43m',
            'bg_blue': '\x1b[44m'
        }
    
    async def clear_screen(self):
        """清屏"""
        self.chan.write("\x1b[2J\x1b[H")
    
    async def move_cursor(self, x: int, y: int):
        """移动光标"""
        self.chan.write(f"\x1b[{y+1};{x+1}H")
        self.cursor_x = x
        self.cursor_y = y
    
    async def draw_text(self, text: str, x: int, y: int, color: str = 'white'):
        """在指定位置绘制文本"""
        await self.move_cursor(x, y)
        colored_text = f"{self.colors.get(color, '')}{text}{self.colors['reset']}"
        self.chan.write(colored_text)
    
    async def draw_box(self, x: int, y: int, width: int, height: int, title: str = ""):
        """绘制边框"""
        # 绘制顶部边框
        top_line = "╔" + "═" * (width - 2) + "╗"
        if title:
            title_padded = f" {title} "
            if len(title_padded) < width - 2:
                title_start = (width - len(title_padded)) // 2
                top_line = ("╔" + "═" * (title_start - 1) + 
                           title_padded + 
                           "═" * (width - title_start - len(title_padded) - 1) + "╗")
        
        await self.draw_text(top_line, x, y)
        
        # 绘制侧边和底部
        for i in range(1, height - 1):
            await self.draw_text("║" + " " * (width - 2) + "║", x, y + i)
        
        bottom_line = "╚" + "═" * (width - 2) + "╝"
        await self.draw_text(bottom_line, x, y + height - 1)
    
    async def draw_health_bar(self, current: int, maximum: int, x: int, y: int, width: int = 20):
        """绘制血条"""
        if maximum <= 0:
            return
            
        filled = int((current / maximum) * width)
        bar = "█" * filled + "░" * (width - filled)
        
        # 根据血量设置颜色
        if current / maximum > 0.6:
            color = 'green'
        elif current / maximum > 0.3:
            color = 'yellow'
        else:
            color = 'red'
        
        await self.draw_text(f"HP: [{bar}] {current}/{maximum}", x, y, color)
    
    async def draw_exp_bar(self, current: int, needed: int, x: int, y: int, width: int = 20):
        """绘制经验条"""
        if needed <= 0:
            return
            
        filled = int((current / needed) * width)
        bar = "▓" * filled + "░" * (width - filled)
        
        await self.draw_text(f"EXP: [{bar}] {current}/{needed}", x, y, 'cyan')
    
    async def draw_player_status(self, player):
        """绘制玩家状态面板"""
        await self.clear_screen()
        
        # 绘制状态框
        await self.draw_box(2, 2, 50, 20, f"{player.name} - {player.player_class}")
        
        # 基本信息
        await self.draw_text(f"等级: {player.level}", 4, 4, 'yellow')
        await self.draw_text(f"职业: {player.player_class}", 4, 5, 'cyan')
        
        # 属性
        await self.draw_text("属性:", 4, 7, 'bold')
        await self.draw_text(f"生命值: {player.hp}/{player.max_hp}", 6, 8, 'red')
        await self.draw_text(f"魔法值: {player.mp}/{player.max_mp}", 6, 9, 'blue')
        await self.draw_text(f"攻击力: {player.attack}", 6, 10, 'yellow')
        await self.draw_text(f"防御力: {player.defense}", 6, 11, 'green')
        await self.draw_text(f"敏捷: {player.agility}", 6, 12, 'magenta')
        
        # 经验值
        await self.draw_health_bar(player.hp, player.max_hp, 4, 14)
        if hasattr(player, 'exp') and hasattr(player, 'exp_needed'):
            await self.draw_exp_bar(player.exp, player.exp_needed, 4, 15)
        
        await self.draw_text("按任意键继续...", 4, 18, 'white')
    
    async def draw_inventory(self, inventory):
        """绘制背包界面"""
        await self.clear_screen()
        
        await self.draw_box(2, 2, 80, 25, "背包")
        
        if not inventory or len(inventory) == 0:
            await self.draw_text("背包是空的", 4, 4, 'yellow')
        else:
            await self.draw_text("物品列表:", 4, 4, 'bold')
            
            for i, item in enumerate(inventory):
                y_pos = 6 + i
                if y_pos < 25:
                    item_text = f"{i+1}. {item.name} x{item.quantity}"
                    if hasattr(item, 'description'):
                        item_text += f" - {item.description}"
                    await self.draw_text(item_text, 6, y_pos)
        
        await self.draw_text("按任意键继续...", 4, 24, 'white')
    
    async def draw_scene_description(self, scene):
        """绘制场景描述"""
        await self.clear_screen()
        
        # 场景标题
        await self.draw_text(f"=== {scene.name} ===", 2, 2, 'bold')
        
        # 场景描述
        description_lines = self._wrap_text(scene.description, 100)
        for i, line in enumerate(description_lines):
            await self.draw_text(line, 2, 4 + i)
        
        # 显示可用出口
        if scene.exits:
            y_offset = 6 + len(description_lines)
            await self.draw_text("可去的方向:", 2, y_offset, 'yellow')
            for direction, destination in scene.exits.items():
                y_offset += 1
                await self.draw_text(f"  {direction} -> {destination}", 4, y_offset, 'cyan')
        
        # 显示NPC
        if hasattr(scene, 'npcs') and scene.npcs:
            y_offset = 8 + len(description_lines) + len(scene.exits)
            await self.draw_text("这里的人:", 2, y_offset, 'yellow')
            for npc in scene.npcs:
                y_offset += 1
                await self.draw_text(f"  {npc.name} - {npc.profession}", 4, y_offset, 'green')
    
    async def draw_game_ui(self, player, current_scene):
        """绘制游戏主界面"""
        # 上半部分显示场景
        scene_height = 20
        ui_height = 8
        
        # 清空指定区域而不是整个屏幕
        for i in range(self.height):
            await self.move_cursor(0, i)
            self.chan.write(" " * self.width)
        
        # 绘制场景区域
        await self.draw_box(0, 0, self.width, scene_height, current_scene)
        
        # 绘制玩家状态栏
        status_y = scene_height
        await self.draw_box(0, status_y, self.width, ui_height, "状态")
        
        # 玩家基本信息
        await self.draw_text(f"{player.name} (Lv.{player.level})", 2, status_y + 1, 'yellow')
        await self.draw_health_bar(player.hp, player.max_hp, 2, status_y + 2, 30)
        
        if hasattr(player, 'mp'):
            await self.draw_text(f"MP: {player.mp}/{player.max_mp}", 35, status_y + 2, 'blue')
        
        # 提示信息
        await self.draw_text("输入 'help' 查看命令帮助", 2, status_y + 4, 'white')
        
        # 输入提示
        await self.draw_prompt(">>> ")
    
    async def draw_prompt(self, prompt: str = "> "):
        """绘制输入提示"""
        await self.move_cursor(0, self.height - 1)
        self.chan.write(f"{self.colors['bold']}{prompt}{self.colors['reset']}")
    
    async def draw_message(self, message: str, color: str = 'white'):
        """绘制消息"""
        # 在消息区域显示
        message_lines = self._wrap_text(message, self.width - 4)
        
        # 滚动显示多行消息
        for line in message_lines:
            self.chan.write(f"{self.colors.get(color, '')}{line}{self.colors['reset']}\r\n")
    
    async def draw_dialogue_box(self, npc_name: str, message: str):
        """绘制对话框"""
        box_width = min(80, self.width - 10)
        box_height = 8
        x = (self.width - box_width) // 2
        y = self.height - box_height - 2
        
        await self.draw_box(x, y, box_width, box_height, f"对话 - {npc_name}")
        
        # 包装文本
        wrapped_lines = self._wrap_text(message, box_width - 4)
        
        for i, line in enumerate(wrapped_lines[:box_height-3]):
            await self.draw_text(line, x + 2, y + 2 + i)
    
    def _wrap_text(self, text: str, width: int) -> List[str]:
        """文本换行处理"""
        if not text:
            return [""]
            
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + word) + 1 <= width:
                if current_line:
                    current_line += " "
                current_line += word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [""]
    
    async def draw_combat_ui(self, player, enemy):
        """绘制战斗界面"""
        await self.clear_screen()
        
        # 绘制战斗框架
        await self.draw_box(2, 2, self.width - 4, 25, "战斗")
        
        # 敌人信息
        await self.draw_text(f"敌人: {enemy.name}", 4, 4, 'red')
        await self.draw_health_bar(enemy.hp, enemy.max_hp, 4, 5, 40)
        
        # 玩家信息
        await self.draw_text(f"玩家: {player.name}", 4, 15, 'green')
        await self.draw_health_bar(player.hp, player.max_hp, 4, 16, 40)
        
        # 战斗选项
        await self.draw_text("战斗选项:", 4, 20, 'yellow')
        await self.draw_text("1. 攻击", 6, 21)
        await self.draw_text("2. 防御", 6, 22)
        await self.draw_text("3. 使用物品", 6, 23)
        await self.draw_text("4. 逃跑", 6, 24)
    
    async def animate_text(self, text: str, x: int, y: int, delay: float = 0.05):
        """文字打字机效果"""
        await self.move_cursor(x, y)
        for char in text:
            self.chan.write(char)
            await asyncio.sleep(delay)
    
    async def flash_screen(self, color: str = 'red', duration: float = 0.2):
        """屏幕闪烁效果"""
        self.chan.write(f"{self.colors.get('bg_' + color, '')}")
        await self.clear_screen()
        await asyncio.sleep(duration)
        self.chan.write(f"{self.colors['reset']}")
        await self.clear_screen()
