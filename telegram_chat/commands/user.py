from typing import List

from mcdreforged.api.types import PluginServerInterface

from telegram import Update
from telegram.ext import ContextTypes

from .. import tools
from ..config import *
from . import MessageType

async def bot_ban(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                       event_type: MessageType):
    id = command[0]
    if id not in ban_list and event_type == MessageType.ADMIN:
        ban_list.append(int(id))
        await tools.send_to(
            event,
            context,
            f"成功封禁 Telegram 账号: {id}"
        )
        tools.save_data(server)

async def bot_pardon(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                          event_type: MessageType):
    id = command[0]
    if id in ban_list and event_type == MessageType.ADMIN:
        ban_list.remove(id)
        await tools.send_to(
            event,
            context,
            f"成功解封 Telegram 账号: {id}"
        )
        tools.save_data(server)
        
def ban(server, event, context, command, event_type):
    tools.execute(server, event, context, f"ban {command[0]}") if event_type == MessageType.ADMIN else None

def pardon(server, event, context, command, event_type):
    tools.execute(server, event, context, f"pardon {command[0]}") if event_type == MessageType.ADMIN else None