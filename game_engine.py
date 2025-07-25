"""
Game Engine - 游戏核心引擎
处理游戏状态、玩家输入、画面渲染等
"""

import asyncio
import json
import os
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from ascii_renderer import ASCIIRenderer
from player import Player
from npc import NPC
from world import World
from combat import CombatSystem, create_enemy

class GameState(Enum):
    """游戏状态枚举"""
    MAIN_MENU = "main_menu"
    CHARACTER_CREATION = "character_creation"
    PLAYING = "playing"
    INVENTORY = "inventory"
    DIALOGUE = "dialogue"
    COMBAT = "combat"
    PAUSE = "pause"

@dataclass
class InputCommand:
    """输入命令结构"""
    command: str
    args: List[str]

class GameEngine:
    """游戏引擎核心类"""
    
    def __init__(self, chan, ai_service):
        self.chan = chan
        self.ai_service = ai_service
        self.renderer = ASCIIRenderer(chan)
        self.terminal_width = 120
        self.terminal_height = 30
        self.running = True
        self.state = GameState.MAIN_MENU
        
        # 游戏对象
        self.player = None
        self.world = World()
        self.current_scene = None
        self.dialogue_npc = None
        self.combat_system = CombatSystem(self.renderer)
        
        # 输入缓冲
        self.input_buffer = ""
        self.command_history = []
        
    async def run(self):
        """游戏主循环"""
        try:
            await self.initialize()
            
            while self.running:
                # 处理输入
                await self.handle_input()
                
                # 更新游戏状态
                await self.update()
                
                # 渲染画面
                await self.render()
                
                # 控制帧率
                await asyncio.sleep(0.05)
                
        finally:
            await self.cleanup()
    
    async def initialize(self):
        """初始化游戏"""
        # 设置终端
        self.chan.write("\x1b[?25l")  # 隐藏光标
        self.chan.write("\x1b[?1049h")  # 进入备用屏幕
        self.chan.write("\x1b[2J\x1b[H")  # 清屏
        
        # 加载游戏数据
        await self.load_game_data()
        
        # 显示欢迎界面
        await self.show_welcome()
    
    async def cleanup(self):
        """清理资源"""
        try:
            self.chan.write("\x1b[?25h")  # 显示光标
            self.chan.write("\x1b[?1049l")  # 退出备用屏幕
            self.chan.write("\x1b[2J\x1b[H")  # 清屏
            await self.chan.write("感谢游玩！再见！\r\n")
        except:
            pass
    
    async def load_game_data(self):
        """加载游戏数据"""
        # 确保数据目录存在
        os.makedirs("data/scenes", exist_ok=True)
        os.makedirs("data/npcs", exist_ok=True)
        os.makedirs("data/items", exist_ok=True)
        
        # 加载世界数据
        await self.world.load_data()
    
    async def show_welcome(self):
        """显示欢迎界面"""
        welcome_art = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ████████╗██╗  ██╗███████╗    ██████╗ ██████╗  ██████╗     ██████╗  █████╗  ║
║   ╚══██╔══╝██║  ██║██╔════╝    ██╔══██╗██╔══██╗██╔════╝    ██╔════╝ ██╔══██╗ ║
║      ██║   ███████║█████╗      ██████╔╝██████╔╝██║  █████╗  ██║ ███╗██╔═══██╗ ║
║      ██║   ██╔══██║██╔══╝      ██╔══██╗██╔═══╝ ██║   ╚══██╗ ██║   ██║██║   ██║ ║
║      ██║   ██║  ██║███████╗    ██║  ██║██║     ╚██████╗██╔╝ ╚██████╔╝╚█████╔╝ ║
║      ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚═╝  ╚═╝╚═╝      ╚═════╝╚═╝   ╚═════╝  ╚════╝  ║
║                                                                              ║
║                          欢迎来到命令行RPG世界！                              ║
║                                                                              ║
║  指令说明:                                                                   ║
║    new     - 创建新角色                                                      ║
║    load    - 加载角色                                                        ║
║    help    - 查看帮助                                                        ║
║    quit    - 退出游戏                                                        ║
║                                                                              ║
║  在游戏中输入 'help' 获取更多指令                                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        await self.renderer.draw_text(welcome_art, 0, 0)
        await self.renderer.draw_prompt("请输入指令: ")
    
    async def handle_input(self):
        """处理用户输入"""
        try:
            if self.chan.reader._buffer:
                data = await self.chan.read(1024)
                for char in data:
                    if char == '\r' or char == '\n':
                        if self.input_buffer.strip():
                            await self.process_command(self.input_buffer.strip())
                            self.command_history.append(self.input_buffer.strip())
                            self.input_buffer = ""
                    elif char == '\b' or char == '\x7f':  # 退格键
                        if self.input_buffer:
                            self.input_buffer = self.input_buffer[:-1]
                    elif char.isprintable():
                        self.input_buffer += char
        except:
            self.running = False
    
    async def process_command(self, command_text: str):
        """处理命令"""
        parts = command_text.split()
        if not parts:
            return
            
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if self.state == GameState.MAIN_MENU:
            await self.handle_menu_command(command, args)
        elif self.state == GameState.CHARACTER_CREATION:
            await self.handle_character_creation(command, args)
        elif self.state == GameState.PLAYING:
            await self.handle_game_command(command, args)
        elif self.state == GameState.DIALOGUE:
            await self.handle_dialogue_command(command, args)
    
    async def handle_menu_command(self, command: str, args: List[str]):
        """处理主菜单命令"""
        if command == "new":
            self.state = GameState.CHARACTER_CREATION
            await self.start_character_creation()
        elif command == "load":
            await self.load_character()
        elif command == "help":
            await self.show_help()
        elif command == "quit":
            self.running = False
        else:
            await self.renderer.draw_message("未知命令，请输入 'help' 查看帮助")
    
    async def handle_character_creation(self, command: str, args: List[str]):
        """处理角色创建"""
        if not hasattr(self, '_creation_step'):
            self._creation_step = 0
            self._character_data = {}
        
        if self._creation_step == 0:  # 输入名字
            if command:
                self._character_data['name'] = command
                self._creation_step = 1
                await self.renderer.draw_message(f"你好，{command}！请选择职业：")
                await self.renderer.draw_message("1. 战士 (高血量，高攻击)")
                await self.renderer.draw_message("2. 法师 (高魔力，魔法攻击)")
                await self.renderer.draw_message("3. 盗贼 (高敏捷，暴击)")
        elif self._creation_step == 1:  # 选择职业
            class_map = {"1": "warrior", "2": "mage", "3": "rogue"}
            if command in class_map:
                self._character_data['class'] = class_map[command]
                await self.create_player()
                self.state = GameState.PLAYING
                self.current_scene = "starting_village"
                await self.renderer.draw_message("角色创建完成！开始你的冒险吧！")
            else:
                await self.renderer.draw_message("请输入 1、2 或 3")
    
    async def create_player(self):
        """创建玩家角色"""
        self.player = Player(
            name=self._character_data['name'],
            player_class=self._character_data['class']
        )
        delattr(self, '_creation_step')
        delattr(self, '_character_data')
    
    async def handle_game_command(self, command: str, args: List[str]):
        """处理游戏中的命令"""
        if command == "look" or command == "l":
            await self.look_around()
        elif command == "move" or command == "go":
            if args:
                await self.move_to(args[0])
            else:
                await self.renderer.draw_message("去哪里？用法: move <方向>")
        elif command == "talk":
            if args:
                await self.talk_to_npc(args[0])
            else:
                await self.renderer.draw_message("和谁说话？用法: talk <NPC名字>")
        elif command == "inventory" or command == "inv":
            await self.show_inventory()
        elif command == "status" or command == "stat":
            await self.show_status()
        elif command == "attack" or command == "fight":
            if args:
                await self.attack_enemy(args[0])
            else:
                await self.renderer.draw_message("攻击谁？用法: attack <敌人名字>")
        elif command == "use":
            if args:
                await self.use_item(args[0])
            else:
                await self.renderer.draw_message("使用什么？用法: use <物品名字>")
        elif command == "equip":
            if args:
                await self.equip_item(args[0])
            else:
                await self.renderer.draw_message("装备什么？用法: equip <物品名字>")
        elif command == "unequip":
            if args:
                await self.unequip_item(args[0])
            else:
                await self.renderer.draw_message("脱下什么？用法: unequip <装备槽位>")
        elif command == "save":
            await self.save_game()
        elif command == "help":
            await self.show_game_help()
        elif command == "quit":
            self.running = False
        else:
            await self.renderer.draw_message("未知命令，输入 'help' 查看帮助")
    
    async def handle_dialogue_command(self, command: str, args: List[str]):
        """处理对话中的命令"""
        if command == "exit" or command == "bye":
            self.state = GameState.PLAYING
            self.dialogue_npc = None
            await self.renderer.draw_message("对话结束")
        else:
            # 将输入发送给AI处理
            full_text = command + " " + " ".join(args)
            response = await self.ai_service.process_dialogue(
                self.dialogue_npc, full_text, self.player
            )
            await self.renderer.draw_message(f"{self.dialogue_npc.name}: {response}")
    
    async def look_around(self):
        """查看周围环境"""
        scene = self.world.get_scene(self.current_scene)
        if scene:
            await self.renderer.draw_scene_description(scene)
    
    async def move_to(self, direction: str):
        """移动到指定方向"""
        scene = self.world.get_scene(self.current_scene)
        if scene and direction in scene.exits:
            self.current_scene = scene.exits[direction]
            await self.renderer.draw_message(f"你向{direction}走去...")
            await self.look_around()
        else:
            await self.renderer.draw_message("那个方向没有路")
    
    async def talk_to_npc(self, npc_name: str):
        """与NPC对话"""
        scene = self.world.get_scene(self.current_scene)
        if scene:
            npc = scene.get_npc(npc_name)
            if npc:
                self.dialogue_npc = npc
                self.state = GameState.DIALOGUE
                greeting = await self.ai_service.get_npc_greeting(npc, self.player)
                await self.renderer.draw_message(f"{npc.name}: {greeting}")
                await self.renderer.draw_message("(输入 'exit' 结束对话)")
            else:
                await self.renderer.draw_message(f"这里没有叫{npc_name}的人")
    
    async def show_inventory(self):
        """显示背包"""
        if self.player:
            await self.renderer.draw_inventory(self.player.inventory)
    
    async def show_status(self):
        """显示状态"""
        if self.player:
            await self.renderer.draw_player_status(self.player)
    
    async def show_help(self):
        """显示帮助"""
        help_text = """
可用命令：
  new      - 创建新角色
  load     - 加载已保存的角色
  help     - 显示此帮助
  quit     - 退出游戏
"""
        await self.renderer.draw_message(help_text)
    
    async def show_game_help(self):
        """显示游戏内帮助"""
        help_text = """
游戏命令：
  look/l           - 查看周围环境
  move/go <方向>   - 移动到指定方向
  talk <NPC>       - 与NPC对话
  attack/fight <敌人> - 攻击敌人
  inventory/inv    - 查看背包
  status/stat      - 查看角色状态
  use <物品>       - 使用物品
  equip <物品>     - 装备物品
  unequip <槽位>   - 脱下装备
  save             - 保存游戏
  help             - 显示此帮助
  quit             - 退出游戏
"""
        await self.renderer.draw_message(help_text)
    
    async def attack_enemy(self, enemy_name: str):
        """攻击敌人"""
        scene = self.world.get_scene(self.current_scene)
        if not scene:
            await self.renderer.draw_message("你不在任何场景中")
            return
        
        # 查找敌人NPC
        enemy_npc = None
        for npc in scene.npcs:
            if (npc.name.lower() == enemy_name.lower() or 
                npc.id.lower() == enemy_name.lower()) and npc.is_hostile:
                enemy_npc = npc
                break
        
        if not enemy_npc:
            # 生成随机敌人（如果是危险区域）
            if not scene.is_safe:
                enemy = create_enemy("slime", max(1, self.player.level))
                await self.renderer.draw_message(f"一只{enemy.name}出现了！")
                result = await self.combat_system.start_combat(self.player, enemy)
                await self.handle_combat_result(result)
            else:
                await self.renderer.draw_message("这里没有可以攻击的敌人")
        else:
            # 与NPC战斗
            await self.renderer.draw_message(f"与{enemy_npc.name}开始战斗！")
            # 这里需要将NPC转换为Enemy对象
            # 简化实现
            await self.renderer.draw_message("战斗系统正在开发中...")
    
    async def handle_combat_result(self, result):
        """处理战斗结果"""
        if result.winner == "player":
            await self.renderer.draw_message("你胜利了！")
            for log_entry in result.combat_log[-5:]:  # 显示最后5条日志
                await self.renderer.draw_message(log_entry)
        elif result.winner == "enemy":
            await self.renderer.draw_message("你被击败了...")
            # 复活处理
            self.player.hp = int(self.player.max_hp * 0.1)
            await self.renderer.draw_message("你醒来时发现自己在新手村...")
            self.current_scene = "starting_village"
        elif result.winner == "flee":
            await self.renderer.draw_message("你成功逃脱了！")
    
    async def use_item(self, item_name: str):
        """使用物品"""
        # 查找物品
        item = None
        for inv_item in self.player.inventory:
            if inv_item.name.lower() == item_name.lower() or inv_item.id.lower() == item_name.lower():
                item = inv_item
                break
        
        if not item:
            await self.renderer.draw_message("你没有这个物品")
            return
        
        result = self.player.use_item(item.id)
        await self.renderer.draw_message(result["message"])
    
    async def equip_item(self, item_name: str):
        """装备物品"""
        # 查找物品
        item = None
        for inv_item in self.player.inventory:
            if inv_item.name.lower() == item_name.lower() or inv_item.id.lower() == item_name.lower():
                item = inv_item
                break
        
        if not item:
            await self.renderer.draw_message("你没有这个物品")
            return
        
        if item.item_type not in ['weapon', 'armor', 'accessory']:
            await self.renderer.draw_message("这个物品不能装备")
            return
        
        success = self.player.equip_item(item.id)
        if success:
            await self.renderer.draw_message(f"装备了 {item.name}")
        else:
            await self.renderer.draw_message("装备失败")
    
    async def unequip_item(self, slot: str):
        """脱下装备"""
        valid_slots = ['weapon', 'armor', 'accessory']
        if slot.lower() not in valid_slots:
            await self.renderer.draw_message(f"无效的装备槽位。可用槽位: {', '.join(valid_slots)}")
            return
        
        success = self.player.unequip_item(slot.lower())
        if success:
            await self.renderer.draw_message(f"脱下了 {slot}")
        else:
            await self.renderer.draw_message(f"没有装备 {slot}")
    
    async def save_game(self):
        """保存游戏"""
        try:
            import os
            os.makedirs("saves", exist_ok=True)
            filename = f"saves/{self.player.name}.json"
            
            # 保存当前场景到玩家数据
            self.player.current_scene = self.current_scene
            self.player.save_to_file(filename)
            await self.renderer.draw_message("游戏已保存")
        except Exception as e:
            await self.renderer.draw_message(f"保存失败: {e}")
    
    async def start_character_creation(self):
        """开始角色创建"""
        await self.renderer.draw_message("=== 角色创建 ===")
        await self.renderer.draw_message("请输入你的角色名字:")
    
    async def load_character(self):
        """加载角色"""
        await self.renderer.draw_message("加载功能尚未实现")
    
    async def update(self):
        """更新游戏状态"""
        pass
    
    async def render(self):
        """渲染画面"""
        if self.state == GameState.PLAYING and self.player:
            await self.renderer.draw_game_ui(self.player, self.current_scene)
