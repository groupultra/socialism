import websocket
import rel
from enum import Enum
from .. import codes

import json, traceback, datetime
from .message import Message, MessageType, message_from_raw

class JSONSocketUser:
    """
    This is basic class of socket client user, which 
    implements fundamental interfaces that you can 
    reach as a user.
    We wraps the message data into a Message object.
    For better performance(not indeed), you could set
    `pre_analyse` to be `False` to get raw data of message(dict).
    """

    def __init__(self, path:str=None, reconnect:int=None, pre_analyse:bool=True) -> None:
        self.path = path if path else 'wss://frog.4fun.chat/social'
        self.reconnect = reconnect if reconnect else 5
        self.codes = codes
        self.pre_analyse = pre_analyse

        self.create_connection(self.path)
        print('created connection with {}'.format(self.path))
    
    def _create_websocket(self, uri:str, on_open=None, on_message=None, on_error=None, on_close=None):
        """
        Create and return a websocket connection object

        Args:
            uri : str
                Location of server this user connects.

            on_open : function : optional
                Callback function execute when websocket connection is created.
                
            on_message : function : optional
                Callback function execute when receive message from websocket connection.
            
            on_error : function : optional
                Callback function execute when error occurs on websocket connection.

            on_close : function : optional
                Callback function execute when websocket connectoin breaks or closes.

        Return:
            Return the websocket object that is created when called.
            
        """
        print('create_websocket!')
        ws = websocket.WebSocketApp(
            uri,
            on_open=on_open or self.on_open,
            on_message=on_message or self.on_message,
            on_error=on_error or self.on_error,
            on_close=on_close or self.on_close
        )
        return ws
    
    def create_connection(self, uri: str, on_open=None, on_message=None, on_error=None, on_close=None):
        """
        Initialize websocket connection between this user object itself and given server

        Args:
            Args:
            uri : str
                Location of server this user connects.

            on_open : function : optional
                Callback function execute when websocket connection is created.
                
            on_message : function : optional
                Callback function execute when receive message from websocket connection.
            
            on_error : function : optional
                Callback function execute when error occurs on websocket connection.

            on_close : function : optional
                Callback function execute when websocket connectoin breaks or closes.
        """
        self.ws = self._create_websocket(uri, on_open, on_message, on_error, on_close)
        self.ws.run_forever(dispatcher=rel, reconnect=self.reconnect)

    def on_message(self, ws, message):
        """
        Default callback when receive message from websocket connectoin.
        Don't override this function if you can't figure out what you would
        face to do so!

        Args:
            ws : websocket.WebSocketApp
                Connection object.
            
            message : str
                Message Object in utf-8 received from websocket connection.

        """
        print(f'JSONSocketUser.message: {message}')
        self._safe_handle(ws, message)

    def on_error(self, ws, error):
        """
        Default callback execute when error occurs on connection.
        As default, it would only print error instead of raise an
        exception.
        Args:
            ws : websocket.WebSocketApp
                Connection object.
            
            error : exception object
                Object contains full information of the error.
            
        """
        print(f'JSONSocketUser.error: {error}')
    
    def on_close(self, ws, close_status_code, close_msg):
        """
        Default callback execute when connection is closed.
        As default, it would only print closure information.

        Args:
            ws : websocket.WebSocketApp
                Connection object

            close_status_code : str
                Status code of closure, more details refer to `https://websocket-client.readthedocs.io/en/latest`
        
            close_msg : str
                Information of closure.
            
        """
        print(f'JSONSocketUser.close: {ws} closed with status code {close_status_code} and message {close_msg}')

    def on_open(self, ws):
        """
        Callback that is called when connection is open.
        As default it will only print message that bot opens.
        Args:
            ws : websocket.WebSocketApp
                Connection object. 
        
        """
        print('JSONSocketUser.open')
        
    @staticmethod
    def _make_data_dict(code:int, **extra_args) -> object:
        """
        Format given params to meet that social server need.

        Args:
            code : int
                Type code of this message, more details refer to `/codes.md`
            **extra_args : key-value pair of params : optional
                Other params to carry with message. all of these will be wrapped
                in `extra` segment of return value.

        Return:
            Wrapped object of all given params.
        """
        return {
            'code': code,
            'extra': extra_args
        }
    
    def _send_data_to_ws(self, ws, code:int, **extra_args):
        """
        Warp and format given params then send with websocket connection.

        Args:
            ws : websocket.WebSocketApp
                Connection object.
            code : int 
                Type code of the message, which decides how it will work
            **extra_args : key-value pair of params : optional
                Other params to carry with message. all of these will be wrapped
                in `extra` segment of return value.

        """
        data_dict = self._make_data_dict(code=code, **extra_args)
        self._safe_send(ws, data_dict)

    def _safe_send(self, ws, data:dict):
        """
        Send wrapped data making sure of data safety. The `safety` emphasizes data format 
        instead of connection or privacy!

        Args:
            ws : websocket.WebSocketApp
                Connection object.
            
            data : dict
                Wrapped data object in format of that in `/code.md`. 
        
        """
        try:
            if isinstance(data, dict):
                data = json.dumps(data)
            else:
                pass

            ws.send(data)
            return True
        except websocket.WebSocketConnectionClosedException as e:
            print('Bot: _safe_send: Connection Closed Exception', e)

        except Exception as e:
            traceback.print_exc()
            print('Bot: self._safe_send: Exception Occurs', e)

    def _safe_handle(self, ws, message:str):
        """
        Load object from message (that in type of jstr) and distribute it
        to matching handler.
        It will time for each message from received to fully processed. 
        Args:
            ws : websocket.WebSocketApp
                Connection object.
            message : json string
                Message received from websocket.

        """
        ct = datetime.datetime.now()
        print('before social bot _safe_handle current time:- ', ct)

        try:
            data = json.loads(message)
            ct = datetime.datetime.now()
            self._handle_data_dict(ws, data)

        except ValueError as e:
            print(f'Bot: _safe_handle received non-json message: {message}')

        except Exception as e:
            print('Bot: Server function error!', e)
            traceback.print_exc()
        
        ct = datetime.datetime.now()
        print('after social bot _safe_handle current time:- ', ct)
    
    def _handle_data_dict(self, ws, data:dict):
        """
        Distribute message to matching handler by type code.
        
        Args:
            ws : websocket.WebSocketApp
                Connection object.
            data : dict
                Message object received from connection.
        
        """
        code = data['code']

        if code >= 40000 and code < 50000:
            self.on_receive_command(data)
        elif code >= 50000 and code < 60000:
            self.on_receive_message(message_from_raw(data) if self.pre_analyse else data)
        elif code >= 60000 and code < 70000:
            self.on_receive_status(data)
        else:
            self.on_receive_other(data)
        print(f'Bot default: _handle_data_dict received {data} at websocket {ws}')

    def _command_register(self, email, password):
        """
        Fundamental API for user to register.

        Args:
            email : str
                Email for registering an account.
            password : str
                Password for registering an account.
            
        """

        if not self.ws:
            raise Exception('error: register before connection created!')
        
        self._send_data_to_ws(self.ws, self.codes.OPERATION_REGISTER, email=email, password=password)
    
    def _command_reset_password(self, email, password):
        """
        Fundamental API for user to reset password of account.

        Args:
            email : str
                Email of account to reset password.
            password : str
                Original password of the account.
        """

        if not self.ws:
            raise Exception('error: reset password before connection created!')
        
        self._send_data_to_ws(self.ws, self.codes.OPERATION_RESET_PASSWORD, email=email, password=password)

    def _command_login(self, user_id, password):
        """
        Fundamental API for user to login.

        Args:
            user_id : str
                User ID of account to login.
            password : str
                Password of the account.
        """

        if not self.ws:
            raise Exception('error: login before connection created!')
        
        self._send_data_to_ws(self.ws, self.codes.OPERATION_LOGIN, user_id=user_id, password=password)
    
    def _command_logout(self, user_id):
        """
        Fundamental API for user to logout.

        Args:
            user_id : str
                User ID of account to logout.
        """

        if not self.ws:
            raise Exception('error: logout before connection created!')
        
        self._send_data_to_ws(self.ws, self.codes.OPERATION_LOGOUT, user_id=user_id)

    def _command_join_channel(self, user_id, channel_id):
        """
        Fundamental API for user to join a existing channel.
        Will receive error code if trynna join a unexisting channel.

        Args:
            user_id : str
                User ID of account that already logged in.
            channel_id : str
                ID of the channel to join.
        """

        if not self.ws:
            raise Exception('error: join channel before connection created!')
        
        self._send_data_to_ws(self.ws, self.codes.OPERATION_JOIN_CHANNEL, user_id=user_id, channel_id=channel_id)

    def _command_leave_channel(self, user_id, channel_id):
        """
        Fundamental API for user to leave a existing channel that contains current account.
        Will receive error code if trynna leave a channel that doesn't contain you.

        Args:
            user_id : str
                User ID of account that already logged in.
            channel_id : str
                ID of the channel to leave.
        """
        if not self.ws:
            raise Exception('error: leave channel before connection created!')
        
        self._send_data_to_ws(self.ws, self.codes.OPERATION_LEAVE_CHANNEL, user_id=user_id, channel_id=channel_id)

    def _command_fetch_offline_message(self, user_id):
        """
        Fundamental API for user to fetch messages that sent to an account 
        when it's not online.

        Args:
            user_id : str
                User ID of a account that already logged in.
        """

        if not self.ws:
            raise Exception('error: fetch offline message before connection created!')
        
        self._send_data_to_ws(self.ws, self.codes.OPERATION_FETCH_OFFLINE_MESSAGE, user_id=user_id)

    def _command_fetch_user_channels(self, user_id):
        """
        Fundamental API for user to fetch the list of channels that contains this account. 

        Args:
            user_id : str
                User ID of a account that already logged in.
        """

        if not self.ws:
            raise Exception('error: get user channels before connection created!')
        
        self._send_data_to_ws(self.ws, self.codes.OPERATION_GET_USER_CHANNEL_LIST, user_id=user_id)

    def _command_create_channel(self, user_id, channel_id):
        """
        Fundamental API for user to create a new channel. 
        If create with a ID already in use will receive error code.

        Args:
            user_id : str
                User ID of a account that already logged in.
            channel_id : str
                ID of channel to create.
        """

        if not self.ws:
            raise Exception('error: create channel before connection created!')
        
        self._send_data_to_ws(self.ws, self.codes.OPERATION_CREATE_CHANNEL, user_id=user_id, channel_id=channel_id)

    def _command_fetch_channel_user_list(self, user_id, channel_id):
        """
        Fundamental API for user to fetch a list of ussers in a certain channel. 
        Will receive error code if trynna fetch a channel inexists.

        Args:
            user_id : str
                User ID of a account that already logged in.
            channel_id : str
                ID of channel to fetch.
        """

        if not self.ws:
            raise Exception('error: fetch channel user list before connection created!')
        
        self._send_data_to_ws(self.ws, self.codes.COMMAND_UP_FETCH_CHANNEL_USER_LIST, user_id=user_id, channel_id=channel_id)

    def _command_fetch_channel_command_list(self, user_id, channel_id):
        """
        Fundamental API for user to fetch a list of features in a certain channel. 
        Will receive error code if trynna fetch a channel inexists.

        Args:
            user_id : str
                User ID of a account that already logged in.
            channel_id : str
                ID of channel to fetch.
        """

        if not self.ws:
            raise Exception('error: fetch channel command list before connection created!')
        
        self._send_data_to_ws(self.ws, self.codes.COMMAND_UP_FETCH_CCS_COMMAND_LIST, user_id=user_id, channel_id=channel_id)

    def _command_fetch_recipient_list(self, user_id, msg_id):
        """
        Fundamental API for user to fetch a list of recipients of a certain message.
        Will receive error code if trynna fetch a message unexist.
        Args:
            user_id : str
                User ID of a account that already logged in.
            msg_id : str
                ID of message to fetch.
        """

        if not self.ws:
            raise Exception('error: fetch recipient list before connection created!')
        
        self._send_data_to_ws(self.ws, self.codes.COMMAND_UP_FETCH_RECIPIENT_LIST, user_id=user_id, msg_id=msg_id)

    def _command_send_message(self, temp_msg_id, message:Message):
        """
        Wrapped API for sending certain message to certain users in certain channel.

        Args:
            temp_msg_id : str
                Not in use, will be removed in the future.
            message : Message
                Message object that consists of information required for sending.
        """

        if not self.ws:
            raise Exception('error: send message before connection created!')
        
        if message.type == MessageType.TEXT:
            self._send_message_text(message.channel, message.sender, message.to, temp_msg_id, message.body, message.origin)
        else:
            #TODO:
            pass

    def _send_message_text(self, channel_id, from_user_id, to_user_ids, temp_msg_id, msg_body, origin):
        """
        Fundamental API to send message in text.
        
        Args: 
            channel_id : str
                ID of channel to send.
            from_user_id : str
                ID of sender.
            to_user_id : list
                List of recipients.
            temp_msg_id : str
                Not in use, will be removed in the future.
            msg_body : str
                Content of message to send.
            origin : str
                Specifier for bot, server, god and goddess.
        """
        print("Send text message: id-{}, body-{}".format(temp_msg_id, msg_body))
        self._send_data_to_ws(self.ws, self.codes.MESSAGE_UP_TEXT, channel_id=channel_id, from_user_id=from_user_id, to_user_ids=to_user_ids, temp_msg_id=temp_msg_id, msg_body=msg_body, origin=origin)
    
    def on_receive_command(self, data):
        """
        Default callback that is called when receive command from connection.

        Args:
            data : dict
                Object of command.
        
        """
        print(f'Default on_receive_command: {data}')

    def on_receive_message(self, data):
        """
        Default callback that is called when receive message from connection.

        Args:
            data : Message
                Object of message.
        
        """
        print(f'Default on_receive_message: {data}')

    def on_receive_status(self, data):
        """
        Default callback that is called when receive status from connection.

        Args:
            data : dict
                Object of status.
        
        """
        print(f'Default on_receive_status: {data}')

    def on_receive_other(self, data):
        """
        Default callback that is called when receive something that is not command,
        message or status from connection.
        It always indicates error occurs on server end. As default, it will raise an 
        exception when called.
        Args:
            data : dict
                Object of received thing.
        
        """
        raise Exception(f"Error happens, received {data}")

    def run(self):
        """
        Default function to startup a bot.
        Basically it will bind an rel to reconnect when stalled too long.
        Override this if you want to make some change before connection is
        created!
        """
        rel.signal(2, rel.abort)
        print('rel created')
        rel.dispatch()
        print('finished running')

if __name__ == '__main__':
    websocket.enableTrace(True)
    service = JSONSocketUser()
    service.run()

