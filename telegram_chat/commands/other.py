import time
from typing import List

from mcdreforged.api.types import PluginServerInterface

from telegram import Update
from telegram.ext import ContextTypes

from .. import tools
from ..const import Help
from ..info import get_system_info
from . import ChatType, MessageType

async def help(server, event, context, command, type):
    await tools.send_to(event, context, Help.admin) if type == MessageType.ADMIN else await tools.send_to(event, context, Help.user)

async def info(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    if event_type == MessageType.ADMIN and event.message and tools.get_type(event) == ChatType.PRIVATE:
        await tools.send_to(
            event,
            context,
            get_system_info()
        )

async def ping(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    if event.message is None: raise Exception("event.message is none")
    delay = max((time.time() - event.message.date.timestamp()) * 1000, 0)
    await tools.send_to(
        event,
        context,
        f"Pong！服务在线，延迟 {delay:.2f}ms。"
    )

async def reload(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                      event_type: MessageType):
    if event_type == MessageType.ADMIN:
        await tools.send_to(
            event,
            context,
            f"收到，正在重载……"
        )
        server.reload_plugin("telegram_chat")