"""
Combat System - 战斗系统
处理玩家与敌人的战斗逻辑
"""

import random
import asyncio
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

class CombatAction(Enum):
    """战斗行动类型"""
    ATTACK = "attack"
    DEFEND = "defend"
    USE_SKILL = "use_skill"
    USE_ITEM = "use_item"
    FLEE = "flee"

@dataclass
class CombatResult:
    """战斗结果"""
    winner: str  # "player" or "enemy"
    exp_gained: int
    items_gained: List[Dict]
    money_gained: int
    combat_log: List[str]

class Enemy:
    """敌人类"""
    
    def __init__(self, enemy_id: str, name: str, level: int = 1):
        self.id = enemy_id
        self.name = name
        self.level = level
        
        # 基础属性
        self.max_hp = 50 + (level - 1) * 20
        self.hp = self.max_hp
        self.attack = 8 + (level - 1) * 3
        self.defense = 3 + (level - 1) * 2
        self.agility = 5 + (level - 1) * 1
        
        # 奖励
        self.exp_reward = 25 * level
        self.money_reward = 10 * level
        self.loot_table = []
        
        # AI类型
        self.ai_type = "normal"  # normal, aggressive, defensive, smart
        
        # 技能
        self.skills = []
        
    def take_damage(self, damage: int) -> int:
        """受到伤害"""
        actual_damage = max(1, damage - self.defense)
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage
    
    def is_alive(self) -> bool:
        """是否存活"""
        return self.hp > 0
    
    def get_attack_damage(self) -> int:
        """获取攻击伤害"""
        base_damage = self.attack
        # 添加随机因素
        variance = int(base_damage * 0.2)
        return random.randint(base_damage - variance, base_damage + variance)
    
    def choose_action(self, player) -> Dict[str, Any]:
        """AI选择行动"""
        if self.ai_type == "aggressive":
            return {"action": CombatAction.ATTACK}
        
        elif self.ai_type == "defensive":
            if self.hp < self.max_hp * 0.3:
                # 血量低时可能逃跑
                if random.random() < 0.3:
                    return {"action": CombatAction.FLEE}
                else:
                    return {"action": CombatAction.DEFEND}
            else:
                return {"action": CombatAction.ATTACK}
        
        elif self.ai_type == "smart":
            # 智能AI会根据情况选择行动
            if self.hp < self.max_hp * 0.2 and random.random() < 0.4:
                return {"action": CombatAction.FLEE}
            elif player.hp < player.max_hp * 0.3:
                # 玩家血量低时主动攻击
                return {"action": CombatAction.ATTACK}
            elif self.hp < self.max_hp * 0.5 and random.random() < 0.3:
                return {"action": CombatAction.DEFEND}
            else:
                return {"action": CombatAction.ATTACK}
        
        else:  # normal
            actions = [CombatAction.ATTACK, CombatAction.ATTACK, CombatAction.DEFEND]
            return {"action": random.choice(actions)}

class CombatSystem:
    """战斗系统类"""
    
    def __init__(self, renderer):
        self.renderer = renderer
        self.combat_log = []
        self.turn_count = 0
        
    async def start_combat(self, player, enemy) -> CombatResult:
        """开始战斗"""
        self.combat_log = []
        self.turn_count = 0
        
        self.log(f"战斗开始！{player.name} vs {enemy.name}")
        
        while player.hp > 0 and enemy.hp > 0:
            self.turn_count += 1
            
            # 渲染战斗界面
            await self.renderer.draw_combat_ui(player, enemy)
            await self.renderer.draw_message(f"\n第{self.turn_count}回合")
            
            # 玩家回合
            player_action = await self.get_player_action(player, enemy)
            if player_action["action"] == CombatAction.FLEE:
                flee_success = await self.attempt_flee(player, enemy)
                if flee_success:
                    self.log(f"{player.name} 成功逃脱了！")
                    return CombatResult("flee", 0, [], 0, self.combat_log)
                else:
                    self.log(f"{player.name} 逃跑失败！")
            else:
                await self.execute_player_action(player, enemy, player_action)
            
            # 检查敌人是否死亡
            if not enemy.is_alive():
                break
            
            # 敌人回合
            enemy_action = enemy.choose_action(player)
            await self.execute_enemy_action(player, enemy, enemy_action)
            
            # 检查玩家是否死亡
            if player.hp <= 0:
                break
            
            # 短暂延迟
            await asyncio.sleep(1)
        
        # 结算战斗结果
        return await self.resolve_combat(player, enemy)
    
    async def get_player_action(self, player, enemy) -> Dict[str, Any]:
        """获取玩家行动"""
        await self.renderer.draw_message("\n你的行动:")
        await self.renderer.draw_message("1. 攻击")
        await self.renderer.draw_message("2. 防御")
        await self.renderer.draw_message("3. 使用技能")
        await self.renderer.draw_message("4. 使用物品")
        await self.renderer.draw_message("5. 逃跑")
        
        # 这里应该等待玩家输入，为了简化，我们随机选择
        # 在实际实现中，需要与游戏引擎的输入系统集成
        choice = random.randint(1, 5)
        
        if choice == 1:
            return {"action": CombatAction.ATTACK}
        elif choice == 2:
            return {"action": CombatAction.DEFEND}
        elif choice == 3:
            # 选择技能
            available_skills = [skill for skill in player.skills.keys()]
            if available_skills:
                skill = random.choice(available_skills)
                return {"action": CombatAction.USE_SKILL, "skill": skill}
            else:
                return {"action": CombatAction.ATTACK}
        elif choice == 4:
            # 使用物品
            consumables = [item for item in player.inventory if item.item_type == "consumable"]
            if consumables:
                item = random.choice(consumables)
                return {"action": CombatAction.USE_ITEM, "item": item.id}
            else:
                return {"action": CombatAction.ATTACK}
        else:
            return {"action": CombatAction.FLEE}
    
    async def execute_player_action(self, player, enemy, action: Dict[str, Any]):
        """执行玩家行动"""
        action_type = action["action"]
        
        if action_type == CombatAction.ATTACK:
            damage = self.calculate_damage(player.get_total_attack(), enemy.defense)
            actual_damage = enemy.take_damage(damage)
            self.log(f"{player.name} 攻击 {enemy.name}，造成 {actual_damage} 点伤害")
            
        elif action_type == CombatAction.DEFEND:
            # 防御减少下次受到的伤害
            player.defending = True
            self.log(f"{player.name} 进入防御姿态")
            
        elif action_type == CombatAction.USE_SKILL:
            skill_name = action.get("skill")
            if skill_name:
                result = player.use_skill(skill_name)
                if result["success"]:
                    self.log(f"{player.name} 使用了 {skill_name}")
                    
                    # 处理技能效果
                    if "damage" in result:
                        damage = result["damage"]
                        actual_damage = enemy.take_damage(damage)
                        self.log(f"对 {enemy.name} 造成 {actual_damage} 点伤害")
                    
                    if "heal" in result:
                        heal = result["heal"]
                        player.hp = min(player.max_hp, player.hp + heal)
                        self.log(f"{player.name} 恢复了 {heal} 点生命值")
                else:
                    self.log(result["message"])
            
        elif action_type == CombatAction.USE_ITEM:
            item_id = action.get("item")
            if item_id:
                result = player.use_item(item_id)
                if result["success"]:
                    self.log(f"{player.name} 使用了物品")
                    self.log(result["message"])
                else:
                    self.log(result["message"])
    
    async def execute_enemy_action(self, player, enemy, action: Dict[str, Any]):
        """执行敌人行动"""
        action_type = action["action"]
        
        if action_type == CombatAction.ATTACK:
            damage = self.calculate_damage(enemy.get_attack_damage(), player.get_total_defense())
            
            # 如果玩家在防御，减少伤害
            if hasattr(player, 'defending') and player.defending:
                damage = int(damage * 0.5)
                player.defending = False
                self.log(f"{player.name} 的防御减少了伤害")
            
            actual_damage = max(1, damage)
            player.hp = max(0, player.hp - actual_damage)
            self.log(f"{enemy.name} 攻击 {player.name}，造成 {actual_damage} 点伤害")
            
        elif action_type == CombatAction.DEFEND:
            self.log(f"{enemy.name} 进入防御姿态")
            enemy.defending = True
            
        elif action_type == CombatAction.FLEE:
            flee_success = random.random() < 0.3  # 30%逃跑成功率
            if flee_success:
                self.log(f"{enemy.name} 逃跑了！")
                enemy.hp = 0  # 标记为"死亡"以结束战斗
            else:
                self.log(f"{enemy.name} 逃跑失败！")
    
    def calculate_damage(self, attack: int, defense: int) -> int:
        """计算伤害"""
        base_damage = max(1, attack - defense)
        # 添加随机因素
        variance = int(base_damage * 0.1)
        return random.randint(max(1, base_damage - variance), base_damage + variance)
    
    async def attempt_flee(self, player, enemy) -> bool:
        """尝试逃跑"""
        # 基于敏捷计算逃跑成功率
        player_agility = player.agility
        enemy_agility = enemy.agility
        
        flee_chance = 0.5 + (player_agility - enemy_agility) * 0.02
        flee_chance = max(0.1, min(0.9, flee_chance))  # 限制在10%-90%之间
        
        return random.random() < flee_chance
    
    async def resolve_combat(self, player, enemy) -> CombatResult:
        """结算战斗结果"""
        if player.hp <= 0:
            self.log(f"{player.name} 被击败了！")
            return CombatResult("enemy", 0, [], 0, self.combat_log)
        
        elif not enemy.is_alive():
            self.log(f"{enemy.name} 被击败了！")
            
            # 给予奖励
            exp_gained = enemy.exp_reward
            money_gained = enemy.money_reward
            items_gained = self.generate_loot(enemy)
            
            player.gain_exp(exp_gained)
            if not hasattr(player, 'money'):
                player.money = 0
            player.money += money_gained
            
            for item_data in items_gained:
                from player import Item
                item = Item(**item_data)
                player.add_item(item)
            
            self.log(f"获得 {exp_gained} 经验值")
            self.log(f"获得 {money_gained} 金币")
            
            if items_gained:
                self.log("获得物品:")
                for item in items_gained:
                    self.log(f"  - {item['name']}")
            
            return CombatResult("player", exp_gained, items_gained, money_gained, self.combat_log)
        
        return CombatResult("draw", 0, [], 0, self.combat_log)
    
    def generate_loot(self, enemy) -> List[Dict]:
        """生成战利品"""
        loot = []
        
        # 基础战利品表
        common_loot = [
            {"id": "slime_gel", "name": "史莱姆凝胶", "description": "粘性物质", 
             "item_type": "misc", "base_price": 5, "properties": {}},
        ]
        
        # 根据敌人等级和类型决定掉落
        if enemy.id == "slime":
            if random.random() < 0.7:  # 70%几率掉落
                loot.append(common_loot[0])
        
        # 稀有掉落
        if random.random() < 0.1:  # 10%几率掉落药水
            loot.append({
                "id": "health_potion", "name": "生命药水", "description": "恢复50点生命值", 
                "item_type": "consumable", "base_price": 25, "properties": {"heal": 50}
            })
        
        return loot
    
    def log(self, message: str):
        """记录战斗日志"""
        self.combat_log.append(message)

def create_enemy(enemy_type: str, level: int = 1) -> Enemy:
    """创建敌人"""
    enemies = {
        "slime": {
            "name": "史莱姆",
            "hp_base": 30,
            "attack_base": 5,
            "defense_base": 2,
            "ai_type": "normal"
        },
        "goblin": {
            "name": "哥布林",
            "hp_base": 50,
            "attack_base": 8,
            "defense_base": 3,
            "ai_type": "aggressive"
        },
        "orc": {
            "name": "兽人",
            "hp_base": 80,
            "attack_base": 12,
            "defense_base": 5,
            "ai_type": "smart"
        }
    }
    
    if enemy_type not in enemies:
        enemy_type = "slime"
    
    enemy_data = enemies[enemy_type]
    enemy = Enemy(enemy_type, enemy_data["name"], level)
    
    # 调整属性
    enemy.max_hp = enemy_data["hp_base"] + (level - 1) * 15
    enemy.hp = enemy.max_hp
    enemy.attack = enemy_data["attack_base"] + (level - 1) * 2
    enemy.defense = enemy_data["defense_base"] + (level - 1) * 1
    enemy.ai_type = enemy_data["ai_type"]
    
    return enemy
