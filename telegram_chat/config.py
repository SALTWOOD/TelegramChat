from mcdreforged.api.utils import Serializable
from typing import Any, Dict, List

class Config(Serializable):
    admins: List[str] = []
    group: int = 0

    forwardings: Dict[str, bool] = {
        "tg_to_mc": True,
        "mc_to_tg": True,
    }
    
    telegram: Dict[str, Any] = {
        "token": None,
        "api": None
    }
    
    whitelist: Dict[str, Any] = {
        "add_when_bind": True,
        "verify_player": True
    }

instance: Config = Config()
bindings: dict[str, str]
ban_list: List[int] = []
online_player_api: Any = None