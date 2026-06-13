# common/appium_server.py
"""
Appium Server 管理器（独立模块）
✅ 支持自启动
✅ 宽松安全模式
✅ 端口冲突自动释放
✅ 优雅关闭
"""

import os
import signal
import socket
import subprocess
import time
from contextlib import contextmanager
from typing import Optional

import requests

from utils.logging.logger import logger


class AppiumServer:
    """Appium Server 管理类"""

    def __init__(self, host: str = "127.0.0.1", port: int = 4723):
        self.host = host
        self.port = port
        self.server_url = f"http://{host}:{port}"
        self.process: Optional[subprocess.Popen] = None

    def is_port_available(self) -> bool:
        """检查端口是否可用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self.host, self.port))
                return True
            except socket.error:
                return False

    def is_server_running(self) -> bool:
        """检查 Appium Server 是否已运行"""
        try:
            response = requests.get(f"{self.server_url}/status", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def start(self) -> bool:
        """启动 Appium Server"""
        logger.info(f"🚀 启动 Appium Server: {self.server_url}")

        # 端口被占用则释放
        if not self.is_port_available():
            logger.warning(f"⚠️ 端口 {self.port} 被占用，尝试释放...")
            self._kill_process_on_port()
            time.sleep(2)

        # ✅ 必须加 --relaxed-security
        cmd = [
            "appium",
            "--address", self.host,
            "--port", str(self.port),
            "--relaxed-security",
            "--log-level", "warn",
            "--session-override"
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )

            if self._wait_for_server():
                logger.info(f"✅ Appium Server 启动成功: {self.server_url}")
                return True
            else:
                logger.error("❌ Appium Server 启动超时")
                self.stop()
                return False

        except Exception as e:
            logger.error(f"❌ 启动 Appium Server 失败: {e}")
            return False

    def _wait_for_server(self, timeout: int = 30) -> bool:
        """等待服务器就绪"""
        logger.info("⏳ 等待 Appium Server 就绪...")
        for _ in range(timeout):
            if self.is_server_running():
                return True
            time.sleep(1)
        return False

    def _kill_process_on_port(self):
        """杀掉占用端口的进程"""
        try:
            if os.name == 'nt':
                subprocess.run(
                    f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{self.port}\') do taskkill /PID %a /F',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.run(
                    f"lsof -ti:{self.port} | xargs kill -9",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception:
            pass

    def stop(self):
        """停止 Appium Server"""
        if not self.process:
            return

        logger.info("🛑 停止 Appium Server...")
        try:
            if os.name == 'nt':
                self.process.send_signal(signal.CTRL_C_EVENT)
            else:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

            self.process.wait(timeout=10)
            logger.info("✅ Appium Server 已停止")
        except Exception:
            self.process.kill()
        finally:
            self.process = None


@contextmanager
def appium_server_context(host: str = "127.0.0.1", port: int = 4723):
    """Appium Server 上下文管理器"""
    server = AppiumServer(host=host, port=port)
    try:
        if server.is_server_running():
            logger.info(f"ℹ️ Appium Server 已在运行: {server.server_url}")
            yield server
        else:
            if server.start():
                yield server
            else:
                raise RuntimeError("Appium Server 启动失败")
    finally:
        if server.process:
            server.stop()