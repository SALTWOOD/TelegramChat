import asyncio
import logging
import threading
import time
from typing import Callable

from telegram import Bot, Update
from telegram.ext import Application, ApplicationBuilder, filters, MessageHandler

class TelegramBot:
    action: Callable
    application: Application
    bot_thread: threading.Thread
    loop: asyncio.AbstractEventLoop
    logger: logging.Logger
    stop_sign: threading.Event
    
    _timeout: int = 60
    
    @property
    def bot(self) -> Bot:
        return self.application.bot

    def __init__(self, logger: logging.Logger, token: str, api: str = "https://api.telegram.org/bot", timeout: int = 60):
        self.application = ApplicationBuilder().base_url(api).token(token).build()
        self.stop_sign = threading.Event()
        self.logger = logger
        self.loop = asyncio.new_event_loop()
        self._timeout = timeout

    def register(self):
        """
        注册命令处理器
        """
        self.application.handlers.clear()
        normal_handler = MessageHandler(filters.ALL, self.action)
        self.application.add_handler(normal_handler)
            
    def start(self, wait_until_connected: bool = False):
        """
        启动机器人
        """
        self.bot_thread = threading.Thread(target=self._start_check_thread, daemon=True)
        self.bot_thread.start()
        
        if wait_until_connected:
            start_time = time.time()
            while True:
                if self.application.running:
                    break
                if time.time() - start_time > self._timeout:
                    raise Exception("Unable to start Telegram bot.")
                time.sleep(0.5)
        self.logger.info("Telegram bot started.")
    
    def stop(self):
        """
        停止机器人
        """
        asyncio.set_event_loop(self.loop)
        if not self.application.running: return
        
        self.stop_sign.set()
        if self.bot_thread.is_alive():
            self.bot_thread.join(timeout=5)
        self.stop_sign.clear()
        self.logger.info("Telegram bot stopped.")
        
    def _stop_check(self):
        """
        检查线程
        """
        asyncio.set_event_loop(self.loop)
        while True:
            if self.stop_sign.is_set():
                self.loop.stop()
                return
            time.sleep(1)
    
    def _start_check_thread(self):
        """
        启动检查线程
        """
        try:
            asyncio.set_event_loop(self.loop)
            threading.Thread(target=self._stop_check, daemon=True).start()
            self.application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)
        except Exception as e:
            self.logger.error(f"Failed to start Telegram bot! Error: {e}")