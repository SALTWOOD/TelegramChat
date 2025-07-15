from typing import List

from mcdreforged.api.types import PluginServerInterface

from telegram import Update
from telegram.ext import ContextTypes

from .. import tools
from ..config import ConfigManager
from .types import MessageType

async def command(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    cmd = command[0]
    if event_type == MessageType.ADMIN:
        await tools.execute(server, event, context, cmd)

async def list(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, *args):
    players = ConfigManager.online_player_api.get_player_list()

    count = len(players)
    message = f"服务器目前有 {count} 个玩家在线~"
    if count:
        message += f"\n=== 玩家列表 ===\n"
        for player in players: message += f"{player}\n"

    await tools.send_to(event, context, message)

async def mc(
        server: PluginServerInterface,
        event: Update,
        context: ContextTypes.DEFAULT_TYPE,
        command: List[str],
        event_type: MessageType
):

    id = str(tools.get_id(event))
    if id in ConfigManager.bindings.keys() and id in ConfigManager.config.admins:
        server.say(f"§2[TG] §a<{ConfigManager.bindings[id]}>§7 {command[0]}")
    else:
        server.say(f"§7[TG] §a<{ConfigManager.bindings[id]}>§7 {command[0]}")