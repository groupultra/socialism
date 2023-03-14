from .json_ws_passive_service import JSONWebsocketPassiveService
from . import codes

# todo: validate connection is from Social on handshake
# no database dependency on this layer
class BaseGoddessService(JSONWebsocketPassiveService):
    def __init__(self, port=9000):
        super().__init__(port=port)
        self.codes = codes

    async def _handle_data_dict(self, data, ws, path):
        # print('BaseGoddessService _handle_data_dict: ', data)
        if data['code'] == self.codes.MESSAGE_TO_CCS:
            await self._handle_message_to_ccs(data, ws, path)
        elif data['code'] == self.codes.COMMAND_TO_CCS:
            await self._handle_command_to_ccs(data, ws, path)
        # elif data['code'] == self.codes.QUERY_RESPOND_TO_CCS:
        #     await self._handle_query_respond_to_ccs(data, ws, path)
        else:
            pass

    async def _handle_message_to_ccs(self, data, ws, path):
        data['extra']['origin'] = self.__class__.__name__
        data['extra']['type_code'] += 20000

        # 3xxxx to 5xxxx
        await self._send_data_to_ws(ws, self.codes.MESSAGE_FROM_CCS, **data['extra'])               

    async def _handle_command_to_ccs(self, data, ws, path):
        type_code = data['extra']['type_code']
        # print('BaseGoddessService _handle_command_to_ccs: ', data)
        if 20000 <= type_code <= 29999:
            await self._handle_basic_command(data, ws, path)
        elif 80000 <= type_code <= 89999:
            await self._handle_notice(data, ws, path)
        elif 90000 <= type_code <= 99999:
            await self._handle_feature(data, ws, path)

        else:
            pass
    
    async def _handle_basic_command(self, data, ws, path):
        pass

    async def _handle_notice(self, data, ws, path):
        pass

    async def _handle_feature(self, data, ws, path):
        pass

    async def _send_command_down(self, ws, type_code, **kwargs):
        await self._send_data_to_ws(ws, self.codes.COMMAND_FROM_CCS, type_code=type_code, **kwargs)

    async def _send_ccs_operation(self, data, ws, path):
        pass
    

        