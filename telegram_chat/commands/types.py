from enum import Enum

class MessageType(Enum):
    USER = 0
    ADMIN = 1

class ChatType(Enum):
    PRIVATE = 0
    GROUP = SUPERGROUP = 1
    OTHER = 2