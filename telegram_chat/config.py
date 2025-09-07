from mcdreforged.api.utils import Serializable
from typing import Any, Dict, List
import logging
from .telegram_manager import TelegramBot
from mcdreforged.api.types import PluginServerInterface

class Config(Serializable):
    admins: List[str] = []
    group: int = 0

    forwardings: Dict[str, bool] = {
        "tg_to_mc": True,
        "mc_to_tg": True,
    }
    
    telegram: Dict[str, Any] = {
        "token": None,
        "api": None,
        "startup_timeout": 60,
    }
    
    whitelist: Dict[str, Any] = {
        "add_when_bind": True,
        "verify_player": True
    }

class ConfigManager:
    config: Config = Config()
    bindings: dict[str, str] = {}
    ban_list: List[int] = []
    online_player_api: Any = None # type: ignore
    bot: TelegramBot = None # type: ignore
    logger: logging.Logger = None # type: ignore

    @staticmethod
    def load_data(server: PluginServerInterface):
        ConfigManager.config = server.load_config_simple(target_class=Config) # type: ignore
        ConfigManager.bindings = server.load_config_simple(
            "bindings.json",
            default_config={"data": {}},
            echo_in_console=False
        )["data"]
        ConfigManager.ban_list = server.load_config_simple(
            "ban_list.json",
            default_config={"data": []},
            echo_in_console=False
        )["data"]

    @staticmethod
    def save_data(server: PluginServerInterface):
        """
        保存数据
        """
        server.save_config_simple(
            {
                "data": ConfigManager.bindings,
            },
            "bindings.json"
        )
        server.save_config_simple(
            {
                "data": ConfigManager.ban_list,
            },
            "ban_list.json"
        )