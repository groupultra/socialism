from commons.base_goddess_service import BaseGoddessService
from goddess_db_agent import GoddessDBAgent

import asyncio
import time
import datetime


class GoddessService(BaseGoddessService):
    """
        This is the wrapped Goddess service.
        CCS provides a various of features for users in corresponding channels to use.
    """

    def __init__(self, port, uri, token, dbfile, name='GoddessService'):
        """
            Args:
                port: The python code should run on this port on your server.
                uri: Starts with "wss://", the websocket uri.
                token: The token you get from social frontend.
                dbfile: For this version, it's a path to a json file. 
        """
        super().__init__(port)
        self.agent = GoddessDBAgent(dbfile)
        self.uri = uri
        self.token = token
        self.name = name
        
        self.feature_commands = []

        self.basic_command_func_map = {
            self.codes.COMMAND_UP_FETCH_CHANNEL_USER_LIST: handle_command_fetch_user_list,
            self.codes.COMMAND_UP_FETCH_RECIPIENT_LIST: handle_command_fetch_recipient_list,
            self.codes.COMMAND_UP_FETCH_CCS_COMMAND_LIST: handle_command_fetch_cmd_list,
        }
        
        self.notice_func_map = {
            self.codes.NOTICE_ASK_AUTH_TOKEN: handle_notice_auth_token,
            self.codes.NOTICE_TAKE_OVER: handle_notice_take_over,
            self.codes.NOTICE_RELEASE: handle_notice_release,
            self.codes.NOTICE_USER_JOINED: handle_notice_user_joined,
        }
        self.feature_func_map = {}

        self.prompt = {}

        self.message_func_map = {
            self.codes.MESSAGE_UP_TEXT: handle_message_up_text,
            self.codes.MESSAGE_UP_IMAGE: handle_message_up_image,
            self.codes.MESSAGE_UP_FILE: handle_message_up_file,
        }


    def add_feature(self, name, code, prompts, func=None):
        """
            Add a feature to the service.
            Every feature contains a name, a code and a prompt.

            Args:
                code: A five-digited int starting with 9, like 90001.
                prompts: Will be replaced by "params" in the future. Now it's the string that shows to the user in the input bar.
                func: When receieve this feature from the frontend, will call this function to handle. In goddess mode, all of the handle functions should be async.
        """
        self.feature_commands.append(
            {'name': name, 'code': code, 'prompts': [prompts]})
        self.prompt[code] = prompts
        if func:
            self.feature_func_map[code] = func

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
            Code for messages is MESSAGE_TO_CCS, but we need to specify by the type_code.
            For example, text messages are MESSAGE_UP_TEXT.
        """
        self.message_func_map[code] = func

    async def _handle_data_dict_core(self, data, ws, path):
        print(f'WrappedGoddessService: _handle_data_dict received {data}.')
        if data['code'] == self.codes.MESSAGE_TO_CCS:
            await self._handle_message_to_ccs(data, ws, path)
        elif data['code'] == self.codes.COMMAND_TO_CCS:
            await self._handle_command_to_ccs(data, ws, path)
        else:
            pass
        
    async def _handle_data_dict(self, data, ws, path):
        asyncio.ensure_future(self._handle_data_dict_core(data, ws, path))

    async def _handle_message_to_ccs(self, data, ws, path):
        type_code = data['extra']['type_code']
        if type_code in self.message_func_map:
            await self.message_func_map[type_code](self, data, ws, path)
        else:
            print('no message function for code', type_code)

    async def _handle_command_to_ccs(self, data, ws, path):
        type_code = data['extra']['type_code']
        if 20000 <= type_code <= 29999:
            await self._handle_basic_command(data, ws, path)
        elif 80000 <= type_code <= 89999:
            await self._handle_notice(data, ws, path)
        elif 90000 <= type_code <= 99999:
            await self._handle_feature(data, ws, path)
        else:
            pass

    async def _handle_basic_command(self, data, ws, path):
        type_code = data['extra']['type_code']
        if type_code in self.basic_command_func_map:
            await self.basic_command_func_map[type_code](self, data, ws, path)
        else:
            print('no basic_command function for code', type_code)
    


    async def _handle_notice(self, data, ws, path):
        type_code = data['extra']['type_code']
        
        print('receive notice:' + str(data))

        if type_code in self.notice_func_map:
            await self.notice_func_map[type_code](self, data, ws, path)
            
        else:
            if type_code == self.codes.NOTICE_USER_LEFT:
                channel_id = data['extra']['channel_id']
                # Here the CCS database may want to update to delete the new user
                # In the case of Social default Goddess, the database has been updated on OPERATION_JOIN
                user_id = data['extra']['user_id']
                self.agent.leave_channel(channel_id, user_id)
                user_ids = self.agent.get_channel_user_list(channel_id)
                print('user_ids', user_ids)
                # serial_numbers= self.agent.user_id_list_to_serial_number_list(user_ids)
                # alias = [self.serial_number_to_alias(serial_number) for serial_number in serial_numbers]
                # print('alias', alias)
                # await self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CHANNEL_USER_LIST,
                #     channel_id=channel_id, to_user_ids=user_ids)
                # await self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CCS_COMMAND_LIST,
                #     channel_id=channel_id, to_user_ids=user_ids)
                
                await self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CHANNEL_USER_LIST,
                    channel_id=channel_id, to_user_ids=user_ids, user_ids=user_ids)
                # await self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CCS_COMMAND_LIST,
                #     channel_id=channel_id, to_user_ids=user_ids, commands=self.feature_commands)
                
            elif type_code == self.codes.NOTICE_GET_CHANNEL_USER_LIST:
                print('ccs yellowbear notice get channel user list', data)    
                

            else:
                raise Exception('yellowbear goddess Unknown type_code: {}'.format(type_code))
        
        '''
        else:
            print('no notice function for code', type_code)
        '''

    async def _handle_feature(self, data, ws, path):
        type_code = data['extra']['type_code']
        if type_code in self.feature_func_map:
            await self.feature_func_map[type_code](self, data, ws, path)
        else:
            print('no feature function for code', type_code)

    async def _send_ccs_operation(self, data, ws, path):
        print('WrappedGoddessService ccs_operation: ', data)
        code = data['code']
        password = data['extra']['password']
        ccs_id = data['extra']['ccs_id']
        if code == self.codes.OPERATION_CCS_LOGIN:
            await self._send_data_to_ws(
                ws, self.codes.OPERATION_CCS_LOGIN, ccs_id=ccs_id, password=password)
        else:
            pass

    async def _send_command_down(self, ws, type_code, **kwargs):
        await self._send_data_to_ws(ws, self.codes.COMMAND_FROM_CCS,
                              type_code=type_code, **kwargs)
    
    ### Some wrapped functions, use them to make your work easier!
    
    async def broadcast_command_text(self, channel_id, ws, text, clear=False):
        """
            Broadcast a text to all users in a channel.
        """
        await self._send_command_down(
            ws, 
            self.codes.COMMAND_DOWN_DISPLAY_TEXT,
            channel_id=channel_id, 
            to_user_ids=self.agent.get_channel_user_list(channel_id), 
            args={'text': text, 'clear': clear}
        )
    
    async def broadcast_command_image(self, channel_id, ws, url, clear=False):
        """
            Broadcast an image to all users in a channel.
        """
        await self._send_command_down(
            ws, 
            self.codes.COMMAND_DOWN_DISPLAY_IMAGE,
            channel_id=channel_id, 
            to_user_ids=self.agent.get_channel_user_list(channel_id), 
            args={'type':'url', 'image': url}
        )
    
    async def reply_command_text(self, data, ws, text, clear=False):
        """
            Reply a text to the sender.
        """
        await self._send_command_down(
            ws, 
            self.codes.COMMAND_DOWN_DISPLAY_TEXT,
            channel_id = data['extra']['channel_id'], 
            to_user_ids = [data['extra']['user_id']], 
            args = {'text': text, 'clear': clear}
        )
    
    # two texts, one for sender, one for others
    async def whistle_sender_command_text(
        self, data, ws, *,
        text_to_sender, text_to_others, 
        clear_sender=False, clear_others=False
    ):
        """
            Dog whistle, send different text to sender and the others separately.
        """
        # to sender
        await self._send_command_down(
            ws, 
            self.codes.COMMAND_DOWN_DISPLAY_TEXT,
            channel_id = data['extra']['channel_id'], 
            to_user_ids = [data['extra']['user_id']], 
            args = {'text': text_to_sender, 'clear': clear_sender}
        )
        # to others
        user_ids = self.agent.get_channel_user_list(data['extra']['channel_id'])
        await self._send_command_down(
            ws, 
            self.codes.COMMAND_DOWN_DISPLAY_TEXT,
            channel_id = data['extra']['channel_id'], 
            to_user_ids = list(set(user_ids) - {data['extra']['user_id']}), 
            args = {'text': text_to_others, 'clear': clear_others}
        )
    

# default operations, user can write their own functions to cover them

async def handle_fetch_command(self, data, ws, path):
    """
        A function that handles the "fetch command" notice.
        This can be the default behavior.
        You may want to use it in your customized handle functions.
    """
    channel_id = data['extra']['channel_id']
    user_id = data['extra']['user_id']
    await self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CCS_COMMAND_LIST,
        channel_id=channel_id, to_user_ids=[user_id], commands=self.feature_commands)

async def handle_join(self, data, ws, path):
    """
        A function that handles the "join" notice.
        This can be the default behavior.
        You may want to use it in your customized handle functions.
    """
    channel_id = data['extra']['channel_id']
    user_id = data['extra']['user_id']
    await self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CCS_COMMAND_LIST,
        channel_id=channel_id, to_user_ids=[user_id], commands=self.feature_commands)

async def handle_notice_auth_token(self, data, ws, path):
    """
        A function that handles the "auth token" notice.
        This can be the default behavior.
        You may want to use it in your customized handle functions.
    """
    print('yellow 502 ask notice auth token', data)
    user_id = data['extra']['user_id']
    channel_id = data['extra']['channel_id']
    target_channel_id = data['extra']['target_channel_id']
    uri = self.uri
    token = self.token
    await self._send_data_to_ws(ws, self.codes.COPERATION_CONFIRM_AUTH_TOKEN, user_id=user_id, channel_id=channel_id, to_user_ids=[user_id], target_channel_id=target_channel_id, uri=uri, token=token)
    
async def handle_notice_take_over(self, data, ws, path):
    """
        A function that handles the "take over" notice.
        This can be the default behavior.
        You may want to use it in your customized handle functions.
    """
    print("yellow 502 NOTICE_TAKE_OVER data", data)
    target_channel_id = data['extra']['target_channel_id']
    target_user_ids = data['extra']['target_user_ids']
    target_channel_name = data['extra']['target_channel_name']
    target_channel_timestamp = data['extra']['target_channel_timestamp']
    target_channel_timestamp = datetime.datetime.fromtimestamp(target_channel_timestamp)

    self.agent.init_user_id_list(target_channel_id, target_user_ids)
    # self.agent.reconstruct_channel(target_channel_id, target_channel_name, target_channel_timestamp)
    # self.agent.reconstruct_channel_user_map(target_channel_id, target_user_ids)
    print(self.feature_commands)
    await self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CHANNEL_USER_LIST,
                                    channel_id=target_channel_id, to_user_ids=target_user_ids, user_ids=target_user_ids)
    await self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CCS_COMMAND_LIST,
                                    channel_id=target_channel_id, to_user_ids=target_user_ids, user_ids=target_user_ids, commands=self.feature_commands)

async def handle_notice_release(self, data, ws, path):
    """
        A function that handles the "release" notice.
        This can be the default behavior.
        You may want to use it in your customized handle functions.
    """
    target_channel_id = data['extra']['target_channel_id']
    target_user_ids = data['extra']['target_user_ids']
    print("yellow 502 NOTICE_RELEASE")
    # self.agent.remove_channel(target_channel_id)
    # self.agent.remove_channel_user_map(target_channel_id)

async def handle_notice_user_joined(self, data, ws, path):
    """
        A function that handles the "user joined" notice.
        This can be the default behavior.
        You may want to use it in your customized handle functions.
    """
    print('yellow 502 notice user joined', data)
    # on NOTICE_JOIN_SUCCESS, give out UPDATE_CHANNEL_USER_LIST and UPDATE_CCS_COMMAND_LIST
    channel_id = data['extra']['channel_id']
    # Here the CCS database may want to update to insert the new user
    # In the case of Social default Goddess, the database has been updated on OPERATION_JOIN
    user_id = data['extra']['user_id']
    self.agent.join_channel(channel_id, user_id)
    user_ids = self.agent.get_channel_user_list(channel_id)

    await self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CHANNEL_USER_LIST,
        channel_id=channel_id, to_user_ids=user_ids, user_ids=user_ids) 
    
    await self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CCS_COMMAND_LIST,
        channel_id=channel_id, to_user_ids=[user_id], commands=self.feature_commands)

async def handle_command_fetch_user_list(self, data, ws, path):
    """
        A function that handles the "fetch user list" command.
        This can be the default behavior.
        You may want to use it in your customized handle functions.
    """
    channel_id = data['extra']['channel_id']
    user_id = data['extra']['user_id']
    user_list = self.agent.get_channel_user_list(channel_id)
    
    await self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CHANNEL_USER_LIST,
        channel_id=data['extra']['channel_id'], to_user_ids=[user_id], user_ids=user_list)

async def handle_command_fetch_cmd_list(self, data, ws, path):
    """
        A function that handles the "fetch command list" command.
        This can be the default behavior.
        You may want to use it in your customized handle functions.
    """
    channel_id = data['extra']['channel_id']
    user_id = data['extra']['user_id']
    # import datetime;

    # ct stores current time
    # ct = datetime.datetime.now()
    # print("current time:-", ct)
    # print('fetch ccs command list', channel_id, user_id)
    await self._send_command_down(ws, self.codes.COMMAND_DOWN_UPDATE_CCS_COMMAND_LIST,
        channel_id=channel_id, to_user_ids=[user_id], commands=self.feature_commands)

async def handle_command_fetch_recipient_list(self, data, ws, path):
    # TODO
    pass

async def handle_message_up_text(self, data, ws, path):
    """
        A function that handles the received text message.
        This can be the default behavior.
        You may want to use it in your customized handle functions.
    """
    data['extra']['type_code'] += 20000
    await self._send_data_to_ws(ws, self.codes.MESSAGE_FROM_CCS, **data['extra'])

async def handle_message_up_image(self, data, ws, path):
    """
        A function that handles the received image message.
        This can be the default behavior.
        You may want to use it in your customized handle functions.
    """
    data['extra']['type_code'] += 20000
    await self._send_data_to_ws(ws, self.codes.MESSAGE_FROM_CCS, **data['extra'])

async def handle_message_up_file(self, data, ws, path):
    """
        A function that handles the received file message.
        This can be the default behavior.
        You may want to use it in your customized handle functions.
    """
    data['extra']['type_code'] += 20000
    await self._send_data_to_ws(ws, self.codes.MESSAGE_FROM_CCS, **data['extra'])
