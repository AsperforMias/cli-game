#!/usr/bin/env python3
"""
简化的SSH测试服务器 - 用于调试连接问题
"""

import asyncssh
import asyncio
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleGameSession(asyncssh.SSHServerSession):
    """简化的游戏会话"""
    
    def __init__(self):
        super().__init__()
        self.chan = None
        self.running = False
    
    def shell_requested(self):
        return True
    
    def pty_requested(self, term_type, term_size, term_modes):
        logger.info(f"PTY请求: {term_type}, 大小: {term_size}")
        return True
    
    def session_started(self):
        logger.info("会话开始")
        asyncio.create_task(self.run_simple_game())
    
    def connection_made(self, chan):
        logger.info("连接建立")
        self.chan = chan
        self.running = True
    
    async def run_simple_game(self):
        """运行简化的游戏"""
        try:
            # 清屏并显示欢迎信息
            self.chan.write("\x1b[2J\x1b[H")
            self.chan.write("🎮 CLI RPG Game - 测试版本\r\n")
            self.chan.write("=" * 50 + "\r\n")
            self.chan.write("连接成功！游戏正在运行...\r\n\r\n")
            
            # 显示简单菜单
            self.chan.write("可用命令:\r\n")
            self.chan.write("  help  - 显示帮助\r\n")
            self.chan.write("  test  - 测试功能\r\n")
            self.chan.write("  quit  - 退出游戏\r\n\r\n")
            self.chan.write("请输入命令: ")
            
            # 简单的输入循环
            while self.running:
                try:
                    # 读取用户输入
                    data = await asyncio.wait_for(self.chan.read(1024), timeout=1.0)
                    if data:
                        command = data.strip()
                        logger.info(f"收到命令: {command}")
                        
                        if command == 'quit':
                            self.chan.write("\r\n正在退出...\r\n")
                            break
                        elif command == 'help':
                            self.chan.write("\r\n这是帮助信息！\r\n")
                        elif command == 'test':
                            self.chan.write("\r\n测试功能正常！\r\n")
                        else:
                            self.chan.write(f"\r\n未知命令: {command}\r\n")
                        
                        self.chan.write("请输入命令: ")
                
                except asyncio.TimeoutError:
                    # 超时是正常的，继续循环
                    continue
                except Exception as e:
                    logger.error(f"输入处理错误: {e}")
                    break
            
        except Exception as e:
            logger.error(f"游戏运行错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            logger.info("游戏会话结束")
            try:
                self.chan.write("\r\n感谢游玩！再见！\r\n")
                await asyncio.sleep(1)
                self.chan.close()
            except:
                pass
    
    def connection_lost(self, exc):
        logger.info(f"连接断开: {exc}")
        self.running = False

class SimpleGameServer(asyncssh.SSHServer):
    """简化的游戏服务器"""
    
    def connection_made(self, conn):
        logger.info(f"新连接: {conn.get_extra_info('peername')}")
    
    def connection_lost(self, exc):
        logger.info(f"连接丢失: {exc}")
    
    def begin_auth(self, username):
        logger.info(f"认证开始: {username}")
        return True
    
    def password_auth_supported(self):
        return True
    
    def validate_password(self, username, password):
        logger.info(f"密码验证: {username}")
        if password == "rpg2025":
            logger.info("认证成功")
            return True
        logger.warning("认证失败")
        return False
    
    def session_requested(self):
        logger.info("会话请求")
        return SimpleGameSession()

async def main():
    """主函数"""
    try:
        logger.info("启动简化测试服务器...")
        
        # 启动服务器
        server = await asyncssh.create_server(
            SimpleGameServer,
            '0.0.0.0',
            2222,
            server_host_keys=['ssh_host_key']
        )
        
        logger.info("服务器启动成功！")
        print("🚀 简化测试服务器已启动")
        print("连接方式: ssh -p 2222 player@localhost")
        print("密码: rpg2025")
        print("按 Ctrl+C 停止服务器")
        
        # 保持服务器运行
        await server.wait_closed()
        
    except KeyboardInterrupt:
        logger.info("服务器被用户停止")
    except Exception as e:
        logger.error(f"服务器错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
