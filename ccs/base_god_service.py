from .json_ws_active_service import JSONWebsocketActiveService
from .. import codes

class BaseGodService(JSONWebsocketActiveService):
    def __init__(self):
        super().__init__()
        self.codes = codes
        self.path = '' # possible new route path for websocket
        
    def on_open(self, ws):
        print('BaseGodService opened')
        
    # override this function to handle data
    def _handle_data_dict(self, data, ws):
        # print(f'BaseGodService: _handle_data_dict received {data} at websocket {ws}')
        if data['code'] == self.codes.MESSAGE_TO_CCS:
            self._handle_message_to_ccs(data, ws, self.path)
        elif data['code'] == self.codes.COMMAND_TO_CCS:
            self._handle_command_to_ccs(data, ws, self.path)
        else:
            pass
    
    def _handle_message_to_ccs(self, data, ws, path):
        data['extra']['origin'] = self.__class__.__name__
        data['extra']['type_code'] += 20000

        # 3xxxx to 5xxxx
        self._send_data_to_ws(ws, self.codes.MESSAGE_FROM_CCS, **data['extra'])               

    def _handle_command_to_ccs(self, data, ws, path):
        type_code = data['extra']['type_code']
        if 20000 <= type_code <= 29999:
            self._handle_basic_command(data, ws, path)
        elif 80000 <= type_code <= 89999:
            self._handle_notice(data, ws, path)

        elif 90000 <= type_code <= 99999:
            self._handle_feature(data, ws, path)

        else:
            pass
    
    
    def _handle_basic_command(self, data, ws, path):
        pass

    def _handle_notice(self, data, ws, path):
        pass

    def _handle_feature(self, data, ws, path):
        pass
   
    def _send_ccs_operation(self, data, ws, path):
        code = data['code']
        if code == self.codes.COPERATION_GOD_RECONNECT:
            user_id = data['extra']['user_id']
            password = data['extra']['password']
            self._send_data_to_ws(ws, code, user_id=user_id, password=password)
        else:
            pass
        # # print('BaseGoddessService ccs_operation: ', data)
        # code = data['code']
        # password = data['extra']['password']
        # ccs_id = data['extra']['ccs_id']
        # if code == self.codes.COPERATION_LOGIN:
        #     self._send_data_to_ws(ws, self.codes.COPERATION_LOGIN, ccs_id=ccs_id, password=password)
        # else:
        #     pass

    def _send_command_down(self, ws, type_code, **kwargs):
        self._send_data_to_ws(ws, self.codes.COMMAND_FROM_CCS, type_code=type_code, **kwargs)