from mcdreforged.api.command import CommandContext
from mcdreforged.api.types import CommandSource, PluginServerInterface

from telegram import Update
from telegram.ext import ContextTypes

from . import ChatType, MessageType, bot, config, logger

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
    config.instance = server.load_config_simple(target_class=Config) # type: ignore
    config.bindings = server.load_config_simple(
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
            "data": config.bindings,
        },
        "bindings.json"
    )
    server.save_config_simple(
        {
            "data": config.ban_list,
        },
        "ban_list.json"
    )

async def send_to_group(msg: str, **kwargs):
    """
    向所有群聊广播
    """
    await bot.bot.send_message(chat_id=config.instance.group, text=msg, **kwargs)
        
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
    return MessageType.ADMIN if str(get_id(event)) in config.instance.admins else MessageType.USER

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