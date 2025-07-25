"""
World - 游戏世界系统
管理场景、地图、NPC分布等
"""

import json
import os
from typing import Dict, List, Any, Optional
from npc import NPC, create_default_npcs, load_npcs_from_file

class Scene:
    """场景类"""
    
    def __init__(self, scene_id: str, name: str, description: str):
        self.id = scene_id
        self.name = name
        self.description = description
        self.exits = {}  # 出口：方向 -> 目标场景ID
        self.npcs = []   # 场景中的NPC
        self.items = []  # 场景中的物品
        self.events = [] # 场景事件
        self.ascii_art = ""  # 场景的ASCII艺术
        self.background_music = ""  # 背景音乐（如果支持）
        
        # 场景属性
        self.is_safe = True  # 是否安全区域
        self.weather = "clear"  # 天气
        self.time_of_day = "day"  # 时间段
        
    def add_exit(self, direction: str, target_scene: str, description: str = ""):
        """添加出口"""
        self.exits[direction] = {
            'target': target_scene,
            'description': description
        }
    
    def add_npc(self, npc: NPC):
        """添加NPC到场景"""
        if npc not in self.npcs:
            self.npcs.append(npc)
            npc.scene_id = self.id
    
    def remove_npc(self, npc_id: str):
        """从场景移除NPC"""
        self.npcs = [npc for npc in self.npcs if npc.id != npc_id]
    
    def get_npc(self, npc_name: str) -> Optional[NPC]:
        """根据名字查找NPC"""
        for npc in self.npcs:
            if npc.name.lower() == npc_name.lower() or npc.id.lower() == npc_name.lower():
                return npc
        return None
    
    def get_npcs_by_type(self, npc_type) -> List[NPC]:
        """根据类型获取NPC"""
        return [npc for npc in self.npcs if npc.npc_type == npc_type]
    
    def add_item(self, item_data: Dict[str, Any]):
        """在场景中添加物品"""
        self.items.append(item_data)
    
    def remove_item(self, item_id: str):
        """从场景移除物品"""
        self.items = [item for item in self.items if item.get('id') != item_id]
    
    def get_full_description(self) -> str:
        """获取完整的场景描述"""
        desc = self.description
        
        # 添加天气和时间信息
        if self.weather != "clear":
            weather_desc = {
                "rain": "外面正在下雨。",
                "snow": "雪花纷飞。",
                "fog": "周围雾气弥漫。",
                "storm": "暴风雨正在肆虐。"
            }
            desc += " " + weather_desc.get(self.weather, "")
        
        # 添加NPC信息
        if self.npcs:
            desc += "\n\n这里有："
            for npc in self.npcs:
                desc += f"\n  - {npc.name}（{npc.profession}）"
        
        # 添加物品信息
        if self.items:
            desc += "\n\n你看到了一些物品："
            for item in self.items:
                desc += f"\n  - {item['name']}"
        
        return desc

class World:
    """游戏世界类"""
    
    def __init__(self):
        self.scenes = {}
        self.npcs = {}
        self.current_weather = "clear"
        self.current_time = "day"
        self.world_events = []
        
    async def load_data(self):
        """加载世界数据"""
        # 确保数据目录存在
        os.makedirs("data/scenes", exist_ok=True)
        os.makedirs("data/npcs", exist_ok=True)
        
        # 创建默认数据
        await self.create_default_world()
        
        # 尝试加载自定义数据
        await self.load_scenes_from_file("data/scenes/scenes.json")
        await self.load_npcs_from_file("data/npcs/npcs.json")
    
    async def create_default_world(self):
        """创建默认的游戏世界"""
        # 创建场景
        await self.create_default_scenes()
        
        # 创建NPC
        self.npcs = create_default_npcs()
        
        # 将NPC放置到场景中
        await self.place_npcs()
    
    async def create_default_scenes(self):
        """创建默认场景"""
        # 新手村
        starting_village = Scene(
            "starting_village",
            "新手村",
            "这是一个宁静的小村庄，是许多冒险者开始旅程的地方。村子里有几栋朴素的房屋，中央有一个古老的井。村民们友善而热情，总是乐于帮助新来的冒险者。"
        )
        starting_village.ascii_art = """
    🏠    🏠    🏠
      \\   |   /
       \\  |  /
        \\ | /
    🏠---🏛️---🏠
        / | \\
       /  |  \\
      /   |   \\
    🏠    🏠    🏠
        """
        starting_village.add_exit("north", "forest_entrance", "通往森林的小径")
        starting_village.add_exit("east", "trading_post", "通往贸易站的道路")
        starting_village.add_exit("west", "farmland", "通往农田的小路")
        self.scenes[starting_village.id] = starting_village
        
        # 森林入口
        forest_entrance = Scene(
            "forest_entrance",
            "森林入口",
            "茂密的森林在你面前展开，阳光透过树叶洒下斑驳的光影。你能听到鸟儿的歌声和远处传来的神秘声音。这里是冒险的开始，但也要小心森林中的危险。"
        )
        forest_entrance.add_exit("south", "starting_village", "回到村庄的路")
        forest_entrance.add_exit("north", "deep_forest", "深入森林")
        forest_entrance.add_exit("east", "crystal_cave", "通往水晶洞穴")
        self.scenes[forest_entrance.id] = forest_entrance
        
        # 深林
        deep_forest = Scene(
            "deep_forest",
            "森林深处",
            "你已经深入森林，周围的树木变得更加茂密，光线也变得昏暗。这里是各种魔法生物的栖息地，包括史莱姆、哥布林和其他危险的生物。小心前进！"
        )
        deep_forest.is_safe = False
        deep_forest.add_exit("south", "forest_entrance", "返回森林入口")
        deep_forest.add_exit("north", "ancient_ruins", "通往古代遗迹")
        self.scenes[deep_forest.id] = deep_forest
        
        # 贸易站
        trading_post = Scene(
            "trading_post",
            "贸易站",
            "这是一个繁忙的贸易站，商人们在这里交易各种货物。你可以看到来自世界各地的商品，从普通的日用品到珍贵的魔法物品应有尽有。"
        )
        trading_post.add_exit("west", "starting_village", "回到村庄")
        trading_post.add_exit("north", "merchant_guild", "商人公会")
        self.scenes[trading_post.id] = trading_post
        
        # 农田
        farmland = Scene(
            "farmland",
            "农田",
            "广阔的农田延伸到地平线，金黄的麦浪在微风中摇摆。农夫们正在辛勤地工作，这里是村庄的主要食物来源。"
        )
        farmland.add_exit("east", "starting_village", "回到村庄")
        farmland.add_exit("north", "windmill", "前往风车")
        self.scenes[farmland.id] = farmland
        
        # 水晶洞穴
        crystal_cave = Scene(
            "crystal_cave",
            "水晶洞穴",
            "这个洞穴的墙壁上长满了发光的水晶，散发出柔和的蓝光。洞穴深处传来神秘的回声，似乎隐藏着什么秘密。"
        )
        crystal_cave.is_safe = False
        crystal_cave.add_exit("west", "forest_entrance", "离开洞穴")
        crystal_cave.add_exit("north", "crystal_chamber", "深入洞穴")
        self.scenes[crystal_cave.id] = crystal_cave
        
        # 古代遗迹
        ancient_ruins = Scene(
            "ancient_ruins",
            "古代遗迹",
            "这些古老的石制建筑见证了一个失落文明的辉煌。藤蔓爬满了破损的墙壁，神秘的符文在微光中若隐若现。这里可能隐藏着强大的魔法物品，但也充满了危险。"
        )
        ancient_ruins.is_safe = False
        ancient_ruins.add_exit("south", "deep_forest", "返回森林")
        self.scenes[ancient_ruins.id] = ancient_ruins
    
    async def place_npcs(self):
        """将NPC放置到场景中"""
        npc_placements = {
            "starting_village": ["village_elder", "blacksmith_tom", "alchemist_mary"],
            "trading_post": [],
            "forest_entrance": [],
            "deep_forest": [],
            "crystal_cave": [],
            "ancient_ruins": []
        }
        
        for scene_id, npc_ids in npc_placements.items():
            if scene_id in self.scenes:
                scene = self.scenes[scene_id]
                for npc_id in npc_ids:
                    if npc_id in self.npcs:
                        scene.add_npc(self.npcs[npc_id])
    
    async def load_scenes_from_file(self, filename: str):
        """从文件加载场景数据"""
        if not os.path.exists(filename):
            # 创建默认场景文件
            await self.save_scenes_to_file(filename)
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for scene_data in data:
                scene = Scene(
                    scene_data['id'],
                    scene_data['name'],
                    scene_data['description']
                )
                
                # 加载出口
                if 'exits' in scene_data:
                    for direction, exit_data in scene_data['exits'].items():
                        if isinstance(exit_data, str):
                            scene.exits[direction] = {'target': exit_data, 'description': ''}
                        else:
                            scene.exits[direction] = exit_data
                
                # 加载其他属性
                scene.is_safe = scene_data.get('is_safe', True)
                scene.weather = scene_data.get('weather', 'clear')
                scene.ascii_art = scene_data.get('ascii_art', '')
                
                # 加载场景物品
                if 'items' in scene_data:
                    scene.items = scene_data['items']
                
                self.scenes[scene.id] = scene
                
        except Exception as e:
            print(f"Error loading scenes: {e}")
    
    async def save_scenes_to_file(self, filename: str):
        """保存场景数据到文件"""
        scenes_data = []
        
        for scene in self.scenes.values():
            scene_data = {
                'id': scene.id,
                'name': scene.name,
                'description': scene.description,
                'exits': scene.exits,
                'is_safe': scene.is_safe,
                'weather': scene.weather,
                'ascii_art': scene.ascii_art,
                'items': scene.items
            }
            scenes_data.append(scene_data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(scenes_data, f, ensure_ascii=False, indent=2)
    
    async def load_npcs_from_file(self, filename: str):
        """从文件加载NPC数据"""
        if os.path.exists(filename):
            file_npcs = load_npcs_from_file(filename)
            self.npcs.update(file_npcs)
    
    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """获取指定场景"""
        return self.scenes.get(scene_id)
    
    def get_all_scenes(self) -> Dict[str, Scene]:
        """获取所有场景"""
        return self.scenes
    
    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """获取指定NPC"""
        return self.npcs.get(npc_id)
    
    def get_all_npcs(self) -> Dict[str, NPC]:
        """获取所有NPC"""
        return self.npcs
    
    def add_scene(self, scene: Scene):
        """添加场景"""
        self.scenes[scene.id] = scene
    
    def remove_scene(self, scene_id: str):
        """移除场景"""
        if scene_id in self.scenes:
            del self.scenes[scene_id]
    
    def add_npc(self, npc: NPC, scene_id: str = None):
        """添加NPC"""
        self.npcs[npc.id] = npc
        
        if scene_id and scene_id in self.scenes:
            self.scenes[scene_id].add_npc(npc)
    
    def move_npc(self, npc_id: str, from_scene: str, to_scene: str):
        """移动NPC"""
        if from_scene in self.scenes:
            self.scenes[from_scene].remove_npc(npc_id)
        
        if to_scene in self.scenes and npc_id in self.npcs:
            self.scenes[to_scene].add_npc(self.npcs[npc_id])
    
    def update_weather(self, new_weather: str):
        """更新天气"""
        self.current_weather = new_weather
        
        # 更新所有场景的天气（可以有选择性）
        for scene in self.scenes.values():
            scene.weather = new_weather
    
    def update_time(self, new_time: str):
        """更新时间"""
        self.current_time = new_time
        
        for scene in self.scenes.values():
            scene.time_of_day = new_time
    
    def add_world_event(self, event: Dict[str, Any]):
        """添加世界事件"""
        self.world_events.append(event)
    
    def get_random_encounter(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """获取随机遭遇（用于战斗或事件）"""
        scene = self.get_scene(scene_id)
        if not scene or scene.is_safe:
            return None
        
        # 这里可以实现随机遭遇逻辑
        encounters = {
            "deep_forest": [
                {"type": "enemy", "id": "slime", "name": "史莱姆", "chance": 0.3},
                {"type": "enemy", "id": "goblin", "name": "哥布林", "chance": 0.2},
                {"type": "treasure", "items": ["health_potion"], "chance": 0.1}
            ],
            "crystal_cave": [
                {"type": "enemy", "id": "crystal_golem", "name": "水晶魔像", "chance": 0.2},
                {"type": "treasure", "items": ["mana_crystal"], "chance": 0.15}
            ]
        }
        
        import random
        scene_encounters = encounters.get(scene_id, [])
        
        for encounter in scene_encounters:
            if random.random() < encounter['chance']:
                return encounter
        
        return None
    
    def get_scene_connections(self) -> Dict[str, List[str]]:
        """获取场景连接图（用于寻路等）"""
        connections = {}
        
        for scene_id, scene in self.scenes.items():
            connections[scene_id] = []
            for direction, exit_data in scene.exits.items():
                target = exit_data if isinstance(exit_data, str) else exit_data['target']
                connections[scene_id].append(target)
        
        return connections
    
    def find_path(self, start_scene: str, end_scene: str) -> List[str]:
        """寻找两个场景之间的路径"""
        connections = self.get_scene_connections()
        
        # 简单的BFS寻路
        from collections import deque
        
        queue = deque([(start_scene, [start_scene])])
        visited = {start_scene}
        
        while queue:
            current, path = queue.popleft()
            
            if current == end_scene:
                return path
            
            for neighbor in connections.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []  # 没有找到路径
