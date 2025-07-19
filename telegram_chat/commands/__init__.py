import re
from enum import Enum

from .. import const, tools
from ..command_builder import CommandBuilder
from . import bind, game, other, user, whitelist
from .types import ChatType, MessageType

# 实用函数
def register_commands():
    """
    注册命令树
    """
    def run_command(command, need_admin: bool = False):
        async def _run(server, event, context, _, type):
            if not need_admin or type == MessageType.ADMIN:
                await tools.execute(server, event, context, command)
        return _run
    
    command_tree = CommandBuilder()
    # /mc
    command_tree.add_command(re.compile(r'/mc (.*)'), [str], game.mc)

    # /list
    command_tree.add_command("/list", None, game.list)

    #/bind
    command_tree.add_command("/bind", None, lambda srv, evt, ctx, cmd, typ: tools.send_to(evt, ctx, const.Help.bind))
    command_tree.add_command(re.compile(r'/bind unbind (\d*)'), [str], bind.bind_unbind)
    command_tree.add_command(re.compile(r'/bind query (TG|ID) (\w*)'), [str, str], bind.bind_query)
    command_tree.add_command(re.compile(r'/bind (\d*) (\w*)'), [str, str], bind.bind_admin)
    command_tree.add_command(re.compile(r'/bind (\w*)'), [str], bind.bind_user)

    # /whitelist
    command_tree.add_command("/whitelist", None, lambda srv, evt, ctx, cmd, typ: tools.send_to(evt, ctx, const.Help.whitelist))
    command_tree.add_command("/whitelist list", None, run_command("whitelist list", True))
    command_tree.add_command("/whitelist reload", None, run_command("whitelist reload", True))
    command_tree.add_command("/whitelist on", None, run_command("whitelist on", True))
    command_tree.add_command("/whitelist off", None, run_command("whitelist off", True))
    command_tree.add_command(re.compile(r'/whitelist add (\w*)'), [str], whitelist.whitelist_add)
    command_tree.add_command(re.compile(r'/whitelist remove (\w*)'), [str], whitelist.whitelist_remove)

    # command
    command_tree.add_command(re.compile(r'/command (.*)'), [str], game.command)

    # /help
    command_tree.add_command("/help", None, other.help)
    
    # /ping
    command_tree.add_command("/ping", None, other.ping)
    
    # /start /stop /restart 
    command_tree.add_command("/start", None, lambda srv, evt, ctx, cmd, typ: srv.start() if typ == MessageType.ADMIN else None)
    command_tree.add_command("/stop", None, lambda srv, evt, ctx, cmd, typ: srv.stop() if typ == MessageType.ADMIN else None)
    command_tree.add_command("/restart", None, lambda srv, evt, ctx, cmd, typ: srv.restart() if typ == MessageType.ADMIN else None)
    
    # /info
    command_tree.add_command("/info", None, other.info)
    
    # /reload
    command_tree.add_command("/reload", None, other.reload)
    
    # /ban /pardon
    command_tree.add_command(re.compile(r'/ban (\d*)'), [int], user.ban)
    command_tree.add_command(re.compile(r'/pardon (\d*)'), [int], user.pardon)
    
    # /bot-
    command_tree.add_command(re.compile(r'/bot-ban (\d*)'), [int], user.bot_ban)
    command_tree.add_command(re.compile(r'/bot-pardon (\d*)'), [int], user.bot_pardon)
    
    # /save
    command_tree.add_command("/save", None, other.save)
    
    return command_tree