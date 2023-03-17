import websockets
import json
import traceback
from datetime import datetime, timezone, timedelta

import logging  # todo: 日志
# logging.basicConfig(format="%(message)s", level=logging.DEBUG)

# A websocket server is a coroutine that passively accepts websocket connections.
# A websocket client is a coroutine that actively makes websocket connections.
# Once the connection is established, the business logic can be controlled bidirectionally.

# Basic Server
class JSONWebsocketPassiveService:
    def __init__(self, port=7654):
        self.port = port

    @property
    def _timestamp(self):
        now = datetime.now(timezone.utc)
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc) # use POSIX epoch
        return (now - epoch) // timedelta(microseconds=1) # or `/ 1e3` for float

    @staticmethod
    def _make_data_dict(code, **extra_args):
        return {
            'code': code,
            'extra': extra_args
        }

    async def _safe_send(self, ws, data):
        # import datetime;

        # ct stores current time
        # ct = datetime.datetime.now()
        # print("before social passive _safe_sendcurrent time:-", ct, data)
        
        try:
            if isinstance(data, dict):
                data = json.dumps(data)
            else:
                pass
            
            await ws.send(data)
            # ct stores current time
            # ct = datetime.datetime.now()
            # print("after social passive _safe_sendcurrent time:-", ct)
            return True
        except websockets.ConnectionClosedOK as e:
            print('_safe_send: Connection Closed OK Exception.', e)
            
            return False
        except websockets.ConnectionClosed as e:
            print('_safe_send: Connection Closed Exception.', e)
            
            return False
        except Exception as e:
            traceback.print_exc()
            print('self._safe_send: Exception Occurs', e)
            
            return False
        
        
    async def _send_data_to_ws(self, ws, code, **extra_args):
        data_dict = self._make_data_dict(code=code, **extra_args)
        await self._safe_send(ws, data_dict)

    async def echo(self, ws, message):
        print(f'echo() received message: {message}')
        message = "I got your message: {}".format(message)
        await self._safe_send(ws, message)

    async def _safe_handle(self, ws, path):
        # import datetime;

        # ct stores current time
        # ct = datetime.datetime.now()
        # print("before social passive _safe_handle current time:-", ct)
        try:    # This websocket may be closed
            async for message in ws:
                try:
                    import datetime
                    ct = datetime.datetime.now()
                    print("passive handle", ct, message)
                    data = json.loads(message)
                    await self._handle_data_dict(data, ws, path)

                
                except Exception as e:
                    traceback.print_exc()
                    await self._handle_internal_error(e, ws, path)
            # ct = datetime.datetime.now()
            # print("after social passive _safe_handle current time:-", ct)
        except Exception as e:
            print('Exception in handle(): ', e)

    async def _handle_data_dict(self, data, ws, path):
        await self._safe_send(ws, 'Female: _handle_data_dict Not Implemented')

    async def _handle_internal_error(self, e, ws, path):
        await self._safe_send(ws, f'Female._handle_internal_error: {e}')

    # call this for the coroutine to start
    def get_server_coroutine(self):
        return websockets.serve(self._safe_handle, 'localhost', self.port)
