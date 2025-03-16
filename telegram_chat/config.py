from mcdreforged.api.utils import Serializable
from typing import Any, Dict, List

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

instance: Config = Config()
bindings: dict[str, str]
ban_list: List[int] = []
online_player_api: Any = None