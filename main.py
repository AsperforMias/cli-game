#!/usr/bin/env python3
"""
CLI RPG Game - Main Server
基于SSH的命令行RPG游戏服务器
"""

import asyncssh
import asyncio
import os
import json
import logging
from game_engine import GameEngine
from ai_service import AIService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RPGGameServer(asyncssh.SSHServer):
    """SSH游戏服务器"""
    
    def __init__(self):
        super().__init__()
        self.ai_service = AIService()
        
    def connection_made(self, conn):
        self.conn = conn
        try:
            peer = conn.get_extra_info('peername')
            logger.info(f"New connection from {peer[0]}")
        except Exception as e:
            logger.error(f"Connection made error: {e}")

    def connection_lost(self, exc):
        if exc is None:
            logger.info("Client disconnected")
        else:
            logger.error(f"Connection lost: {exc}")

    def begin_auth(self, username):
        self.username = username
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        # 简单的密码验证，实际项目中应该使用更安全的方式
        if password == "rpg2025":
            logger.info(f"User {username} authenticated successfully")
            return True
        logger.warning(f"Failed authentication attempt for {username}")
        return False

    def session_requested(self):
        return RPGGameSession(self.ai_service)


class RPGGameSession(asyncssh.SSHServerSession):
    """SSH游戏会话"""
    
    def __init__(self, ai_service):
        super().__init__()
        self.chan = None
        self.game_engine = None
        self.ai_service = ai_service
        
    def shell_requested(self):
        return True

    def pty_requested(self, term_type, term_size, term_modes):
        if term_size:
            logger.info(f"Terminal size: {term_size[0]}x{term_size[1]}")
        return True

    def connection_made(self, chan):
        self.chan = chan
        self.game_engine = GameEngine(chan, self.ai_service)

    def session_started(self):
        asyncio.create_task(self._run_game())
        
    def data_received(self, data, datatype):
        """处理接收到的数据"""
        if self.game_engine:
            # 将数据传递给游戏引擎处理
            asyncio.create_task(self.game_engine.process_input_data(data))

    async def _run_game(self):
        """运行游戏主循环"""
        try:
            print(f"新的游戏会话开始...")
            self.chan.set_write_buffer_limits(0)
            
            # 发送欢迎信息
            self.chan.write("欢迎来到CLI RPG游戏！\n")
            self.chan.write("正在初始化...\n")
            
            await self.game_engine.run()
            
        except (asyncssh.BreakReceived, asyncssh.TerminalSizeChanged):
            print("客户端断开连接")
        except Exception as e:
            print(f"游戏会话错误: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.chan.write(f"\n游戏出错: {str(e)}\n")
                self.chan.write("按任意键退出...\n")
                await asyncio.sleep(2)
            except:
                pass
        finally:
            print("游戏会话结束")
            if self.chan is not None:
                try:
                    self.chan.write("\n感谢游玩！再见！\n")
                    await asyncio.sleep(1)
                    await self.chan.close()
                except:
                    pass


def generate_ssh_key():
    """生成SSH密钥"""
    key_path = 'ssh_host_key'
    if not os.path.exists(key_path):
        logger.info("Generating SSH host key...")
        key = asyncssh.generate_private_key('ssh-rsa', key_size=2048)
        key.write_private_key(key_path)
        logger.info(f"SSH host key generated and saved to {key_path}")
    else:
        logger.info(f"Using existing SSH host key at {key_path}")


async def run_server():
    """运行SSH服务器"""
    host = '0.0.0.0'
    port = 2222

    logger.info(f"Starting RPG game server on {host}:{port}")
    logger.info("Connect with: ssh -p 2222 player@localhost")
    logger.info("Password: rpg2025")

    try:
        await asyncssh.create_server(
            RPGGameServer,
            host,
            port,
            server_host_keys=['ssh_host_key']
        )
    except Exception as e:
        logger.error(f"Server creation error: {e}")
        raise


def main():
    """主入口函数"""
    generate_ssh_key()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        logger.info("Starting RPG server...")
        server_task = loop.create_task(run_server())
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("\nServer shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        tasks = asyncio.all_tasks(loop)
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.close()
        logger.info("Server stopped.")


if __name__ == "__main__":
    main()
