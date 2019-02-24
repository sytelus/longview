from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .zmq_pub_sub import ZmqPubSub
import threading
import sys
import uuid
import queue
import dill
import time
from .lv_types import *
from . import utils
from .repeated_timer import RepeatedTimer

class WatchClient:
    class Stream:
        def __init__(self, client_id:str, clisrv, streams, event_name:str, eval_f_s:str,
                stream_name:str=None, eval_start:int=0, eval_end:int=sys.maxsize, throttle=None):
            self.stream_name = stream_name or str(uuid.uuid4())
            self._qt = None
            self._streams = streams
            self.clisrv = clisrv
            self._callbacks = {}
            self._streams[self.stream_name] = self
            self.stream_req = StreamRequest(event_name, eval_f_s, self.stream_name, 
                eval_start, eval_end, throttle, client_id)

            self._send_stream_req()

        def on_event_eval(self, eval_result:EvalResult):
            utils.debug_log("Event eval received", eval_result.event_name, verbosity=6)
            if self.closed:
                return
            for callback in self._callbacks.keys():
                callback(eval_result, stream_reset=False)
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
                self.clisrv.send_obj(clisrv_req)
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

            eval_result, stop_iter = None, False
            if not self.closed:
                if self._qt[0].empty():
                    self._qt[1].wait()
                    self._qt[1].clear()
                eval_result = self._qt[0].get()
                stop_iter = eval_result.ended
            else:
                stop_iter = True

            if stop_iter:
                self._qt = None
                raise StopIteration()
            else:
                return eval_result

        def _send_stream_req(self):
            # stop any iterators in progress
            self.closed = True
            if self._qt is not None:
                self._qt[1].set()

            # resubscribe to stream
            clisrv_req = ClientServerRequest(CliSrvReqTypes.create_stream, self.stream_req)
            self.clisrv.send_obj(clisrv_req)
            self.closed = False

        def server_changed(self, server_id):
            utils.debug_log('sending stream req..')
            self._send_stream_req()
            utils.debug_log('sent stream req')
            for callback in self._callbacks.keys():
                callback(None, stream_reset=True)

    _port_start = 40859

    def __init__(self, pubsub_port=None, cliesrv_port=None, host="localhost"):
        self.client_id = str(uuid.uuid4())
        self._streams = {}
        self._renderers = {}

        pubsub_port = pubsub_port or WatchClient._port_start
        cliesrv_port = cliesrv_port or WatchClient._port_start+1
        WatchClient._port_start += int(pubsub_port == WatchClient._port_start) \
                                + int(cliesrv_port == WatchClient._port_start+1)

        self._clisrv = ZmqPubSub.ClientServer(cliesrv_port, False)

        self._sub_event_eval = ZmqPubSub.Subscription(pubsub_port, 
            TopicNames.event_eval, self._on_event_eval)
        self._sub_srv_mgmt = ZmqPubSub.Subscription(pubsub_port, 
            TopicNames.srv_mgmt, self._on_srv_mgmt)

        self._last_server_hb = time.time()
        self._heartbeat_timer = RepeatedTimer(1, self._send_heartbeat)
        self._heartbeat_timer.start()

        self.server_id = None
        utils.debug_log("Client initialized")


    def _on_event_eval(self, eval_result:EvalResult):
        if eval_result.stream_name in self._streams:
            self._streams[eval_result.stream_name].on_event_eval(eval_result)
        else:
            utils.debug_log("Event for unknown stream", eval_result.event_name, verbosity=5)

    def _on_srv_mgmt(self, mgmt_msg:ServerMgmtMsg):
        utils.debug_log("Received - SeverMgmtevent", verbosity=6)
        if mgmt_msg.event_name == 'HB':
            self._last_server_hb = time.time()
            self._heartbeat_timer.unpause()
            server_id = mgmt_msg.event_args
            if server_id != self.server_id and self.server_id is not None:
                utils.debug_log("Server change detected", verbosity=1)
                for stream in self._streams.values():
                    if not stream.closed:
                        stream.server_changed(server_id)
            self.server_id = server_id


    def _send_heartbeat(self):
        if time.time() - self._last_server_hb > 6: #make configurable
            utils.debug_log("Server heartbeat lost, pausing client heartbeat", verbosity=1)
            self._heartbeat_timer.pause()
        clisrv_req = ClientServerRequest(CliSrvReqTypes.heartbeat, self.client_id)
        self._clisrv.send_obj(clisrv_req)

    def create_stream(self, event_name:str, eval_f_s:str, stream_name:str=None, 
        eval_start:int=0, eval_end:int=sys.maxsize, throttle=None):

        stream = WatchClient.Stream(self.client_id, self._clisrv, self._streams, event_name, eval_f_s,
            stream_name, eval_start, eval_end, throttle)

        return stream

    def print_to_srv(self, msg):
        clisrv_req = ClientServerRequest(CliSrvReqTypes.print_msg, msg)
        self._clisrv.send_obj(clisrv_req)

