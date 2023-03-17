from enum import Enum
from .. import codes

class MessageType(Enum):
    """
    This is enumeration of message types.
    """
    TEXT = 1
    IMAGE = 2
    FILE = 3
    
class Message():
    def __init__(self, type:MessageType, body=None, channel:str='', to:list=[], sender:str='', recipient_count:int=0,
                 id:str='', origin:str='Bot', raw=None) -> None:
        self.type = type
        self.body = body
        self.channel = channel
        self.to = to
        self.sender = sender
        self.recipient_count = recipient_count
        self.id = id
        self.origin = origin
        self.raw = raw

def message_from_raw(raw_data:dict) -> Message:
    code = raw_data['code']
    if code < codes.MESSAGE_DOWN_TEXT or code > codes.MESSAGE_DOWN_FILE:
        raise Exception('Analysed raw message unsupported: {}'.format(raw_data))
    
    type = None
    if code == codes.MESSAGE_DOWN_TEXT:
        type = MessageType.TEXT
    elif code == codes.MESSAGE_DOWN_IMAGE:
        type = MessageType.IMAGE
    else:
        type = MessageType.FILE

    ret = Message(type=type, body=raw_data['extra']['msg_body'], channel=raw_data['extra']['channel_id'],
                    sender=raw_data['extra']['from_user_id'], recipient_count=raw_data['extra']['n_recipients'],
                    id=raw_data['extra']['msg_id'], origin=raw_data['extra']['origin'], raw=raw_data)

    return ret