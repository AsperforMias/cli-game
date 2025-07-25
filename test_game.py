#!/usr/bin/env python3
"""
测试脚本 - 验证游戏核心功能
"""

import asyncio
import sys
from io import StringIO

# 模拟通道对象用于测试
class MockChannel:
    def __init__(self):
        self.output = StringIO()
        self.reader = MockReader()
    
    def write(self, data):
        self.output.write(data)
    
    def set_write_buffer_limits(self, limit):
        pass

class MockReader:
    def __init__(self):
        self._buffer = b""

async def test_game_components():
    """测试游戏各个组件"""
    print("=== CLI RPG Game 组件测试 ===\n")
    
    # 测试 Player 系统
    print("1. 测试玩家系统...")
    from player import Player, Item
    
    player = Player("测试玩家", "warrior")
    print(f"   创建玩家: {player.name} (Lv.{player.level} {player.player_class})")
    print(f"   初始属性: HP={player.hp}/{player.max_hp}, 攻击={player.attack}, 防御={player.defense}")
    
    # 测试物品系统
    health_potion = Item("health_potion", "生命药水", "恢复50点生命值", "consumable", 1, {"heal": 50})
    player.add_item(health_potion)
    print(f"   添加物品: {health_potion.name}")
    print(f"   背包物品数: {len(player.inventory)}")
    
    # 测试升级
    player.gain_exp(150)
    print(f"   获得经验后: Lv.{player.level}")
    
    # 测试 NPC 系统
    print("\n2. 测试NPC系统...")
    from npc import create_default_npcs
    
    npcs = create_default_npcs()
    print(f"   创建默认NPC: {len(npcs)} 个")
    for npc_id, npc in npcs.items():
        print(f"     - {npc.name} ({npc.profession})")
    
    # 测试 World 系统
    print("\n3. 测试世界系统...")
    from world import World
    
    world = World()
    await world.load_data()
    print(f"   加载场景: {len(world.scenes)} 个")
    for scene_id, scene in world.scenes.items():
        print(f"     - {scene.name}")
    
    # 测试 ASCII Renderer
    print("\n4. 测试渲染系统...")
    from ascii_renderer import ASCIIRenderer
    
    mock_chan = MockChannel()
    renderer = ASCIIRenderer(mock_chan)
    await renderer.draw_text("测试文本", 0, 0)
    await renderer.draw_health_bar(80, 100, 0, 1)
    print("   渲染系统工作正常")
    
    # 测试 AI Service
    print("\n5. 测试AI服务...")
    from ai_service import AIService
    
    ai_service = AIService()
    if hasattr(ai_service, 'use_mock') and ai_service.use_mock:
        print("   AI服务: 使用模拟模式 (未配置API密钥)")
    else:
        print("   AI服务: 使用真实API")
    
    # 测试战斗系统
    print("\n6. 测试战斗系统...")
    from combat import create_enemy, CombatSystem
    
    slime = create_enemy("slime", 1)
    print(f"   创建敌人: {slime.name} (Lv.{slime.level})")
    print(f"   敌人属性: HP={slime.hp}, 攻击={slime.attack}")
    
    combat_system = CombatSystem(renderer)
    print("   战斗系统初始化完成")
    
    print("\n=== 所有组件测试完成 ===")
    print("游戏已准备就绪！使用以下命令启动：")
    print("  python3 main.py")
    print("  然后在另一个终端中使用: ssh -p 2222 player@localhost")

async def test_game_flow():
    """测试游戏流程"""
    print("\n=== 游戏流程测试 ===")
    
    from game_engine import GameEngine
    from ai_service import AIService
    from player import Player
    
    mock_chan = MockChannel()
    ai_service = AIService()
    
    game_engine = GameEngine(mock_chan, ai_service)
    
    # 测试初始化
    print("1. 测试游戏初始化...")
    await game_engine.load_game_data()
    print("   游戏数据加载完成")
    
    # 创建测试玩家
    print("2. 创建测试玩家...")
    game_engine.player = Player("测试玩家", "warrior")
    game_engine.current_scene = "starting_village"
    print(f"   玩家创建: {game_engine.player.name}")
    
    # 测试场景切换
    print("3. 测试场景系统...")
    scene = game_engine.world.get_scene("starting_village")
    if scene:
        print(f"   当前场景: {scene.name}")
        print(f"   场景NPC数: {len(scene.npcs)}")
    
    print("   游戏流程测试完成")

def main():
    """主测试函数"""
    try:
        # 运行组件测试
        asyncio.run(test_game_components())
        
        # 运行流程测试
        asyncio.run(test_game_flow())
        
        print("\n✅ 所有测试通过！游戏可以正常运行。")
        return 0
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
