from typing import List

from mcdreforged.api.types import PluginServerInterface

from telegram import Update
from telegram.ext import ContextTypes

from .. import tools
from .types import MessageType

async def whitelist_add(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                             event_type: MessageType):
    if event_type == MessageType.ADMIN:
        await tools.add_to_whitelist(server, event, context, command[0])

async def whitelist_remove(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                             event_type: MessageType):
    if event_type == MessageType.ADMIN:
        await tools.remove_from_whitelist(server, event, context, command[0])
