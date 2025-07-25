"""
NPC - 非玩家角色系统
管理NPC的属性、对话、AI行为等
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class NPCType(Enum):
    """NPC类型枚举"""
    MERCHANT = "merchant"
    QUEST_GIVER = "quest_giver"
    GUARD = "guard"
    VILLAGER = "villager"
    ENEMY = "enemy"
    TRAINER = "trainer"

@dataclass
class DialogueOption:
    """对话选项"""
    text: str
    response: str
    conditions: Dict[str, Any] = None
    actions: List[Dict[str, Any]] = None

class NPC:
    """NPC基类"""
    
    def __init__(self, npc_id: str, name: str, npc_type: NPCType):
        self.id = npc_id
        self.name = name
        self.npc_type = npc_type
        self.description = ""
        self.profession = ""
        self.personality = ""
        self.background = ""
        
        # 位置信息
        self.scene_id = ""
        self.position = (0, 0)
        
        # 对话系统
        self.dialogue_tree = {}
        self.current_dialogue_state = "greeting"
        
        # AI相关
        self.mood = 0.5  # 0-1之间，影响对话态度
        self.memory = {}  # 记住与玩家的对话
        self.relationship = {}  # 与不同玩家的关系
        
        # 商店系统（如果是商人）
        self.shop_items = []
        self.shop_money = 1000
        
        # 任务系统（如果是任务发布者）
        self.available_quests = []
        self.completed_quests = []
        
        # 战斗相关（如果是敌人）
        self.is_hostile = False
        self.hp = 100
        self.max_hp = 100
        self.attack = 10
        self.defense = 5
        self.exp_reward = 50
        self.loot_table = []
    
    def set_basic_info(self, description: str, profession: str, personality: str, background: str):
        """设置基本信息"""
        self.description = description
        self.profession = profession
        self.personality = personality
        self.background = background
    
    def add_dialogue_option(self, state: str, option: DialogueOption):
        """添加对话选项"""
        if state not in self.dialogue_tree:
            self.dialogue_tree[state] = []
        self.dialogue_tree[state].append(option)
    
    def get_greeting(self, player) -> str:
        """获取问候语"""
        player_relationship = self.relationship.get(player.name, 0.5)
        
        if player_relationship > 0.8:
            greetings = [
                f"你好，我的朋友{player.name}！",
                f"很高兴再次见到你，{player.name}！",
                f"欢迎回来，{player.name}！"
            ]
        elif player_relationship > 0.5:
            greetings = [
                f"你好，{player.name}。",
                f"嗨，{player.name}，有什么需要帮助的吗？",
                f"又见面了，{player.name}。"
            ]
        else:
            greetings = [
                "你是谁？",
                "陌生人，有什么事吗？",
                "我不认识你。"
            ]
        
        import random
        return random.choice(greetings)
    
    def update_relationship(self, player_name: str, change: float):
        """更新与玩家的关系"""
        current = self.relationship.get(player_name, 0.5)
        self.relationship[player_name] = max(0, min(1, current + change))
    
    def remember_interaction(self, player_name: str, interaction: str):
        """记住与玩家的互动"""
        if player_name not in self.memory:
            self.memory[player_name] = []
        
        self.memory[player_name].append({
            'interaction': interaction,
            'timestamp': None  # 可以添加时间戳
        })
        
        # 限制记忆长度
        if len(self.memory[player_name]) > 10:
            self.memory[player_name] = self.memory[player_name][-10:]
    
    def can_give_quest(self, quest_id: str, player) -> bool:
        """检查是否可以给予任务"""
        if quest_id not in self.available_quests:
            return False
        
        quest = self.available_quests[quest_id]
        
        # 检查前置条件
        if 'requirements' in quest:
            requirements = quest['requirements']
            
            if 'level' in requirements and player.level < requirements['level']:
                return False
            
            if 'completed_quests' in requirements:
                for req_quest in requirements['completed_quests']:
                    if req_quest not in player.completed_quests:
                        return False
        
        return True
    
    def give_quest(self, quest_id: str, player) -> bool:
        """给予任务"""
        if not self.can_give_quest(quest_id, player):
            return False
        
        quest = self.available_quests[quest_id]
        player.add_quest(quest_id, quest)
        return True

class MerchantNPC(NPC):
    """商人NPC"""
    
    def __init__(self, npc_id: str, name: str):
        super().__init__(npc_id, name, NPCType.MERCHANT)
        self.shop_items = []
        self.shop_money = 1000
        self.buy_rate = 0.5  # 收购价格比例
        self.sell_rate = 1.2  # 销售价格比例
    
    def add_shop_item(self, item_data: Dict[str, Any], price: int, stock: int = -1):
        """添加商店物品"""
        shop_item = {
            'item': item_data,
            'price': price,
            'stock': stock,  # -1表示无限库存
            'original_stock': stock
        }
        self.shop_items.append(shop_item)
    
    def can_buy_item(self, item_index: int, quantity: int = 1) -> bool:
        """检查是否可以购买物品"""
        if item_index >= len(self.shop_items):
            return False
        
        item = self.shop_items[item_index]
        if item['stock'] != -1 and item['stock'] < quantity:
            return False
        
        return True
    
    def buy_item(self, item_index: int, player, quantity: int = 1) -> Dict[str, Any]:
        """购买物品"""
        if not self.can_buy_item(item_index, quantity):
            return {'success': False, 'message': '库存不足'}
        
        item = self.shop_items[item_index]
        total_price = item['price'] * quantity
        
        # 检查玩家金钱（需要在player类中添加money属性）
        if not hasattr(player, 'money') or player.money < total_price:
            return {'success': False, 'message': '金钱不足'}
        
        # 检查背包空间
        from player import Item
        game_item = Item(**item['item'])
        game_item.quantity = quantity
        
        if not player.add_item(game_item):
            return {'success': False, 'message': '背包已满'}
        
        # 完成交易
        player.money -= total_price
        self.shop_money += total_price
        
        if item['stock'] != -1:
            item['stock'] -= quantity
        
        return {
            'success': True,
            'message': f'购买了 {quantity} 个 {item["item"]["name"]}',
            'cost': total_price
        }
    
    def sell_item(self, player, item_id: str, quantity: int = 1) -> Dict[str, Any]:
        """出售物品给商人"""
        player_item = player.get_item(item_id)
        if not player_item or player_item.quantity < quantity:
            return {'success': False, 'message': '物品不足'}
        
        # 计算价格（基于物品的基础价格）
        base_price = getattr(player_item, 'base_price', 10)
        sell_price = int(base_price * self.buy_rate * quantity)
        
        if self.shop_money < sell_price:
            return {'success': False, 'message': '商人金钱不足'}
        
        # 完成交易
        player.remove_item(item_id, quantity)
        if not hasattr(player, 'money'):
            player.money = 0
        player.money += sell_price
        self.shop_money -= sell_price
        
        return {
            'success': True,
            'message': f'出售了 {quantity} 个 {player_item.name}',
            'earned': sell_price
        }

class QuestGiverNPC(NPC):
    """任务发布者NPC"""
    
    def __init__(self, npc_id: str, name: str):
        super().__init__(npc_id, name, NPCType.QUEST_GIVER)
        self.available_quests = {}
    
    def add_quest(self, quest_data: Dict[str, Any]):
        """添加可发布的任务"""
        quest_id = quest_data['id']
        self.available_quests[quest_id] = quest_data
    
    def get_available_quests(self, player) -> List[Dict[str, Any]]:
        """获取玩家可接受的任务"""
        available = []
        for quest_id, quest in self.available_quests.items():
            if self.can_give_quest(quest_id, player):
                available.append(quest)
        return available

class EnemyNPC(NPC):
    """敌人NPC"""
    
    def __init__(self, npc_id: str, name: str):
        super().__init__(npc_id, name, NPCType.ENEMY)
        self.is_hostile = True
        self.ai_type = "aggressive"  # aggressive, defensive, smart
        self.skills = []
    
    def take_damage(self, damage: int) -> bool:
        """受到伤害"""
        self.hp = max(0, self.hp - damage)
        return self.hp <= 0
    
    def attack_player(self, player) -> Dict[str, Any]:
        """攻击玩家"""
        damage = max(1, self.attack - player.get_total_defense())
        player.hp = max(0, player.hp - damage)
        
        return {
            'damage': damage,
            'message': f'{self.name} 攻击了你，造成 {damage} 点伤害'
        }
    
    def get_ai_action(self, player) -> str:
        """获取AI行动"""
        if self.ai_type == "aggressive":
            return "attack"
        elif self.ai_type == "defensive":
            return "defend" if self.hp < self.max_hp * 0.3 else "attack"
        elif self.ai_type == "smart":
            # 智能AI可以根据情况选择行动
            if self.hp < self.max_hp * 0.2:
                return "flee"
            elif player.hp < player.max_hp * 0.3:
                return "attack"
            else:
                return "attack"
        
        return "attack"

def load_npcs_from_file(filename: str) -> Dict[str, NPC]:
    """从文件加载NPC数据"""
    npcs = {}
    
    if not os.path.exists(filename):
        return npcs
    
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for npc_data in data:
        npc_type = NPCType(npc_data['type'])
        
        if npc_type == NPCType.MERCHANT:
            npc = MerchantNPC(npc_data['id'], npc_data['name'])
            if 'shop_items' in npc_data:
                for item_data in npc_data['shop_items']:
                    npc.add_shop_item(item_data['item'], item_data['price'], item_data.get('stock', -1))
        
        elif npc_type == NPCType.QUEST_GIVER:
            npc = QuestGiverNPC(npc_data['id'], npc_data['name'])
            if 'quests' in npc_data:
                for quest in npc_data['quests']:
                    npc.add_quest(quest)
        
        elif npc_type == NPCType.ENEMY:
            npc = EnemyNPC(npc_data['id'], npc_data['name'])
            if 'combat_stats' in npc_data:
                stats = npc_data['combat_stats']
                npc.hp = npc.max_hp = stats.get('hp', 100)
                npc.attack = stats.get('attack', 10)
                npc.defense = stats.get('defense', 5)
        
        else:
            npc = NPC(npc_data['id'], npc_data['name'], npc_type)
        
        # 设置基本信息
        npc.set_basic_info(
            npc_data.get('description', ''),
            npc_data.get('profession', ''),
            npc_data.get('personality', ''),
            npc_data.get('background', '')
        )
        
        # 设置对话
        if 'dialogues' in npc_data:
            for state, options in npc_data['dialogues'].items():
                for option_data in options:
                    option = DialogueOption(
                        text=option_data['text'],
                        response=option_data['response'],
                        conditions=option_data.get('conditions'),
                        actions=option_data.get('actions')
                    )
                    npc.add_dialogue_option(state, option)
        
        npcs[npc.id] = npc
    
    return npcs

def create_default_npcs() -> Dict[str, NPC]:
    """创建一些默认的NPC"""
    npcs = {}
    
    # 村长 - 任务发布者
    village_elder = QuestGiverNPC("village_elder", "村长老威廉")
    village_elder.set_basic_info(
        description="一位慈祥的老人，是村子的领导者",
        profession="村长",
        personality="智慧、慈祥、负责任",
        background="在这个村子生活了一辈子，见证了许多冒险者的成长"
    )
    
    # 添加新手任务
    starter_quest = {
        'id': 'kill_slimes',
        'name': '清理史莱姆',
        'description': '村子附近出现了一些史莱姆，请帮忙清理5只',
        'objectives': [
            {'type': 'kill', 'target': 'slime', 'count': 5, 'current': 0}
        ],
        'rewards': {
            'exp': 100,
            'money': 50,
            'items': [
                {'id': 'health_potion', 'name': '生命药水', 'description': '恢复50点生命值', 
                 'item_type': 'consumable', 'properties': {'heal': 50}}
            ]
        },
        'requirements': {'level': 1}
    }
    village_elder.add_quest(starter_quest)
    npcs[village_elder.id] = village_elder
    
    # 铁匠 - 商人
    blacksmith = MerchantNPC("blacksmith_tom", "铁匠汤姆")
    blacksmith.set_basic_info(
        description="一位强壮的铁匠，能够制作和修理各种装备",
        profession="铁匠",
        personality="直爽、热情、技艺精湛",
        background="从父亲那里继承了精湛的锻造技艺"
    )
    
    # 添加商品
    blacksmith.add_shop_item(
        {'id': 'iron_sword', 'name': '铁剑', 'description': '锋利的铁制剑', 
         'item_type': 'weapon', 'properties': {'attack': 10}}, 
        100, 5
    )
    blacksmith.add_shop_item(
        {'id': 'leather_armor', 'name': '皮甲', 'description': '轻便的皮制护甲', 
         'item_type': 'armor', 'properties': {'defense': 5}}, 
        80, 3
    )
    npcs[blacksmith.id] = blacksmith
    
    # 药剂师 - 商人
    alchemist = MerchantNPC("alchemist_mary", "药剂师玛丽")
    alchemist.set_basic_info(
        description="一位聪明的药剂师，精通各种药水的制作",
        profession="药剂师",
        personality="聪明、细心、神秘",
        background="年轻时曾是一名冒险者，后来专注于药剂学研究"
    )
    
    # 添加药水
    alchemist.add_shop_item(
        {'id': 'health_potion', 'name': '生命药水', 'description': '恢复50点生命值', 
         'item_type': 'consumable', 'properties': {'heal': 50}}, 
        25, 10
    )
    alchemist.add_shop_item(
        {'id': 'mana_potion', 'name': '魔法药水', 'description': '恢复30点魔法值', 
         'item_type': 'consumable', 'properties': {'mana': 30}}, 
        20, 10
    )
    npcs[alchemist.id] = alchemist
    
    return npcs
