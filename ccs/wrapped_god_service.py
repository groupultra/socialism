from .base_god_service import BaseGodService
from .wrapped_goddess_db_agent import WrappedGoddessDBAgent
import rel


class WrappedGodService(BaseGodService):
    """
        This is the wrapped God service.
        CCS provides a various of features for users in corresponding channels to use.
    """

    def __init__(self, name='WrappedGodService'):
        super().__init__()
        self.agent = WrappedGoddessDBAgent(name+".json")
        self.uri = None
        self.name = 'WrappedGodService'
        self.feature_commands = []

        self.basic_command_func_map = {}
        self.notice_func_map = {}
        self.feature_func_map = {}

        self.prompt = {}

        self.message_func_map = {}
        
        self.temp_msg_map = {}

    def on_open(self, ws):
        """
            Default behavior "on_open" for websocket.
            You can override this method to customize your own behavior.
            Also applies to "on_message", "on_error" and "on_close".
        """
        data = {'code': self.codes.COPERATION_GOD_RECONNECT, 'extra': {
            'user_id': self.user_id, 'password': self.password}}
        print('SocialGodService send query: run: ', data)
        self._send_ccs_operation(data, ws, None)
        print(self.name, 'opened')

    def add_feature(self, name, code, prompts, func=None):
        """
            Add a feature to the service.
            Every feature contains a name, a code and a prompt.
            The code is always a five-digited int, and the first number must be 9, like 90001.
            The prompt here will be replaced by "params" in the future.
            Now it's the string that shows to the user in the input bar.
            You do not need to specify a handler func to the feature, but it's recommended to do so.
            If one feature with no handler is triggered, an exception will be raised.
            You can use set_feature_handle to set a handler for a feature.
        """
        self.feature_commands.append(
            {'name': name, 'code': code, 'prompts': [prompts] if prompts else []})
        self.prompt[code] = prompts
        if func:
            self.feature_func_map[code] = func

    def remove_feature(self, code):
        """
            Remove a feature from the service.
            The feature is specified by its code.
        """
        self.feature_commands = list(
            filter(lambda x: x['code'] != code, self.feature_commands))
        self.feature_func_map.pop(code, None)

    def set_basic_command_handle(self, code, func):
        """
            Set a handler for a basic command.
            The command is specified by its code.
            Some commands will be like "help", "quit".
        """
        self.basic_command_func_map[code] = func

    def set_notice_handle(self, code, func):
        """
            Set a handler for a notice.
            The notice is specified by its code.
            Some notices will be like "user joined the channel", "user left the channel".
        """
        self.notice_func_map[code] = func

    def set_feature_handle(self, code, func):
        """
            Set a handler for a feature.
            The feature is specified by its code.
        """
        self.feature_func_map[code] = func

    def set_message_handle(self, code, func):
        """
            Set a handler for a message.
            This code is always MESSAGE_TO_CCS.
        """
        self.message_func_map[code] = func

    def _handle_data_dict(self, data, ws):
        print(
            f'WrappedGodService: _handle_data_dict received {data} at websocket {ws}')
        if data['code'] == self.codes.MESSAGE_TO_CCS:
            try:
                self._handle_message_to_ccs(data, ws, self.path)
            except Exception as e:
                print('WrappedGodService: _handle_message_to_ccs error: ', e)
        elif data['code'] == self.codes.COMMAND_TO_CCS:
            try:
                self._handle_command_to_ccs(data, ws, self.path)
            except Exception as e:
                print('WrappedGodService: _handle_command_to_ccs error: ', e)
        else:
            raise Exception('no handler for code', data['code'])

    def _handle_message_to_ccs(self, data, ws, path):
        type_code = data['extra']['type_code']
        if type_code in self.message_func_map:
            self.message_func_map[type_code](self, data, ws, path)
        else:
            raise Exception('no message function for code', type_code)

    def _handle_command_to_ccs(self, data, ws, path):
        type_code = data['extra']['type_code']
        if 20000 <= type_code <= 29999:
            self._handle_basic_command(data, ws, path)
        elif 80000 <= type_code <= 89999:
            self._handle_notice(data, ws, path)
        elif 90000 <= type_code <= 99999:
            self._handle_feature(data, ws, path)
        else:
            raise Exception('no command function for code', type_code)

    def _handle_basic_command(self, data, ws, path):
        type_code = data['extra']['type_code']
        if type_code in self.basic_command_func_map:
            self.basic_command_func_map[type_code](self, data, ws, path)
        else:
            raise Exception('no basic command function for code', type_code)

    def _handle_notice(self, data, ws, path):
        type_code = data['extra']['type_code']
        if type_code in self.notice_func_map:
            self.notice_func_map[type_code](self, data, ws, path)
        else:
            raise Exception('no notice function for code', type_code)

    def _handle_feature(self, data, ws, path):
        type_code = data['extra']['type_code']
        if type_code in self.feature_func_map:
            self.feature_func_map[type_code](self, data, ws, path)
        else:
            raise Exception('no feature function for code', type_code)

    def _send_ccs_operation(self, data, ws, path):
        print('WrappedGodService ccs_operation: ', data)
        code = data['code']
        password = data['extra']['password']
        user_id = data['extra']['user_id']
        if code == self.codes.COPERATION_GOD_RECONNECT:
            self._send_data_to_ws(
                ws, self.codes.COPERATION_GOD_RECONNECT, user_id=user_id, password=password)
        else:
            raise Exception('no ccs operation for code', code)

    def _send_command_down(self, ws, type_code, **kwargs):
        self._send_data_to_ws(ws, self.codes.COMMAND_FROM_CCS,
                              type_code=type_code, **kwargs)

    def _send_message_down(self, ws, type_code, channel_id, to_user_ids, origin, **kwargs):
        self._send_data_to_ws(ws, self.codes.MESSAGE_FROM_CCS,
                              type_code=type_code, channel_id=channel_id, to_user_ids=to_user_ids,
                              origin=origin, **kwargs)

    def broadcast_command_text(self, data, ws, text, clear=False):
        """
            Broadcast a text to all users in a channel.
        """
        channel_id = data['extra']['channel_id']
        self._send_command_down(
            ws,
            self.codes.COMMAND_DOWN_DISPLAY_TEXT,
            channel_id=channel_id,
            to_user_ids=self.agent.get_channel_user_list(channel_id),
            args={'text': text, 'clear': clear}
        )

    def broadcast_command_image(self, data, ws, url):
        """
            Broadcast an image to all users in a channel.
        """
        channel_id = data['extra']['channel_id']
        self._send_command_down(
            ws,
            self.codes.COMMAND_DOWN_DISPLAY_IMAGE,
            channel_id=channel_id,
            to_user_ids=self.agent.get_channel_user_list(channel_id),
            args={
                'type': 'url',
                'image': url
            }
        )

    def reply_command_text(self, data, ws, text, clear=False):
        """
            Reply a text to a single user.
        """
        self._send_command_down(
            ws,
            self.codes.COMMAND_DOWN_DISPLAY_TEXT,
            channel_id=data['extra']['channel_id'],
            to_user_ids=[data['extra']['user_id']],
            args={'text': text, 'clear': clear}
        )

    def reply_command_image(self, data, ws, url):
        """
            Reply an image to a single user.
        """
        self._send_command_down(
            ws,
            self.codes.COMMAND_DOWN_DISPLAY_IMAGE,
            channel_id=data['extra']['channel_id'],
            to_user_ids=[data['extra']['user_id']],
            args={'type': 'url',  'image': url}
        )

    def whistle_sender_command_text(
        self, data, ws, *,
        text_to_sender, text_to_others,
        clear_sender=False, clear_others=False
    ):
        """
            Dog whistle.
        """
        channel_id = data['extra']['channel_id']
        # to sender
        self._send_command_down(
            ws,
            self.codes.COMMAND_DOWN_DISPLAY_TEXT,
            channel_id=channel_id,
            to_user_ids=[data['extra']['user_id']],
            args={'text': text_to_sender, 'clear': clear_sender}
        )
        # to others
        self._send_command_down(
            ws,
            self.codes.COMMAND_DOWN_DISPLAY_TEXT,
            channel_id=channel_id,
            to_user_ids=list(set(self.agent.get_channel_user_list(
                channel_id)) - {data['extra']['user_id']}),
            args={'text': text_to_others, 'clear': clear_others}
        )

    def set_account(self, user_id, password):
        """
            Set the account for the service.
            Fetch these in CH0000.
        """
        self.user_id = user_id
        self.password = password

    def run(self):
        """
            Run the service.
        """
        uri = 'wss://frog.4fun.chat/social' if self.uri is None else self.uri
        ws = self.create_connection(
            uri, self.on_open, self.on_message, self.on_error, self.on_close)

        rel.signal(2, rel.abort)  # Keyboard Interrupt, one for all connections
        rel.dispatch()


def handle_fetch_command(self, data, ws, path):
    """
        A function that handles the "fetch command" notice.
        This can be the default behavior.
    """
    channel_id = data['extra']['channel_id']
    user_id = data['extra']['user_id']
    self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CCS_COMMAND_LIST,
                            channel_id=channel_id, to_user_ids=[user_id], commands=self.feature_commands)


def handle_fetch_user_list(self, data, ws, path):
    """
        A function that handles the "fetch user list" notice.
        This can be the default behavior.
    """
    channel_id = data['extra']['channel_id']
    user_id = data['extra']['user_id']
    self.agent.join_channel(channel_id, user_id)
    user_ids = self.agent.get_channel_user_list(channel_id)
    self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CHANNEL_USER_LIST,
                            channel_id=channel_id, to_user_ids=user_ids, user_ids=user_ids)


def handle_fetch_recipient_list(self, data, ws, path):
    pass


def handle_receive_user_list(self, data, ws, path):
    """
        A function that handles the "get user list" notice.
        This can be the default behavior.
    """
    channel_id = data['extra']['channel_id']
    user_ids = data['extra']['user_ids']
    self.agent.init_user_id_list(channel_id, user_ids)


def handle_join(self, data, ws, path):
    """
        A function that handles the "user join" notice.
        This can be the default behavior.
    """
    channel_id = data['extra']['channel_id']
    user_id = data['extra']['user_id']
    self.agent.join_channel(channel_id, user_id)
    user_ids = self.agent.get_channel_user_list(channel_id)
    self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CHANNEL_USER_LIST,
                            channel_id=channel_id, to_user_ids=user_ids, user_ids=user_ids)
    self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CCS_COMMAND_LIST,
                            channel_id=channel_id, to_user_ids=[user_id], commands=self.feature_commands)


def handle_left(self, data, ws, path):
    """
        A function that handles the "user leave" notice.
        This can be the default behavior.
    """
    channel_id = data['extra']['channel_id']
    user_id = data['extra']['user_id']
    self.agent.leave_channel(channel_id, user_id)
    user_ids = self.agent.get_channel_user_list(channel_id)
    self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CHANNEL_USER_LIST,
                            channel_id=channel_id, to_user_ids=user_ids, user_ids=user_ids)


def handle_notice_take_over(self, data, ws, path):
    """
        A function that handles the "take over channel" notice.
        This can be the default behavior.
    """
    print("NOTICE_TAKE_OVER\n", data)
    target_channel_id = data['extra']['target_channel_id']
    # target_channel_name = data['extra']['target_channel_name']
    user_ids = data["extra"]["target_user_ids"]
    self.agent.init_user_id_list(target_channel_id, user_ids)
    self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CHANNEL_USER_LIST,
                            channel_id=target_channel_id, to_user_ids=user_ids, user_ids=user_ids)
    self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CCS_COMMAND_LIST,
                            channel_id=target_channel_id, to_user_ids=user_ids, user_ids=user_ids, commands=self.feature_commands)


def handle_notice_release(self, data, ws, path):
    """
        A function that handles the "release channel" notice.
        This can be the default behavior.
    """
    # target_channel_id = data['extra']['target_channel_id']
    # target_user_ids = data['extra']['target_user_ids']
    print("NOTICE_RELEASE")

def handle_message(self, data, ws, path):
    """
        A function that handles message to ccs.
        This can be the default behavior.
        When a message is sent, CCS will receive a response
        //TODO: describe later things, like what response and whistle parts
        def _send_message_down(self, ws, type_code, channel_id, to_user_ids, origin, **kwargs):
    """
    self._send_message_down(ws, data['extra']['type_code'], data['extra']['channel_id'], data['extra']['to_user_ids'],
                            data['extra']['origins'])
    self.temp_msg_map[data['extra']['temp_msg_id']] = data['extra']['to_user_ids']
