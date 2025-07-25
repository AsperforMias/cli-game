"""
AI Service - AI NPC 对话服务
处理NPC的智能对话和情感系统
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIService:
    """AI服务类，处理NPC对话"""
    
    def __init__(self):
        # 可以配置不同的AI服务提供商
        self.api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        if self.api_key == "your-api-key-here":
            logger.warning("AI API key not configured, using mock responses")
            self.use_mock = True
        else:
            self.use_mock = False
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        # NPC情感状态缓存
        self.npc_moods = {}
        
        # 对话历史
        self.dialogue_history = {}
    
    async def process_dialogue(self, npc, player_input: str, player) -> str:
        """处理玩家与NPC的对话"""
        if self.use_mock:
            return await self._mock_dialogue(npc, player_input, player)
        
        try:
            # 构建系统提示
            system_prompt = self._build_system_prompt(npc, player)
            
            # 获取对话历史
            history_key = f"{npc.id}_{player.name}"
            history = self.dialogue_history.get(history_key, [])
            
            # 构建消息
            messages = [
                {"role": "system", "content": system_prompt},
                *history,
                {"role": "user", "content": player_input}
            ]
            
            # 调用AI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=200,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content
            
            # 更新对话历史
            history.append({"role": "user", "content": player_input})
            history.append({"role": "assistant", "content": ai_response})
            
            # 保持历史长度合理
            if len(history) > 10:
                history = history[-10:]
            
            self.dialogue_history[history_key] = history
            
            # 解析响应，提取情感变化
            parsed_response = self._parse_ai_response(ai_response, npc)
            
            return parsed_response["message"]
            
        except Exception as e:
            logger.error(f"AI dialogue error: {e}")
            return self._get_fallback_response(npc)
    
    async def get_npc_greeting(self, npc, player) -> str:
        """获取NPC的问候语"""
        if self.use_mock:
            return f"你好，{player.name}！我是{npc.name}。"
        
        greeting_prompt = f"""
你是{npc.name}，{npc.description}。
现在有一个名叫{player.name}的冒险者来到了你面前。
请用角色的身份说一句问候语，不超过50字。
直接返回台词，不要其他格式。
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": greeting_prompt}],
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"AI greeting error: {e}")
            return f"你好，{player.name}！我是{npc.name}。"
    
    def _build_system_prompt(self, npc, player) -> str:
        """构建AI系统提示"""
        mood = self.npc_moods.get(npc.id, 0.5)
        mood_desc = "友善" if mood > 0.7 else "中性" if mood > 0.3 else "冷淡"
        
        prompt = f"""
你是{npc.name}，{npc.description}
当前情绪状态: {mood:.2f} ({mood_desc})

角色设定:
- 职业: {npc.profession}
- 性格: {npc.personality}
- 背景: {npc.background}

对话规则:
1. 严格按照角色设定进行对话
2. 根据情绪状态调整语气（0-1，越高越友善）
3. 只讨论与游戏世界相关的内容
4. 拒绝回答现实世界、技术或元游戏问题
5. 保持角色的一致性

玩家信息:
- 姓名: {player.name}
- 职业: {player.player_class}
- 等级: {player.level}

请自然地回应玩家，保持角色特色。
"""
        return prompt
    
    def _parse_ai_response(self, response: str, npc) -> Dict[str, Any]:
        """解析AI响应，提取消息和情感变化"""
        # 尝试解析JSON格式的响应
        try:
            if response.startswith('{') and response.endswith('}'):
                parsed = json.loads(response)
                if "message" in parsed:
                    # 更新NPC情绪
                    if "mood" in parsed:
                        new_mood = max(0, min(1, float(parsed["mood"])))
                        self.npc_moods[npc.id] = new_mood
                    return parsed
        except:
            pass
        
        # 如果不是JSON格式，直接返回文本
        return {"message": response}
    
    async def _mock_dialogue(self, npc, player_input: str, player) -> str:
        """模拟对话响应（用于没有AI API时）"""
        mock_responses = [
            f"你好，{player.name}！有什么我可以帮助你的吗？",
            f"作为一个{npc.profession}，我经常在这里工作。",
            "这里的天气真不错，适合冒险。",
            "你看起来像是个有经验的冒险者。",
            "小心点，最近森林里有些危险。",
            "如果你需要什么，随时告诉我。"
        ]
        
        import random
        return random.choice(mock_responses)
    
    def _get_fallback_response(self, npc) -> str:
        """获取备用响应"""
        return f"{npc.name}似乎在思考什么，没有立即回应。"
    
    def update_npc_mood(self, npc_id: str, mood_change: float):
        """更新NPC情绪"""
        current_mood = self.npc_moods.get(npc_id, 0.5)
        new_mood = max(0, min(1, current_mood + mood_change))
        self.npc_moods[npc_id] = new_mood
    
    def get_npc_mood(self, npc_id: str) -> float:
        """获取NPC情绪"""
        return self.npc_moods.get(npc_id, 0.5)
    
    def reset_dialogue_history(self, npc_id: str, player_name: str):
        """重置对话历史"""
        history_key = f"{npc_id}_{player_name}"
        if history_key in self.dialogue_history:
            del self.dialogue_history[history_key]
