import logging
from typing import Any

from mcdreforged.api.command import CommandContext, GreedyText, Literal
from mcdreforged.api.types import CommandSource, Info, PluginServerInterface

from telegram import MessageEntity, Update
from telegram.ext import ContextTypes

from . import tools
from .commands import ChatType, MessageType, register_commands
from .command_builder import CommandBuilder
from .config import *
from .const import VERSION, VERSION_STR
from .telegram_manager import TelegramBot

# 变量声明
command_tree: CommandBuilder

# 实用函数
async def execute_bot_command(server: PluginServerInterface, event: Update, context: CommandContext | ContextTypes.DEFAULT_TYPE, content: str, type: MessageType):
    if content.startswith('/'):
        func, args = command_tree.get(content)
        if func is not None:
            server.logger.debug("找到对应的命令处理器！")
            server.logger.debug(f"命令：{func}，参数：{args}")
            await func(server, event, context, args, type)
        else:
            server.logger.debug("未找到对应的命令处理器！")

# MCDR 事件处理函数
async def on_load(server: PluginServerInterface, old):
    """
    插件加载操作
    """
    global bindings, ban_list, bot, logger
    
    load_data(server)
    
    online_player_api = server.get_plugin_instance("online_player_api")
    if online_player_api is None: raise Exception("Unable to load dependency \"online_player_api\"")
    
    async def action(event: Update, context: ContextTypes.DEFAULT_TYPE):
        await on_message(server, event, context)
    
    bot = TelegramBot(server.logger, config.telegram["token"]) if config.telegram["api"] is None else TelegramBot(server.logger, config.telegram["token"], config.telegram["api"])
    bot.action = action
    bot.register()
    bot.start(True)
    
    logger = server.logger
    register_commands()

    server.register_help_message("!!tg", "向 Telegram 群聊发送聊天信息")
    server.register_command(
        Literal("!!tg").then(GreedyText("message").runs(mc_command_tg))
    )
    
    
    if old is not None and old.VERSION < VERSION:
        tip: str = f"TelegramChat 已从 ver.{old.const.VERSION_STR} 更新到 ver.{VERSION_STR}"
        # await tools.send_to_group(tip)
        server.say(f"§7{tip}")

def on_unload(server: PluginServerInterface): bot.stop() if bot is not None else None

async def on_user_info(server: PluginServerInterface, info: Info):
    if config.forwardings["mc_to_tg"] is True and info.player:
        await tools.send_to_group(f"{info.player}:\n{info.content}", entities=[MessageEntity("bold", 0, len(info.player) + 1)])

async def on_player_joined(server: PluginServerInterface, player: str, info: Info):
    message = f"{player} 加入了游戏。"
    await tools.send_to_group(message, entities=[MessageEntity("italic", 0, len(message)), MessageEntity("bold", 0, len(player))])

async def on_player_left(server: PluginServerInterface, player: str):
    message = f"{player} 离开了游戏。"
    await tools.send_to_group(message, entities=[MessageEntity("italic", 0, len(message)), MessageEntity("bold", 0, len(player))])

async def on_message(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE):
    if event.message is None: return
    content = event.message.text
    if content is None: return
    event_type = tools.parse_event_type(event)
    logger.debug(f"Update 数据：\n{event}")
    
    typ = tools.get_type(event)
    # 防止自己的机器人被别人拉去用还越权
    match (typ):
        case ChatType.PRIVATE:
            if str(tools.get_id(event)) not in config.admins: return
        case ChatType.GROUP:
            if str(tools.get_id(event)) not in config.admins and event.message.chat.id != config.group: return
        case _:
            return
    
    # 普通信息
    if config.forwardings["tg_to_mc"] is True and typ == ChatType.GROUP:
        id: str = str(tools.get_id(event))
        name: str = f"§a<{bindings[id]}>§7" if id in bindings else f"§4<{event.message.chat.full_name} ({id})>§7"
        server.say(f"§7[TG] {name}: {content}")

    # 封禁列表，不作应答
    if tools.get_id(event) in ban_list:
        server.logger.debug(f"用户 {tools.get_id(event)} 已被封禁，拒绝处理其请求")
        return
        
    server.logger.debug(f"正在处理用户 {tools.get_id(event)} 的请求……")
    server.logger.debug(f"用户请求执行命令：{content}")
    await execute_bot_command(server, event, context, content, event_type)

# MC 命令处理器
async def mc_command_tg(src: CommandSource, ctx: CommandContext):
    player = "Console"
    if src.is_player:
        player = src.player # type: ignore
        if player not in bindings.values():
            src.reply("请先在群内绑定你的账号！")
            return
        elif (not str(next((key for key, value in bindings.items() if value == player), 0)) in config.admins and not src.has_permission(2)) and (player != "Console"):
            src.reply("你没有足够的权限！")
            return
    msg = f"{player}:\n{ctx['message']}"
    await tools.send_to_group(msg, entities=[MessageEntity("bold", 0, len(player) + 1)])

__all__ = ["bot", "command_tree", "logger"]