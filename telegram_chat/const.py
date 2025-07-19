VERSION = (2, 0, 4)
VERSION_STR = '.'.join(map(str, VERSION))

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
- /save 保存 Bot 配置文件
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