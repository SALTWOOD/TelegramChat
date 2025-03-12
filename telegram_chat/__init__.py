import re
from typing import List, Dict, Any

from mcdreforged.api.command import CommandContext, Literal, GreedyText
from mcdreforged.api.utils import Serializable
from mcdreforged.api.types import PluginServerInterface, CommandSource, Info
from enum import Enum

from telegram import Update, MessageEntity
from telegram.ext import ContextTypes

import requests
import time
from .command_builder import CommandBuilder
from .info import get_system_info
from .version import *
from .telegram import TelegramBot

import logging

# 变量声明
bot: TelegramBot
bindings: dict[str, str]
commands: CommandBuilder
online_player_api: Any

class Config(Serializable):
    group: int = 0

    admins: List[str] = []

    whitelist: Dict[str, Any] = {
        "add_when_bind": True,
        "verify_player": True
    }
    
    forwardings: Dict[str, bool] = {
        "tg_to_mc": True,
        "mc_to_tg": True,
    }
    
    telegram: Dict[str, Any] = {
        "token": None,
        "api": None
    }

config: Config
ban_list: List[int]
logger: logging.Logger

class MessageType(Enum):
    USER = 0
    ADMIN = 1

class ChatType(Enum):
    PRIVATE = 0
    GROUP = SUPERGROUP = 1
    OTHER = 2

class Help():
    basic = """命令列表：
- /list 获取在线玩家列表
- /bind <ID> 绑定当前 Telegram 账号到 Minecraft 账号
- /mc <message> 向 Minecraft 内发送聊天信息
- /ping 查询在线状态及延迟"""
    
    user = f"""TelegramChat Ver.{VERSION_STR}

{basic}
"""

    admin = f"""TelegramChat Ver.{VERSION_STR}

{basic}

管理命令列表：
- /bind 玩家绑定信息相关操作，使用 /bind 获取详细帮助
- /command 向 Minecraft 服务器发送命令
- /mc <message> 向 Minecraft 内发送聊天信息
- /mcdr <command> 向 MCDR 进程发送命令
- /whitelist <add|remove> <玩家名> 管理白名单，使用 /whitelist 获取详细帮助
- /start /stop /restart 启动、关闭、重启服务器
- /info 仅私聊，获取系统信息
- /reload 重载 Bot
- /ban 封禁某人（游戏内）
- /pardon 解除对某人的封禁（游戏内）
- /bot-ban 不允许某人使用 Bot
- /bot-pardon 不再禁止某人使用 Bot
"""

    bind = """/bind <ID> 绑定当前 Telegram 账号到 Minecraft 账号
/bind <TG> <ID> 绑定 Telegram 账号到 Minecraft 账号
/bind unbind <TG> 解除 Telegram 账号与 Minecraft 账号的绑定关系
/bind query "TG"|"ID" <TG|ID> 查询 Telegram 账号或 Minecraft 账号的绑定关系
"""

    whitelist = """/whitelist <add|remove> <玩家名> 管理白名单
/whitelist list 显示白名单列表
/whitelist reload 重新加载白名单配置文件
/whitelist off 关闭白名单功能
/whitelist on 开启白名单功能
/whitelist add <ID> 添加玩家到白名单
/whitelist remove <ID> 移除白名单中的玩家
"""

# 实用函数
def get_type(event: Update) -> ChatType:
    if event.message is None: raise Exception("event.message is none.")
    match (event.message.chat.type):
        case "private":
            return ChatType.PRIVATE
        case "group":
            return ChatType.GROUP
        case "supergroup":
            return ChatType.SUPERGROUP
        case _:
            return ChatType.OTHER

def get_id(event: Update) -> int:
    if event.message is None: raise Exception("event.message is none")
    if event.message.from_user is None: raise Exception("event.message.from_user is none")
    return event.message.from_user.id

async def execute_bot_command(server: PluginServerInterface, event: Update, context: CommandContext | ContextTypes.DEFAULT_TYPE, content: str, type: MessageType):
    if content.startswith('/'):
        func, args = commands.get(content)
        if func is not None:
            server.logger.debug("找到对应的命令处理器！")
            server.logger.debug(f"命令：{func}，参数：{args}")
            await func(server, event, context, args, type)
        else:
            server.logger.debug("未找到对应的命令处理器！")

async def execute(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    """
    执行控制台命令
    """
    if server.is_rcon_running():
        result = server.rcon_query(command)
        if not result: return
        await send_to(event, context, result)
    else: await send_to(event, context, "请开启 RCON 再执行此操作！")

def load_data(server: PluginServerInterface):
    config = server.load_config_simple(target_class=Config) # type: ignore
    bindings = server.load_config_simple(
        "bindings.json",
        default_config={"data": {}},
        echo_in_console=False
    )["data"]
    ban_list = server.load_config_simple(
        "ban_list.json",
        default_config={"data": []},
        echo_in_console=False
    )["data"]

def save_data(server: PluginServerInterface):
    """
    保存数据
    """
    server.save_config_simple(
        {
            "data": bindings,
        },
        "bindings.json"
    )
    server.save_config_simple(
        {
            "data": ban_list,
        },
        "ban_list.json"
    )

async def add_to_whitelist(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, player: str):
    """
    添加到白名单
    """
    server.execute(f"whitelist add {player}")
    await send_to(
        event,
        context,
        f"已把 \"{player}\" 添加到服务器白名单。"
    )

async def remove_from_whitelist(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, player: str):
    """
    删除白名单
    """
    server.execute(f"whitelist remove {player}")
    await send_to(
        event,
        context,
        f"已把 \"{player}\" 从服务器白名单中移除。"
    )

async def send_to_group(msg: str, **kwargs):
    """
    向所有群聊广播
    """
    await bot.bot.send_message(chat_id=config.group, text=msg, **kwargs)
        
async def send_to(event: Update | CommandSource, context: ContextTypes.DEFAULT_TYPE | CommandContext, message: str, at_sender: bool = True):
    """
    回复信息
    """
    logger.debug(f"发送信息：{message}")
    if (isinstance(event, Update) and not isinstance(context, CommandContext)
        and event.effective_chat is not None and event.effective_message is not None): # 后面的是保证 IDE 不打波浪线
        logger.debug(f"发送到 Telegram，chat_id={event.effective_chat.id}, reply_to_message_id={event.effective_chat.id}")
        await context.bot.send_message(chat_id=event.effective_chat.id, text=message, reply_to_message_id=event.effective_message.id if at_sender else None)
    elif isinstance(event, CommandSource):
        logger.debug(f"发送到 CommandSource。")
        event.reply(message)

def parse_event_type(event: Update) -> MessageType:
    """
    处理事件类型
    """
    return MessageType.ADMIN if str(get_id(event)) in config.admins else MessageType.USER

def register_commands():
    """
    注册命令树
    """
    global commands
    
    def run_command(command, need_admin: bool = False):
        async def _run(server, event, context, _, type):
            if not need_admin or type == MessageType.ADMIN:
                await execute(server, event, context, command)
        return _run
    
    commands = CommandBuilder()
    # /mc
    commands.add_command(re.compile(r'/mc (.*)'), [str], tg_command_mc)

    # /list
    commands.add_command("/list", None, tg_command_list)

    #/bind
    commands.add_command("/bind", None, lambda srv, evt, ctx, cmd, typ: send_to(evt, ctx, Help.bind))
    commands.add_command(re.compile(r'/bind unbind (\d*)'), [str], tg_command_bind_unbind)
    commands.add_command(re.compile(r'/bind query (TG|ID) (\w*)'), [str, str], tg_command_bind_query)
    commands.add_command(re.compile(r'/bind (\d*) (\w*)'), [str, str], tg_command_bind_admin)
    commands.add_command(re.compile(r'/bind (\w*)'), [str], tg_command_bind_user)

    # /whitelist
    commands.add_command("/whitelist", None, lambda srv, evt, ctx, cmd, typ: send_to(evt, ctx, Help.whitelist))
    commands.add_command("/whitelist list", None, run_command("whitelist list", True))
    commands.add_command("/whitelist reload", None, run_command("whitelist reload", True))
    commands.add_command("/whitelist on", None, run_command("whitelist on", True))
    commands.add_command("/whitelist off", None, run_command("whitelist off", True))
    commands.add_command(re.compile(r'/whitelist add (\w*)'), [str], tg_command_whitelist_add)
    commands.add_command(re.compile(r'/whitelist remove (\w*)'), [str], tg_command_whitelist_remove)

    # command
    commands.add_command(re.compile(r'/command (.*)'), [str], tg_command_command)

    # /help
    commands.add_command("/help", None, tg_command_help)
    
    # /ping
    commands.add_command("/ping", None, tg_command_ping)
    
    # /start /stop /restart 
    commands.add_command("/start", None, lambda srv, evt, ctx, cmd, typ: srv.start() if typ == MessageType.ADMIN else None)
    commands.add_command("/stop", None, lambda srv, evt, ctx, cmd, typ: srv.stop() if typ == MessageType.ADMIN else None)
    commands.add_command("/restart", None, lambda srv, evt, ctx, cmd, typ: srv.restart() if typ == MessageType.ADMIN else None)
    
    # /info
    commands.add_command("/info", None, tg_command_info)
    
    # /reload
    commands.add_command("/reload", None, tg_command_reload)
    
    # /ban /pardon
    commands.add_command(re.compile(r'/ban (\d*)'), [int], tg_command_ban)
    commands.add_command(re.compile(r'/pardon (\d*)'), [int], tg_command_pardon)
    
    # /bot-
    commands.add_command(re.compile(r'/bot-ban (\d*)'), [int], tg_command_bot_ban)
    commands.add_command(re.compile(r'/bot-pardon (\d*)'), [int], tg_command_bot_pardon)
    

# MCDR 事件处理函数
async def on_load(server: PluginServerInterface, old):
    """
    插件加载操作
    """
    global config, bindings, ban_list, bot, logger, online_player_api

    load_data(server)

    server.register_help_message("!!tg", "向 Telegram 群聊发送聊天信息")
    server.register_command(
        Literal("!!tg").then(GreedyText("message").runs(mc_command_tg))
    )
    
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
    
    if old is not None and old.VERSION < VERSION:
        tip: str = f"TelegramChat 已从 ver.{old.VERSION_STR} 更新到 ver.{VERSION_STR}"
        # await send_to_group(tip)
        server.say(f"§7{tip}")

def on_unload(server: PluginServerInterface):
    """
    卸载插件执行机器人停止操作
    """
    if bot is not None:
        bot.stop()

async def on_user_info(server: PluginServerInterface, info: Info):
    if config.forwardings["mc_to_tg"] is True and info.player:
        await send_to_group(f"{info.player}:\n{info.content}", entities=[MessageEntity("bold", 0, len(info.player) + 1)])

async def on_player_joined(server: PluginServerInterface, player: str, info: Info):
    message = f"{player} 加入了游戏。"
    await send_to_group(message, entities=[MessageEntity("italic", 0, len(player)), MessageEntity("bold", 0, len(message))])

async def on_player_left(server: PluginServerInterface, player: str):
    message = f"{player} 离开了游戏。"
    await send_to_group(message, entities=[MessageEntity("italic", 0, len(player)), MessageEntity("bold", 0, len(message))])

async def on_message(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE):
    if event.message is None: return
    content = event.message.text
    if content is None: return
    event_type = parse_event_type(event)
    logger.debug(f"Update 数据：\n{event}")
    
    typ = get_type(event)
    # 防止自己的机器人被别人拉去用还越权
    match (typ):
        case ChatType.PRIVATE:
            if str(get_id(event)) not in config.admins: return
        case ChatType.GROUP:
            if str(get_id(event)) not in config.admins and event.message.chat.id != config.group: return
        case _:
            return
    
    # 普通信息
    if config.forwardings["tg_to_mc"] is True and typ == ChatType.GROUP:
        id: str = str(get_id(event))
        name: str = f"§a<{bindings[id]}>§7" if id in bindings else f"§4<{event.message.chat.first_name} ({id})>§7"
        server.say(f"§7[TG] {name}: {content}")

    # 封禁列表，不作应答
    if get_id(event) in ban_list:
        server.logger.debug(f"用户 {get_id(event)} 已被封禁，拒绝处理其请求")
        return
        
    server.logger.debug(f"正在处理用户 {get_id(event)} 的请求……")
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
    await send_to_group(msg, entities=[MessageEntity("bold", 0, len(player) + 1)])

# TG 命令处理器
async def tg_command_list(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, *args):
    players = online_player_api.get_player_list()

    players_count = len(players)
    message = f"服务器目前有 {players_count} 个玩家在线~"
    if players_count:
        message += f"\n=== 玩家列表 ===\n"
        for player in players: message += f"{player}\n"

    await send_to(event, context, message)

async def tg_command_mc(
        server: PluginServerInterface,
        event: Update,
        context: ContextTypes.DEFAULT_TYPE,
        command: List[str],
        event_type: MessageType
):

    id = str(get_id(event))
    if id in bindings.keys() and id in config.admins:
        server.say(f"§2[TG] §a<{bindings[id]}>§7 {command[0]}")
    else:
        server.say(f"§7[TG] §a<{bindings[id]}>§7 {command[0]}")

async def tg_command_bind_user(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    player = command[0]
    user_id = str(get_id(event))

    if user_id in bindings.keys():
        value = bindings[user_id]
        await send_to(
            event,
            context,
            f"你已经绑定了 \"{value}\"，请找管理员修改！"
        )
        return
    if config.whitelist["verify_player"] is True:
        try:
            # 检查玩家档案是否存在
            response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player}", timeout=10)
            if not response.ok:
                await send_to(
                    event,
                    context,
                    f"无法获取玩家 \"{player}\" 的资料信息，请检查是否输入了一个离线玩家名或者不存在的玩家名！\n详细错误信息：{response.json().get('errorMessage')}"
                )
                return
        except requests.exceptions.Timeout:
            await send_to(
                event,
                context,
                f"获取玩家档案超时，请重试。"
            )
            return

    bindings[user_id] = player
    await send_to(
        event,
        context,
        f"成功绑定到 \"{player}\""
    )
    save_data(server)
    if config.whitelist["add_when_bind"] is True:
        await add_to_whitelist(server, event, context, player)

async def tg_command_bind_admin(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                          event_type: MessageType):
    if event_type == MessageType.ADMIN:
        id: str = command[0]
        player: str = command[1]

        if id in bindings:
            await tg_command_bind_unbind(server, event, context, [id], event_type)
        bindings[id] = player
        await send_to(
            event,
            context,
            f"成功将 Telegram 账号: {id} 绑定到 \"{player}\""
        )
        save_data(server)
        if config.whitelist["add_when_bind"] is True:
            await add_to_whitelist(server, event, context, player)

async def tg_command_bind_unbind(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                           event_type: MessageType):
    if event_type == MessageType.ADMIN:
        id: str = command[0]
        if id in bindings:
            player: str = bindings[id]
            del bindings[id]
            save_data(server)
            await send_to(
                event,
                context,
                f"成功解除 Telegram 账号: {id} 对 \"{player}\" 的绑定！"
            )
            if config.whitelist["add_when_bind"] is True:
                await remove_from_whitelist(server, event, context, player)

async def tg_command_bind_query(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                          event_type: MessageType):
    if event_type == MessageType.ADMIN:
        typ: str = command[0]
        value: str = command[1]
        match typ:
            case "TG":
                result = None
                if value in bindings:
                    result = bindings[value]

                if result is None:
                    await send_to(
                        event,
                        context,
                        f"没有查询到结果！"
                    )
                    return
                await send_to(
                    event,
                    context,
                    f"查询到如下结果：\nTelegram: {value} 绑定的是 \"{result}\""
                )
            case "ID":
                result = None
                if value in bindings.values():
                    result = [k for k, v in bindings.items() if v == value]

                if result is None:
                    await send_to(
                        event,
                        context,
                        f"没有查询到结果！"
                    )
                    return
                await send_to(
                    event,
                    context,
                    f"查询到如下结果：\n{'\n'.join(map(str, [f'Telegram: {key} 绑定的是 \"{value}\"' for key in result]))}"
                )

async def tg_command_whitelist_add(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                             event_type: MessageType):
    if event_type == MessageType.ADMIN:
        await add_to_whitelist(server, event, context, command[0])

async def tg_command_whitelist_remove(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                             event_type: MessageType):
    if event_type == MessageType.ADMIN:
        await remove_from_whitelist(server, event, context, command[0])

async def tg_command_command(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    cmd = command[0]
    if event_type == MessageType.ADMIN:
        await execute(server, event, context, cmd)

async def tg_command_info(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    if event_type == MessageType.ADMIN and event.message and get_type(event) == ChatType.PRIVATE:
        await send_to(
            event,
            context,
            get_system_info()
        )

async def tg_command_reload(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                      event_type: MessageType):
    if event_type == MessageType.ADMIN:
        await send_to(
            event,
            context,
            f"收到，在 2 秒后重载……"
        )
        time.sleep(2)
        server.reload_plugin("telegram_chat")

async def tg_command_ping(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    if event.message is None: raise Exception("event.message is none")
    delay = max((time.time() - event.message.date.timestamp()) * 1000, 0)
    await send_to(
        event,
        context,
        f"Pong！服务在线，延迟 {delay:.2f}ms。"
    )

async def tg_command_bot_ban(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                       event_type: MessageType):
    id = command[0]
    if id not in ban_list and event_type == MessageType.ADMIN:
        ban_list.append(int(id))
        await send_to(
            event,
            context,
            f"成功封禁 Telegram 账号: {id}"
        )
        save_data(server)

async def tg_command_bot_pardon(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                          event_type: MessageType):
    id = command[0]
    if id in ban_list and event_type == MessageType.ADMIN:
        ban_list.remove(id)
        await send_to(
            event,
            context,
            f"成功解封 Telegram 账号: {id}"
        )
        save_data(server)

async def tg_command_help(server, event, context, command, type):
    await send_to(event, context, Help.admin) if type == MessageType.ADMIN else await send_to(event, context, Help.user)

def tg_command_ban(server, event, context, command, event_type):
    execute(server, event, context, f"ban {command[0]}") if event_type == MessageType.ADMIN else None

def tg_command_pardon(server, event, context, command, event_type):
    execute(server, event, context, f"pardon {command[0]}") if event_type == MessageType.ADMIN else None