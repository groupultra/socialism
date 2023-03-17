import websocket    # use wsaccel for higher performance

import rel

import json
import traceback
# import threading, 
import time
# import _thread
import gc
import _thread
# A manager of connections that facilitates
# 1. actively establishing new connections to specific uri
# 2. once the connection is established, they follow the same on_xxx rules
# 3. Active works synchronously (direct forwarding), passive works asynchronously (logic)

# Never use echo server! Another echo client will flood the network!

# This framework is unable to send data at random time from outside on_XXX functions,
# but it is enough for our purpose, as long as we can use on_open for initial connection.
class JSONWebsocketActiveService:
    def __init__(self) -> None:
        pass
    
    # new websocket, do not try to connect
    def create_websocket(self, uri, on_open=None, on_message=None, on_error=None, on_close=None):
        print('create_websocket')
        ws = websocket.WebSocketApp(uri,
            on_open=on_open or self.on_open,
            on_message=on_message or self.on_message,
            on_error=on_error or self.on_error,
            on_close=on_close or self.on_close
        )
        return ws
    
    # new connections could be created in response to on_XXX following same rules
    def create_connection(self, uri, on_open=None, on_message=None, on_error=None, on_close=None):
        print('create_connection')
        # ws = websocket.WebSocketApp(uri,
        #     on_open=on_open or self.on_open,
        #     on_message=on_message or self.on_message,
        #     on_error=on_error or self.on_error,
        #     on_close=on_close or self.on_close
        # )
        ws = self.create_websocket(uri, on_open, on_message, on_error, on_close)
        # ws.run_forever(reconnect=5)
        ws.run_forever(skip_utf8_validation=True, dispatcher=rel, reconnect=5)
        # print('before yield ws run_forever')
        # yield ws
        # print('start run_forever')
        # keep_on = True # use the return of run_forever to capture KeyboardInterrupt
        # while keep_on:
        #     try:
        #         keep_on = ws.run_forever(skip_utf8_validation=True, ping_interval=10, ping_timeout=8)
        #     except Exception as e:
        #         gc.collect()
        #         print("Websocket connection Error : {e}")                    
        #     print("Reconnecting websocket after 5 sec")
        #     time.sleep(5)
        return ws

    def on_message(self, ws, message):
        import datetime
        ct = datetime.datetime.now()
        print("on_message on_message on_message", ct)
        self._safe_handle(ws, message)

    def on_error(self, ws, error):
        print(f'Male.on_error: {error}')

    def on_close(self, ws, close_status_code, close_msg):
        print(f"Male.on_close: {ws} closed with status code {close_status_code} and message {close_msg}")
        # print ("Retry connection: %s" % time.ctime())
        # time.sleep(5)
        # self.run() # retry per 5 seconds
    
    # override this function to do something when connection is established
    def on_open(self, ws):
        pass

    @staticmethod
    def _make_data_dict(code, **extra_args):
        return {
            'code': code,
            'extra': extra_args
        }

    def _send_data_to_ws(self, ws, code, **extra_args):
        data_dict = self._make_data_dict(code=code, **extra_args)
        self._safe_send(ws, data_dict)

    def _safe_send(self, ws, data):
        try:
            if isinstance(data, dict):
                data = json.dumps(data)
            else:
                pass
            import datetime;
            ct = datetime.datetime.now()
            print("active send", ct)
            ws.send(data)
            return True

        except websocket.WebSocketConnectionClosedException as e:
            print('Male: _safe_send: Connection Closed Exception.', e)
            
            return False
        except Exception as e:
            traceback.print_exc()
            print('Male: self._safe_send: Exception Occurs', e)
            
            return False

    def echo(self, ws, message):
        print(f'echo() received message: {message}')
        message = "I got your message: {}".format(message)
        self._safe_send(ws, message)

    def _safe_handle(self, ws, message):
        
        import datetime;

        # # ct stores current time
        
        try:
            ct = datetime.datetime.now()
            print("before social active _safe_handle current time:-", ct)
            data = json.loads(message)
            # ct = datetime.datetime.now()
            # print('data', data, ct)
            self._handle_data_dict(data, ws)

        except ValueError as e:
            # traceback.print_exc()
            print(f'Male: _safe_handle received non-json message {message}')
        
        except Exception as e:
            print('Male: Server function error!')
            traceback.print_exc()
        
        # import datetime;

        # # ct stores current time
        # ct = datetime.datetime.now()
        # print("after social active _safe_handle current time:-", ct)

    # override this function to handle data
    def _handle_data_dict(self, data, ws):
        print(f'Male default: _handle_data_dict received {data} at websocket {ws}')
        

    def run(self):
        uri = 'wss://frog.4fun.chat/social'
        self.create_connection(uri)
        # print("after create_connection")
        rel.signal(2, rel.abort)  # Keyboard Interrupt, one for all connections
        # print("after signal")
        rel.dispatch()
        # print("after everything in run")
    
    # def run(self):
    #     uri = 'wss://frog.4fun.chat/social'
    #     ws = self.create_connection(uri)
    #     # _thread.start_new_thread(self.create_connection, (uri,))
    #     # # ws = websocket.WebSocketApp("ws://127.0.0.1:3000", on_open = on_open, on_close = on_close)
    #     # wst = threading.Thread(target=ws.run_forever())
    #     # wst.daemon = True
    #     # print('before start')
    #     # wst.start()
    #     # print('after start')
        
        
        

if __name__ == "__main__":
    # websocket.enableTrace(True)
    
    service = JSONWebsocketActiveService()
    service.run()