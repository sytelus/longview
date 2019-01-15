from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .zmq_pub_sub import ZmqPubSub
import threading
import sys
import uuid
import queue
import dill
from .lv_types import *
from .renderers import *


class WatchClient:
    class Stream:
        def __init__(self, clisrv, streams, event_name:str, eval_f_s:str,
                callback:Callable[[EvalResult], None]=None, stream_name:str=None, 
                eval_start:int=0, eval_end:int=sys.maxsize, throttle=None):
            self.closed = True
            self.stream_name = stream_name or str(uuid.uuid4())
            self.clisrv = clisrv
            self.stream_req = StreamRequest(event_name, eval_f_s, self.stream_name, 
                eval_start, eval_end, throttle)
            clisrv_req = ClientServerRequest(CliSrvReqTypes.create_stream, self.stream_req)
            self.clisrv.request(clisrv_req)
            self.closed = False
            self._qt = None
            self._streams = streams

            self._callbacks = {}
            if callback is not None:
                self._callbacks[callback] = callback

            self._streams[self.stream_name] = self

        def on_event_eval(self, eval_result:EvalResult):
            if self.closed:
                return
            for callback in self._callbacks.keys():
                callback(eval_result)
            if self._qt is not None:
                self._qt[0].put(eval_result)
                self._qt[1].set()

        def subscribe(self, callback):
            self._callbacks[callback] = callback
        def unsubscribe(self, callback):
            self._callbacks.pop(callback, None)

        def close(self):
            if not self.closed:
                self._callbacks = {}
                clisrv_req = ClientServerRequest(CliSrvReqTypes.del_stream, self.stream_req)
                self.clisrv.request(clisrv_req)
                del self._streams[self.stream_name]
                self._qt = None
                self.closed = True

        def __enter__(self):
            return self

        def __exit__(self, exception_type, exception_value, traceback):
            self.close()

        def __del__(self):
            self.close()

        def __iter__(self):
            self._qt = (queue.Queue(), threading.Event())
            return self

        def __next__(self):
            if self._qt is None:
                raise RuntimeError("iter() wasn't called before next()")
            if self._qt[0].empty():
                self._qt[1].wait()
                self._qt[1].clear()
            eval_result = self._qt[0].get()
            if eval_result.ended:
                self._qt = None
                raise StopIteration()
            else:
                return eval_result
    
    _port_start = 40859

    def __init__(self, pubsub_port=None, cliesrv_port=None, host="localhost"):
        self._streams = {}
        self._renderers = {}
        
        self._sub = ZmqPubSub.Subscription(pubsub_port or WatchClient._port_start, 
            TopicNames.event_eval, self._on_event_eval)
        self._clisrv = ZmqPubSub.ClientServer(cliesrv_port or WatchClient._port_start+1, False)
        WatchClient._port_start += 2

    def _on_event_eval(self, eval_result:EvalResult):
        if eval_result.stream_name in self._streams:
            self._streams[eval_result.stream_name].on_event_eval(eval_result)
        else:
            pass
            #print("Stream {} not handled".format(eval_result.stream_name))

    def create_stream(self, event_name:str, eval_f_s:str, callback:Callable[[EvalResult], None]=None,
            stream_name:str=None, eval_start:int=0, eval_end:int=sys.maxsize, throttle=None):

        stream = WatchClient.Stream(self._clisrv, self._streams, event_name, eval_f_s, callable, 
            stream_name, eval_start, eval_end, throttle)

        return stream

