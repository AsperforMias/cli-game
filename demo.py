#!/usr/bin/env python3
"""
CLI RPG Game Demo - 快速演示脚本
"""

import asyncio
import time
from ai_service import AIService
from player import Player, Item
from world import World
from npc import create_default_npcs
from ascii_renderer import ASCIIRenderer
from combat import create_enemy, CombatSystem

class DemoChannel:
    """演示用的模拟通道"""
    def __init__(self):
        self.output = []
    
    def write(self, data):
        self.output.append(data)
        print(data, end='')
    
    def set_write_buffer_limits(self, limit):
        pass

async def demo_game_features():
    """演示游戏功能"""
    print("🎮 CLI RPG Game 功能演示")
    print("=" * 50)
    
    # 创建演示环境
    demo_chan = DemoChannel()
    renderer = ASCIIRenderer(demo_chan)
    ai_service = AIService()
    
    print("\n📝 1. 创建角色")
    print("-" * 20)
    player = Player("勇者阿明", "warrior")
    print(f"角色: {player.name}")
    print(f"职业: {player.player_class}")
    print(f"等级: {player.level}")
    print(f"生命值: {player.hp}/{player.max_hp}")
    print(f"攻击力: {player.attack}")
    print(f"防御力: {player.defense}")
    print(f"金钱: {player.money}")
    
    await asyncio.sleep(1)
    
    print("\n🎒 2. 背包系统")
    print("-" * 20)
    
    # 添加一些物品
    items_to_add = [
        Item("health_potion", "生命药水", "恢复50点生命值", "consumable", 3, {"heal": 50}),
        Item("iron_sword", "铁剑", "锋利的铁制剑", "weapon", 1, {"attack": 10}),
        Item("leather_armor", "皮甲", "轻便的皮制护甲", "armor", 1, {"defense": 5})
    ]
    
    for item in items_to_add:
        player.add_item(item)
        print(f"获得物品: {item.name} x{item.quantity}")
    
    print(f"背包物品数: {len(player.inventory)}")
    
    await asyncio.sleep(1)
    
    print("\n⚔️ 3. 装备系统")
    print("-" * 20)
    
    # 装备武器和护甲
    player.equip_item("iron_sword")
    print(f"装备武器: 铁剑")
    print(f"总攻击力: {player.get_total_attack()}")
    
    player.equip_item("leather_armor")
    print(f"装备护甲: 皮甲")
    print(f"总防御力: {player.get_total_defense()}")
    
    await asyncio.sleep(1)
    
    print("\n🌍 4. 世界系统")
    print("-" * 20)
    
    world = World()
    await world.load_data()
    
    print(f"游戏世界包含 {len(world.scenes)} 个场景:")
    for scene_id, scene in world.scenes.items():
        safety = "安全" if scene.is_safe else "危险"
        print(f"  - {scene.name} ({safety})")
    
    await asyncio.sleep(1)
    
    print("\n👥 5. NPC系统")
    print("-" * 20)
    
    npcs = create_default_npcs()
    print(f"创建了 {len(npcs)} 个NPC:")
    
    for npc in npcs.values():
        print(f"  - {npc.name} ({npc.profession})")
        print(f"    {npc.description}")
    
    await asyncio.sleep(1)
    
    print("\n🤖 6. AI对话系统")
    print("-" * 20)
    
    village_elder = npcs["village_elder"]
    
    # 模拟对话
    greeting = await ai_service.get_npc_greeting(village_elder, player)
    print(f"{village_elder.name}: {greeting}")
    
    # 模拟玩家对话
    player_message = "你好，我是新来的冒险者"
    ai_response = await ai_service.process_dialogue(village_elder, player_message, player)
    print(f"{player.name}: {player_message}")
    print(f"{village_elder.name}: {ai_response}")
    
    await asyncio.sleep(1)
    
    print("\n⚔️ 7. 战斗系统")
    print("-" * 20)
    
    enemy = create_enemy("slime", 1)
    print(f"遭遇敌人: {enemy.name}")
    print(f"敌人属性: HP={enemy.hp}, 攻击={enemy.attack}, 防御={enemy.defense}")
    
    # 模拟一轮战斗
    print("\n战斗开始！")
    
    # 玩家攻击
    player_damage = max(1, player.get_total_attack() - enemy.defense)
    enemy.take_damage(player_damage)
    print(f"{player.name} 攻击 {enemy.name}，造成 {player_damage} 点伤害")
    print(f"{enemy.name} 剩余血量: {enemy.hp}")
    
    if enemy.hp > 0:
        # 敌人反击
        enemy_damage = max(1, enemy.attack - player.get_total_defense())
        player.hp -= enemy_damage
        print(f"{enemy.name} 反击，对 {player.name} 造成 {enemy_damage} 点伤害")
        print(f"{player.name} 剩余血量: {player.hp}")
    else:
        print(f"{enemy.name} 被击败！")
        exp_gained = enemy.exp_reward
        money_gained = enemy.money_reward
        player.gain_exp(exp_gained)
        player.money += money_gained
        print(f"获得 {exp_gained} 经验值和 {money_gained} 金币")
    
    await asyncio.sleep(1)
    
    print("\n💊 8. 物品使用")
    print("-" * 20)
    
    if player.hp < player.max_hp:
        old_hp = player.hp
        use_result = player.use_item("health_potion")
        print(f"使用生命药水: {use_result['message']}")
        print(f"生命值: {old_hp} -> {player.hp}")
    
    await asyncio.sleep(1)
    
    print("\n📈 9. 角色成长")
    print("-" * 20)
    
    print(f"当前状态:")
    print(f"  等级: {player.level}")
    print(f"  经验: {player.exp}/{player.exp_needed}")
    print(f"  生命值: {player.hp}/{player.max_hp}")
    print(f"  金钱: {player.money}")
    print(f"  装备: 武器={player.equipment['weapon'].name if player.equipment['weapon'] else '无'}")
    print(f"        护甲={player.equipment['armor'].name if player.equipment['armor'] else '无'}")
    
    await asyncio.sleep(1)
    
    print("\n🎨 10. ASCII渲染")
    print("-" * 20)
    
    # 显示一些ASCII艺术
    await renderer.draw_text("═══ 游戏界面示例 ═══", 0, 0)
    await renderer.draw_health_bar(player.hp, player.max_hp, 0, 1, 20)
    
    # 模拟状态栏
    status_text = f"[{player.name}] Lv.{player.level} | 金币: {player.money}"
    await renderer.draw_text(status_text, 0, 3)
    
    print("\n" + "=" * 50)
    print("🎉 演示完成！")
    print("\n要开始游戏，请运行:")
    print("  python3 main.py")
    print("\n然后在另一个终端连接:")
    print("  ssh -p 2222 player@localhost")
    print("  密码: rpg2025")

async def main():
    """主函数"""
    try:
        await demo_game_features()
    except KeyboardInterrupt:
        print("\n\n演示被中断")
    except Exception as e:
        print(f"\n演示出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
