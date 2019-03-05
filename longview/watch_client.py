from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .zmq_pub_sub import ZmqPubSub
import threading
import sys
import uuid
import queue
import dill
import time
import weakref
from .lv_types import *
from . import utils
from .repeated_timer import RepeatedTimer

class WatchClient:
    class Stream:
        def __init__(self, client_id:str, clisrv, event_name:str, expr:str,
                stream_name:str=None, throttle=None):
            self.stream_name = stream_name if stream_name is not None else str(uuid.uuid4())
            self._qt = None
            self.clisrv = clisrv
            self._callbacks = []
            self.stream_req = StreamRequest(event_name, expr, self.stream_name, 
                throttle, client_id)

            self._send_stream_req()

        def on_event_eval(self, eval_result:EvalResult):
            utils.debug_log("Event eval received", eval_result.event_name, verbosity=6)
            if self.closed:
                return
            se = StreamEvent(StreamEvent.Type.eval_result, self.stream_name, eval_result)
            self._make_callbacks(se)
            if self._qt is not None:
                self._qt[0].put(eval_result)
                self._qt[1].set()

        def _make_callbacks(self, stream_event:StreamEvent):
            for callback in self._callbacks:
                if callback and callback():
                    callback()(stream_event)

        def subscribe(self, callback):
            self._callbacks.append(weakref.WeakMethod(callback))
        def unsubscribe(self, callback):
            for i in reversed(range(len(self._callbacks))):
                if self._callbacks[i] and self._callbacks[i]() == callback:
                    del self._callbacks[i]

        def _close(self):
            if not self.closed:
                self._callbacks = []
                clisrv_req = ClientServerRequest(CliSrvReqTypes.del_stream, self.stream_req)
                self.clisrv.send_obj(clisrv_req)
                self._qt = None
                self.closed = True

        def __enter__(self):
            return self

        def __exit__(self, exception_type, exception_value, traceback):
            self.close()

        def __del__(self):
            self._close()

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
            utils.debug_log("sending create streamreq...")
            clisrv_req = ClientServerRequest(CliSrvReqTypes.create_stream, self.stream_req)
            self.clisrv.send_obj(clisrv_req)
            utils.debug_log("sent create streamreq")

            self.closed = False

        def server_changed(self, server_id):
            utils.debug_log('sending stream req..')
            self._send_stream_req()
            utils.debug_log('sent stream req')

            se = StreamEvent(StreamEvent.Type.reset, self.stream_name, None)
            self._make_callbacks(se)

    _port_start = 40859

    def __init__(self, pubsub_port=None, cliesrv_port=None, server_index:int=0, host="localhost"):
        self.client_id = str(uuid.uuid4())
        self._streams = {}

        pubsub_port = (pubsub_port or WatchClient._port_start) + server_index * 2
        cliesrv_port = (cliesrv_port or WatchClient._port_start+1) + server_index * 2

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
            utils.debug_log("Received event for stream", eval_result.stream_name, verbosity=5)
            self._streams[eval_result.stream_name].on_event_eval(eval_result)
        else:
            utils.debug_log("Event for unknown stream", eval_result.stream_name, verbosity=3)

    def _on_srv_mgmt(self, mgmt_msg:ServerMgmtMsg):
        utils.debug_log("Received - SeverMgmtevent", verbosity=6)
        if mgmt_msg.event_name == 'HB':
            self._last_server_hb = time.time()
            if self._heartbeat_timer.get_state() == RepeatedTimer.State.Paused:
                utils.debug_log("Server heartbeat received, restarting client heartbeat", 
                    verbosity=1)
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
            utils.debug_log("Server heartbeat lost, pausing client heartbeat", 
                (time.time(), self._last_server_hb), verbosity=1)
            self._heartbeat_timer.pause()
        clisrv_req = ClientServerRequest(CliSrvReqTypes.heartbeat, self.client_id)
        self._clisrv.send_obj(clisrv_req)

    def create_stream(self, event_name:str, expr:str, stream_name:str=None, throttle=None):
        utils.debug_log("Client - creating stream...", stream_name)

        stream = WatchClient.Stream(self.client_id, self._clisrv, event_name, expr,
            stream_name, throttle)
        self._streams[stream.stream_name] = stream

        return stream

    def close_stream(self, stream):
        stream._close()
        del self._streams[stream.stream_name]

    def print_to_srv(self, msg):
        clisrv_req = ClientServerRequest(CliSrvReqTypes.print_msg, msg)
        self._clisrv.send_obj(clisrv_req)
