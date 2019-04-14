from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .zmq_pub_sub import ZmqPubSub
import sys
import uuid
import time
from .lv_types import *
from . import utils
from .repeated_timer import RepeatedTimer
from .stream import Stream


class WatchClient:
    _port_start = 40859

    class StreamHandler:
        def __init__(self, client_id:str, clisrv, event_name:str, expr:str, stream_name:str=None, throttle=None):

            self.stream = Stream(stream_name, throttle)
            self.clisrv = clisrv
            self.stream_req = StreamRequest(event_name, expr, self.stream_name, 
                throttle, client_id)
            self._send_stream_req()

        def on_subscription_item(self, stream_item:StreamItem):
            utils.debug_log("Stream item received", stream_item.event_name, verbosity=6)
            self.stream.send_data(stream_item)

        def close(self):
            if not self.stream.closed:
                clisrv_req = ClientServerRequest(CliSrvReqTypes.del_stream, self.stream_req)
                self.clisrv.send_obj(clisrv_req)
            self.stream.close()

        def _send_stream_req(self):
            # resubscribe to stream
            utils.debug_log("sending create streamreq...")
            clisrv_req = ClientServerRequest(CliSrvReqTypes.create_stream, self.stream_req)
            self.clisrv.send_obj(clisrv_req)
            utils.debug_log("sent create streamreq")

        def server_changed(self, source_id):
            utils.debug_log('sending stream req..')
            self._send_stream_req()
            utils.debug_log('sent stream req')

            self.stream.send_reset()

    def __init__(self, pubsub_port=None, cliesrv_port=None, server_index:int=0, host="localhost", heartbeat_timeout=600):
        self.heartbeat_timeout = heartbeat_timeout
        self.client_id = str(uuid.uuid4())
        self._stream_handlers = {}

        pubsub_port = (pubsub_port or WatchClient._port_start) + server_index * 2
        cliesrv_port = (cliesrv_port or WatchClient._port_start+1) + server_index * 2

        self._clisrv = ZmqPubSub.ClientServer(cliesrv_port, False)

        self._sub_event_eval = ZmqPubSub.Subscription(pubsub_port, 
            TopicNames.subscription_item, self._on_subscription_item)
        self._sub_srv_mgmt = ZmqPubSub.Subscription(pubsub_port, 
            TopicNames.srv_mgmt, self._on_srv_mgmt)

        self._last_server_hb = time.time()
        self._heartbeat_timer = RepeatedTimer(1, self._send_heartbeat)
        self._heartbeat_timer.start()

        self.source_id = None
        utils.debug_log("Client initialized")

    def _on_subscription_item(self, stream_item:StreamItem):
        if stream_item.stream_name in self._stream_handlers:
            utils.debug_log("Received event for stream", stream_item.stream_name, verbosity=5)
            self._stream_handlers[stream_item.stream_name].on_subscription_item(stream_item)
        else:
            utils.debug_log("Event for unknown stream", stream_item.stream_name, verbosity=5)

    def _on_srv_mgmt(self, mgmt_msg:ServerMgmtMsg):
        utils.debug_log("Received - SeverMgmtevent", verbosity=6)
        if mgmt_msg.event_name == 'HB':
            self._last_server_hb = time.time()
            if self._heartbeat_timer.get_state() == RepeatedTimer.State.Paused:
                utils.debug_log("Server heartbeat received, restarting client heartbeat", 
                    verbosity=1)
                self._heartbeat_timer.unpause()
            source_id = mgmt_msg.event_args
            if source_id != self.source_id and self.source_id is not None:
                utils.debug_log("Server change detected", verbosity=1)
                for stream_handler in self._stream_handlers.values():
                    if not stream_handler.stream.closed:
                        stream_handler.server_changed(source_id)
            self.source_id = source_id


    def _send_heartbeat(self):
        if time.time() - self._last_server_hb > self.heartbeat_timeout:
            utils.debug_log("Server heartbeat lost, pausing client heartbeat", 
                (time.time(), self._last_server_hb), verbosity=1)
            self._heartbeat_timer.pause()
        clisrv_req = ClientServerRequest(CliSrvReqTypes.heartbeat, self.client_id)
        self._clisrv.send_obj(clisrv_req)

    def create_stream(self, event_name:str, expr:str, stream_name:str=None, throttle=1):
        utils.debug_log("Client - creating stream...", stream_name)

        stream_handler = WatchClient.StreamHandler(self.client_id, self._clisrv, event_name, expr, stream_name, throttle)
        self._stream_handlers[stream_handler.stream.stream_name] = stream_handler

        return stream_handler.stream

    def close_stream(self, stream_handler):
        stream_handler.close()
        del self._stream_handlers[stream_handler.stream.stream_name]

    def print_to_srv(self, msg):
        clisrv_req = ClientServerRequest(CliSrvReqTypes.print_msg, msg)
        self._clisrv.send_obj(clisrv_req)
