# common/appium_server.py
"""
Appium Server 管理器（支持 CI / 本地双模）
✅ 本地：自启动 + 端口管理
✅ CI：只读模式，直连宿主机 Appium
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
        # ✅ CI 环境识别（Jenkins 中配置 CI=true）
        self.ci_mode = os.getenv("CI", "false").lower() == "true"

        # ✅ CI 模式下强制使用宿主机地址
        if self.ci_mode:
            self.host = os.getenv("APPIUM_HOST", "host.docker.internal")
        else:
            self.host = host

        self.port = port
        self.server_url = f"http://{self.host}:{port}"
        self.process: Optional[subprocess.Popen] = None

        if self.ci_mode:
            logger.info(f"🧪 CI 模式：跳过 Appium 自启动，直连 {self.server_url}")

    def is_port_available(self) -> bool:
        """检查端口是否可用（CI 模式下跳过）"""
        if self.ci_mode:
            return True  # CI 不关心端口占用，由宿主机负责

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
        """启动 Appium Server（CI 模式下直接跳过）"""
        if self.ci_mode:
            if self.is_server_running():
                logger.info(f"✅ CI 模式：检测到 Appium Server 已运行 {self.server_url}")
                return True
            else:
                logger.error(f"❌ CI 模式：Appium Server 未运行，请先在宿主机启动")
                logger.error(f"   执行：appium -a 0.0.0.0 -p {self.port} --session-override")
                return False

        logger.info(f"🚀 启动 Appium Server: {self.server_url}")

        if not self.is_port_available():
            logger.warning(f"⚠️ 端口 {self.port} 被占用，尝试释放...")
            self._kill_process_on_port()
            time.sleep(2)

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
        logger.info("⏳ 等待 Appium Server 就绪...")
        for _ in range(timeout):
            if self.is_server_running():
                return True
            time.sleep(1)
        return False

    def _kill_process_on_port(self):
        """杀掉占用端口的进程（CI 模式下不执行）"""
        if self.ci_mode:
            return

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
        """停止 Appium Server（CI 模式下不执行）"""
        if self.ci_mode or not self.process:
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
            logger.info(f"ℹ️ Appium Server 已运行: {server.server_url}")
            yield server
        else:
            if server.start():
                yield server
            else:
                raise RuntimeError("Appium Server 启动失败")
    finally:
        server.stop()