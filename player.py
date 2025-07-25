"""
Player - 玩家角色系统
管理玩家属性、技能、背包等
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class Item:
    """物品类"""
    id: str
    name: str
    description: str
    item_type: str  # weapon, armor, consumable, misc
    quantity: int = 1
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}

class Player:
    """玩家角色类"""
    
    def __init__(self, name: str, player_class: str):
        self.name = name
        self.player_class = player_class
        self.level = 1
        self.exp = 0
        self.exp_needed = 100
        
        # 根据职业设置初始属性
        self._setup_class_stats()
        
        # 背包系统
        self.inventory = []
        self.max_inventory_size = 20
        
        # 金钱系统
        self.money = 100  # 起始金钱
        
        # 装备系统
        self.equipment = {
            'weapon': None,
            'armor': None,
            'accessory': None
        }
        
        # 技能系统
        self.skills = {}
        self._setup_class_skills()
        
        # 任务系统
        self.quests = {}
        self.completed_quests = []
        
        # 游戏进度
        self.current_scene = "starting_village"
        self.save_data = {}
    
    def _setup_class_stats(self):
        """根据职业设置初始属性"""
        base_stats = {
            'warrior': {
                'hp': 120, 'mp': 30, 'attack': 15, 'defense': 12, 'agility': 8, 'intelligence': 6
            },
            'mage': {
                'hp': 80, 'mp': 120, 'attack': 8, 'defense': 6, 'agility': 10, 'intelligence': 18
            },
            'rogue': {
                'hp': 100, 'mp': 60, 'attack': 12, 'defense': 8, 'agility': 16, 'intelligence': 10
            }
        }
        
        stats = base_stats.get(self.player_class, base_stats['warrior'])
        
        self.hp = stats['hp']
        self.max_hp = stats['hp']
        self.mp = stats['mp']
        self.max_mp = stats['mp']
        self.attack = stats['attack']
        self.defense = stats['defense']
        self.agility = stats['agility']
        self.intelligence = stats['intelligence']
    
    def _setup_class_skills(self):
        """根据职业设置初始技能"""
        class_skills = {
            'warrior': {
                'sword_mastery': {'level': 1, 'exp': 0},
                'shield_block': {'level': 1, 'exp': 0},
                'battle_cry': {'level': 1, 'exp': 0}
            },
            'mage': {
                'fire_magic': {'level': 1, 'exp': 0},
                'ice_magic': {'level': 1, 'exp': 0},
                'mana_regeneration': {'level': 1, 'exp': 0}
            },
            'rogue': {
                'stealth': {'level': 1, 'exp': 0},
                'backstab': {'level': 1, 'exp': 0},
                'lock_picking': {'level': 1, 'exp': 0}
            }
        }
        
        self.skills = class_skills.get(self.player_class, {})
    
    def add_item(self, item: Item) -> bool:
        """添加物品到背包"""
        if len(self.inventory) >= self.max_inventory_size:
            return False
        
        # 检查是否已有相同物品（可堆叠）
        for existing_item in self.inventory:
            if existing_item.id == item.id and existing_item.item_type == 'consumable':
                existing_item.quantity += item.quantity
                return True
        
        # 添加新物品
        self.inventory.append(item)
        return True
    
    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """从背包移除物品"""
        for i, item in enumerate(self.inventory):
            if item.id == item_id:
                if item.quantity > quantity:
                    item.quantity -= quantity
                    return True
                elif item.quantity == quantity:
                    self.inventory.pop(i)
                    return True
                else:
                    return False
        return False
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """根据ID获取物品"""
        for item in self.inventory:
            if item.id == item_id:
                return item
        return None
    
    def equip_item(self, item_id: str) -> bool:
        """装备物品"""
        item = self.get_item(item_id)
        if not item or item.item_type not in ['weapon', 'armor', 'accessory']:
            return False
        
        # 脱下当前装备
        current_equipment = self.equipment.get(item.item_type)
        if current_equipment:
            self.add_item(current_equipment)
        
        # 装备新物品
        self.equipment[item.item_type] = item
        self.remove_item(item_id, 1)
        
        # 应用装备属性
        self._apply_equipment_stats()
        return True
    
    def unequip_item(self, slot: str) -> bool:
        """脱下装备"""
        if slot not in self.equipment or not self.equipment[slot]:
            return False
        
        item = self.equipment[slot]
        if not self.add_item(item):
            return False
        
        self.equipment[slot] = None
        self._apply_equipment_stats()
        return True
    
    def _apply_equipment_stats(self):
        """应用装备属性加成"""
        # 重置为基础属性
        self._setup_class_stats()
        
        # 应用装备加成
        for equipment in self.equipment.values():
            if equipment and equipment.properties:
                for stat, value in equipment.properties.items():
                    if hasattr(self, stat):
                        setattr(self, stat, getattr(self, stat) + value)
    
    def gain_exp(self, amount: int):
        """获得经验值"""
        self.exp += amount
        
        # 检查升级
        while self.exp >= self.exp_needed:
            self.level_up()
    
    def level_up(self):
        """升级"""
        self.exp -= self.exp_needed
        self.level += 1
        self.exp_needed = int(self.exp_needed * 1.2)
        
        # 属性提升
        stat_gains = self._get_level_up_stats()
        for stat, gain in stat_gains.items():
            if hasattr(self, stat):
                setattr(self, stat, getattr(self, stat) + gain)
        
        # 恢复生命值和魔法值
        self.hp = self.max_hp
        self.mp = self.max_mp
    
    def _get_level_up_stats(self) -> Dict[str, int]:
        """获取升级时的属性提升"""
        class_gains = {
            'warrior': {
                'max_hp': 15, 'max_mp': 3, 'attack': 2, 'defense': 2, 'agility': 1, 'intelligence': 1
            },
            'mage': {
                'max_hp': 8, 'max_mp': 15, 'attack': 1, 'defense': 1, 'agility': 1, 'intelligence': 3
            },
            'rogue': {
                'max_hp': 12, 'max_mp': 8, 'attack': 2, 'defense': 1, 'agility': 3, 'intelligence': 1
            }
        }
        
        return class_gains.get(self.player_class, class_gains['warrior'])
    
    def use_item(self, item_id: str) -> Dict[str, Any]:
        """使用物品"""
        item = self.get_item(item_id)
        if not item or item.item_type != 'consumable':
            return {'success': False, 'message': '无法使用该物品'}
        
        # 处理不同类型的消耗品
        if item.id == 'health_potion':
            heal_amount = item.properties.get('heal', 50)
            old_hp = self.hp
            self.hp = min(self.max_hp, self.hp + heal_amount)
            actual_heal = self.hp - old_hp
            
            self.remove_item(item_id, 1)
            return {
                'success': True, 
                'message': f'恢复了 {actual_heal} 点生命值',
                'heal': actual_heal
            }
        
        elif item.id == 'mana_potion':
            mana_amount = item.properties.get('mana', 30)
            old_mp = self.mp
            self.mp = min(self.max_mp, self.mp + mana_amount)
            actual_mana = self.mp - old_mp
            
            self.remove_item(item_id, 1)
            return {
                'success': True,
                'message': f'恢复了 {actual_mana} 点魔法值',
                'mana': actual_mana
            }
        
        return {'success': False, 'message': '未知的物品效果'}
    
    def learn_skill(self, skill_name: str) -> bool:
        """学习技能"""
        if skill_name not in self.skills:
            self.skills[skill_name] = {'level': 1, 'exp': 0}
            return True
        return False
    
    def use_skill(self, skill_name: str) -> Dict[str, Any]:
        """使用技能"""
        if skill_name not in self.skills:
            return {'success': False, 'message': '你没有学会这个技能'}
        
        skill = self.skills[skill_name]
        
        # 检查MP消耗
        mp_cost = self._get_skill_mp_cost(skill_name, skill['level'])
        if self.mp < mp_cost:
            return {'success': False, 'message': '魔法值不足'}
        
        self.mp -= mp_cost
        
        # 计算技能效果
        effect = self._calculate_skill_effect(skill_name, skill['level'])
        
        # 增加技能经验
        skill['exp'] += 1
        if skill['exp'] >= skill['level'] * 10:
            skill['level'] += 1
            skill['exp'] = 0
            effect['level_up'] = True
        
        return effect
    
    def _get_skill_mp_cost(self, skill_name: str, level: int) -> int:
        """获取技能MP消耗"""
        base_costs = {
            'fire_magic': 15,
            'ice_magic': 15,
            'battle_cry': 10,
            'stealth': 20,
            'backstab': 25
        }
        
        base_cost = base_costs.get(skill_name, 10)
        return max(1, base_cost - level)
    
    def _calculate_skill_effect(self, skill_name: str, level: int) -> Dict[str, Any]:
        """计算技能效果"""
        effects = {
            'fire_magic': {
                'type': 'damage',
                'damage': 20 + level * 5,
                'message': f'释放火球术，造成伤害'
            },
            'ice_magic': {
                'type': 'damage',
                'damage': 15 + level * 4,
                'message': f'释放冰锥术，造成伤害并降低敌人速度'
            },
            'battle_cry': {
                'type': 'buff',
                'attack_boost': level * 2,
                'message': f'发出战吼，提升攻击力'
            }
        }
        
        effect = effects.get(skill_name, {'type': 'none', 'message': '技能效果未实现'})
        effect['success'] = True
        return effect
    
    def add_quest(self, quest_id: str, quest_data: Dict[str, Any]):
        """接受任务"""
        self.quests[quest_id] = quest_data
    
    def complete_quest(self, quest_id: str) -> bool:
        """完成任务"""
        if quest_id in self.quests:
            quest = self.quests.pop(quest_id)
            self.completed_quests.append(quest_id)
            
            # 给予奖励
            if 'rewards' in quest:
                rewards = quest['rewards']
                if 'exp' in rewards:
                    self.gain_exp(rewards['exp'])
                if 'items' in rewards:
                    for item_data in rewards['items']:
                        item = Item(**item_data)
                        self.add_item(item)
            
            return True
        return False
    
    def get_total_attack(self) -> int:
        """获取总攻击力（包括装备加成）"""
        total_attack = self.attack
        weapon = self.equipment.get('weapon')
        if weapon and weapon.properties:
            total_attack += weapon.properties.get('attack', 0)
        return total_attack
    
    def get_total_defense(self) -> int:
        """获取总防御力（包括装备加成）"""
        total_defense = self.defense
        armor = self.equipment.get('armor')
        if armor and armor.properties:
            total_defense += armor.properties.get('defense', 0)
        return total_defense
    
    def save_to_file(self, filename: str):
        """保存角色到文件"""
        save_data = {
            'name': self.name,
            'player_class': self.player_class,
            'level': self.level,
            'exp': self.exp,
            'exp_needed': self.exp_needed,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'mp': self.mp,
            'max_mp': self.max_mp,
            'attack': self.attack,
            'defense': self.defense,
            'agility': self.agility,
            'intelligence': self.intelligence,
            'inventory': [asdict(item) for item in self.inventory],
            'equipment': {k: asdict(v) if v else None for k, v in self.equipment.items()},
            'skills': self.skills,
            'quests': self.quests,
            'completed_quests': self.completed_quests,
            'current_scene': self.current_scene,
            'save_data': self.save_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'Player':
        """从文件加载角色"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        player = cls(data['name'], data['player_class'])
        
        # 恢复属性
        for key, value in data.items():
            if key == 'inventory':
                player.inventory = [Item(**item_data) for item_data in value]
            elif key == 'equipment':
                player.equipment = {
                    k: Item(**v) if v else None 
                    for k, v in value.items()
                }
            else:
                setattr(player, key, value)
        
        return player
    
    def __str__(self) -> str:
        return f"{self.name} (Lv.{self.level} {self.player_class})"
