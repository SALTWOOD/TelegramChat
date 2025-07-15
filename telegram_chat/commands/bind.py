import requests
from typing import List

from mcdreforged.api.types import PluginServerInterface

from telegram import Update
from telegram.ext import ContextTypes

from .. import tools
from ..config import *
from .types import MessageType

async def bind_admin(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                          event_type: MessageType):
    if event_type == MessageType.ADMIN:
        id: str = command[0]
        player: str = command[1]

        if id in bindings:
            await bind_unbind(server, event, context, [id], event_type)
        bindings[id] = player
        await tools.send_to(
            event,
            context,
            f"成功将 Telegram 账号: {id} 绑定到 \"{player}\""
        )
        tools.save_data(server)
        if config.whitelist["add_when_bind"] is True:
            await tools.add_to_whitelist(server, event, context, player)

async def bind_user(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    player = command[0]
    user_id = str(tools.get_id(event))

    if user_id in bindings.keys():
        value = bindings[user_id]
        await tools.send_to(
            event,
            context,
            f"你已经绑定了 \"{value}\"，请联系管理员修改！"
        )
        return
    if config.whitelist["verify_player"] is True:
        try:
            # 检查玩家档案是否存在
            response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player}", timeout=10)
            if not response.ok:
                await tools.send_to(
                    event,
                    context,
                    f"无法获取玩家 \"{player}\" 的资料信息，请检查是否输入了一个离线玩家名或者不存在的玩家名！\n详细错误信息：{response.json().get('errorMessage')}"
                )
                return
        except requests.exceptions.Timeout:
            await tools.send_to(
                event,
                context,
                f"获取玩家档案超时，请重试。"
            )
            return

    bindings[user_id] = player
    await tools.send_to(
        event,
        context,
        f"成功绑定到 \"{player}\""
    )
    tools.save_data(server)
    if config.whitelist["add_when_bind"] is True:
        await tools.add_to_whitelist(server, event, context, player)

async def bind_unbind(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                           event_type: MessageType):
    if event_type == MessageType.ADMIN:
        id: str = command[0]
        if id in bindings:
            player: str = bindings[id]
            del bindings[id]
            tools.save_data(server)
            await tools.send_to(
                event,
                context,
                f"成功解除 Telegram 账号: {id} 对 \"{player}\" 的绑定！"
            )
            if config.whitelist["add_when_bind"] is True:
                await tools.remove_from_whitelist(server, event, context, player)

async def bind_query(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                          event_type: MessageType):
    """
    查询 Minecraft 玩家与 Telegram 账号的绑定关系
    """
    if event_type == MessageType.ADMIN:
        typ: str = command[0]
        value: str = command[1]
        match typ:
            case "TG":
                result = None
                if value in bindings:
                    result = bindings[value]

                if result is None:
                    await tools.send_to(
                        event,
                        context,
                        f"没有查询到结果！"
                    )
                    return
                await tools.send_to(
                    event,
                    context,
                    f"查询到如下结果：\nTelegram: {value} 绑定的是 \"{result}\""
                )
            case "ID":
                result = None
                if value in bindings.values():
                    result = [k for k, v in bindings.items() if v == value]

                if result is None:
                    await tools.send_to(
                        event,
                        context,
                        f"没有查询到结果！"
                    )
                    return
                await tools.send_to(
                    event,
                    context,
                    f"查询到如下结果：\n{'\n'.join(map(str, [f'Telegram: {key} 绑定的是 \"{value}\"' for key in result]))}"
                )