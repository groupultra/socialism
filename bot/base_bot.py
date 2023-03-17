from .json_socket_user import JSONSocketUser, MessageType, Message, rel

from .. import codes
import websocket, datetime, random

class BaseBot(JSONSocketUser):
	"""
	This is the base of bot, deriving from which you can define automation of 
	all behavior that a bot will abey. 
	For basic use, what you need to do is only overriding `on_receive_message`
	to define the behaviour when receive a message. For example, you
	are definately allowed to broadcast the message to everyone in the channel 
	where you receive it by overriding `on_receive_message` and call 
	`send_message` with message you received send it to all users in the channel.

	We wraps the message data into a Message object.
    For better performance(not indeed), you could set
    `pre_analyse` to be `False` to get raw data of message(dict).
	"""
	def __init__(self, user_id:str, password:str, path:str=None, reconnect:int=None, pre_analyse:bool=True) -> None:
		"""
		Initialize a Bot instance.

		Args:
			user_id : str
				User ID of the account you wanna set as a bot.
			password : str
				Password of that account referred above.
			path : str : optional
				Location of server the bot will be running on.
			reconnect : int : optional
				Max pending time for stalling. Reconnection will launch if stalls
				outlong this time.
			pre_analyse : bool : optional
				Trigger for pre-analysing message by wrapping it into a Message object.
				If turned off, data param in on_receive_data() will be raw dict!
		"""
		self.cached = False
		super().__init__(path=path, reconnect=reconnect, pre_analyse=pre_analyse)
		self.codes = codes
		self.channel_list = []
		self.user_lists = {}
		self.user_id = user_id
		self.password = password

	def on_receive_status(self, data):
		"""
		Behaviour when receives status from server(6xxxx).

		By default, we would update channel_list and user_list
		on sereval cases. Therefore, if you want to customize
		behaviour receive status while keeping these properties
		up to date, override this function and **call**
		**super().on_receive_status** to keep them.

		Args:
			data : dict
				WS data in the format definde by `codes.md`
		"""
		code = data['code']

		if code == self.codes.STATUS_INFO_USER_CHANNEL_LIST:
			self._update_channel_list(data)
		elif code == self.codes.STATUS_INFO_CREATE_CHANNEL_SUCCESS or code == self.codes.STATUS_INFO_JOIN_SUCCESS:
			self._append_channel_list(data)
		elif code == self.codes.STATUS_INFO_LEAVE_SUCCESS:
			self._pop_channel_list(data)
		else:
			super().on_receive_status(data)

	def on_receive_message(self, data):
		"""
		Behaviour when receives message from server(3xxxx).
		Override this to customize what to do when receives
		a message!

		Args:
			data : dict || Message
				Wrapped Message object of message received.
				If pre-analyse is turned off, it would be 
				raw WS data in the format definde by `codes.md`
		"""
		print('Bot received message: {}'.format(data))
		super().on_receive_message(data)

	def on_receive_command(self, data):
		"""
		Behaviour when receives commands from server(4xxxx).
		It's crucial for keeping channel_list up to date. If
		you want to customize the behaviour, please **call**
		**super().on_receive_command** to keep those properties.

		Args:
			data : dict
				WS data in the format definde by `codes.md`
		"""
		code = data['code']

		if code == self.codes.COMMAND_DOWN_UPDATE_CHANNEL_USER_LIST:
			self._update_user_lists(data)
		else:
			super().on_receive_command(data)

	def on_open(self, ws):
		"""
		Behaviour at the time websocket connection is created.

		Args:
			ws : websocket.WebSocketApp
                Connection object.
		"""
		if self.cached:
			self.login()
		print('Bot.open!')
	
	def on_close(self, ws, close_status_code, close_msg):
		"""
		Behaviour at the time websocket connection is closed.

		Args:
			ws : websocket.WebSocketApp
                Connection object.
		"""
		print(f'Bot.close: {ws} closed with status code {close_status_code} and message {close_msg}')

	def on_error(self, ws, error):
		"""
		Behaviour at the time error occur on websocket connection.

		Args:
			ws : websocket.WebSocketApp
                Connection object.
		"""
		print(f'Bot.error: {error}')
	
	def on_message(self, ws, message):
		"""
		Behaviour at the time receive message from websocket connection.
	
		Warning:
			Do not re-write this if you have no idea what will happen!

		Args:
			ws : websocket.WebSocketApp
                Connection object.
			message : jstr
				Raw message json string from ws connection.
		"""
		print(f'Bot.message: {message}')
		self._safe_handle(ws, message)

	def _update_channel_list(self, data):
		"""
		Utility function to update current channel_list.
		If such properties are useless to you, and for
		better time performance(not that good though)
		you could re-write this to no-op.

		Args:
			data : dict
				WS data in the format definde by `codes.md`
		"""
		self.channel_list = data['extra']['channel_ids']

		for channel_id in self.channel_list:
			self._command_fetch_channel_user_list(self.user_id, channel_id)

	def _update_user_lists(self, data):
		"""
		Utility function to update current user_lists.
		If such properties are useless to you, and for
		better time performance(not that good though)
		you could re-write this to no-op.

		Args:
			data : dict
				WS data in the format definde by `codes.md`
		"""
		self.user_lists[data['extra']['channel_id']] = data['extra']['user_ids']

	def _append_channel_list(self, data):
		"""
		Utility function to update current channel_list.
		If such properties are useless to you, and for
		better time performance(not that good though)
		you could re-write this to no-op.

		Args:
			data : dict
				WS data in the format definde by `codes.md`
		"""
		self.channel_list.append(data['extra']['channel_id'])
		self._command_fetch_channel_user_list(self.user_id, data['extra']['channel_id'])

	def _pop_channel_list(self, data):
		"""
		Utility function to update current channel_list.
		If such properties are useless to you, and for
		better time performance(not that good though)
		you could re-write this to no-op.

		Args:
			data : dict
				WS data in the format definde by `codes.md`
		"""
		self.channel_list.remove(data['extra']['channel_id'])
		self.user_lists.pop(data['extra']['channel_id'])

	def login(self):
		"""
		Wrapped login function. Call this to login.
		If you wanna customize login behaviour, call
		`_command_login()` to send command to login.
		"""
		print("Bot login!")
		self.cached = True
		self._command_login(self.user_id, self.password)

	def logout(self):
		"""
		Wrapped logout function. Call this to logout.
		If you wanna customize logout behaviour, call
		`_command_logout()` to send command to logout.
		"""
		print("Bot logout!")
		self._command_logout(self.user_id)

	def register(self, email:str, password:str):
		"""
		Wrapped register function. Call this to register.
		If you wanna customize register behaviour, call
		`_command_register()` to send command to register.

		Args:
			email : str
				Email to register an account.
			password : str
				Password for that new account.
		"""
		print("Bot register")
		self._command_register(email, password)

	def reset_password(self, email:str, password:str):
		"""
		Wrapped reset password function. Call this to reset password.
		If you wanna customize reset password behaviour, call
		`_command_reset_password()` to send command to reset password.

		Args:
			email : str
				Email of the account to reset pw.
			password : str
				New password for that account.
		"""
		print("Bot reset password")
		self._command_reset_password(email, password)

	def join_channel(self, channel_id:str):
		"""
		Wrapped join channel function. Call this to join channel.
		If you wanna customize join channel behaviour, call
		`_command_join_channel()` to send command to join channel.

		Args:
			channel_id : str
				ID of channel to join.
		"""
		print("Bot join channel: {}".format(channel_id))
		self._command_join_channel(self.user_id, channel_id)

	def leave_channel(self, channel_id:str):
		"""
		Wrapped leave channel function. Call this to leave channel.
		If you wanna customize leave channel behaviour, call
		`_command_leave_channel()` to send command to leave channel.

		Args:
			channel_id : str
				ID of channel to leave.
		"""
		print("Bot leave channel: {}".format(channel_id))
		self._command_leave_channel(self.user_id, channel_id)

	def fetch_offline_message(self):
		"""
		Wrapped fetch ofl-message function. Call this to fetch ofl-message.
		If you wanna customize fetch ofl-message behaviour, call
		`_command_fetch_offline_message()` to send command to fetch ofl-message.
		"""
		print("Bot fetch offline message!")
		self._command_fetch_offline_message(self.user_id)

	def fetch_bot_channels(self):
		"""
		Wrapped fetch bot channels function. Call this to fetch bot channels.
		If you wanna customize fetch bot channels behaviour, call
		`_command_fetch_user_channels()` to send command to fetch bot channels.
		"""
		print('Bot fetch channels!')
		self._command_fetch_user_channels(self.user_id)

	def create_channel(self, channel_id):
		"""
		Wrapped create channel function. Call this to create channel.
		If you wanna customize create channel behaviour, call
		`_command_create_channel()` to send command to create channel.
		
		Args:
			channel_id : str
				ID of the new channel.
		"""
		print('Bot create channel: {}'.format(channel_id))
		self._command_create_channel(self.user_id, channel_id)

	def fetch_channel_command_list(self, channel_id):
		"""
		Wrapped fetch channel cmd list function. Call this to fetch channel cmd list.
		If you wanna customize fetch channel cmd list behaviour, call
		`_command_fetch_channel_command_list()` to send command to fetch channel cmd list.

		Args:
			channel_id : str
				ID of the channel to fetch command list.
		"""
		print('Bot fetch command list of channel : {}'.format(channel_id))
		self._command_fetch_channel_command_list(self.user_id, channel_id)

	def fetch_recipients(self, message_id):
		"""
		Wrapped fetch recipients function. Call this to fetch recipients of 
		a certain message. If you wanna customize fetch recipients behaviour, 
		call `_command_fetch_recipients()` to send command to fetch recipients.

		Args:
			message_id : str
				ID of the message to look up for recipients.
		"""
		print('Bot fetch recipients of message : {}'.format(message_id))
		self._command_fetch_recipient_list(self.user_id, message_id)
	
	def send_message(self, message:Message):
		"""
		Wrapped send message function. Call this to send message.
		If you wanna customize send message behaviour, call
		`_command_send_message()` to send command to send message.

		Args:
			message : Message
				Wrapped message object contains message body, receivers,
				target channel and sender information.
		"""
		temp_msg_id = f"temp_{datetime.datetime.now().timestamp()}_{str(random.randint(0, 100000)).zfill(5)}"
		print('Bot send message: {}\nto: {}\n at channel: {}'.format(message.body, message.to, message.channel))
		self._command_send_message(temp_msg_id=temp_msg_id, message=message)

	def run(self):
		"""
		Behaviour to run bot. 
		By default, it will login and update several properties
		of bot like channel_list .etc. Then it will hang this
		process up and reconnect when error occurs.
		
		Warning:
			Don't re-write this if you have no idea what will happen!
		"""
		self.login()
		self.fetch_bot_channels()
		rel.signal(2, rel.abort)
		rel.dispatch()
