from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .zmq_pub_sub import ZmqPubSub
import threading
from .lv_types import *
from .evaler import Evaler
import time
import sys
import uuid
from . import utils
from .repeated_timer import RepeatedTimer

class WatchServer:
    _port_start = 40859
    def __init__(self, pubsub_port:int=None, cliesrv_port:int=None):
        self._reset()
        self.open(pubsub_port, cliesrv_port)
        utils.debug_log("WatchServer started", verbosity=1)

    def open(self, pubsub_port:int=None, cliesrv_port:int=None):
        if self.closed:
            self._publication = ZmqPubSub.Publication(port = pubsub_port or WatchServer._port_start)
            self._clisrv = ZmqPubSub.ClientServer(cliesrv_port or WatchServer._port_start+1, 
                True, callback=self._clisrv_callback)
            WatchServer._port_start += 2
            self.closed = False

            self._heartbeat_timer = RepeatedTimer(1, self._send_heartbeat)
            self._heartbeat_timer.start()
        else:
            raise RuntimeError("WatchServer is already open and must be closed before open() call")

    def set_globals(self, **vars):
        self._global_vars.update(vars)

    def log(self, event_name:str='', stream_name='', **vars) -> None:
        # if there is no stream then create one
        if not self.get_stream_req(event_name, stream_name):
            stream_req = StreamRequest(event_name, 'lambda x:x', stream_name, 
                throttle=None, client_id='')
            self.create_stream(stream_req)
        self.observe(event_name, **vars)

    def observe(self, event_name:str='', **vars) -> None:
        event_vars = self._event_vars.get(event_name, {})
        event_vars.update(vars)
        self._event_vars[event_name] = event_vars
        self._exec_event(event_name)

    def get_event_index(self, event_name:str):
        return self._event_counts.get(event_name, -1)

    def end_event(self, event_name:str='', disable_streams=False) -> None:
        stream_reqs = self._event_streams.get(event_name, {})
        for stream_req in stream_reqs.values():
            if not stream_req.disabled:
                self._end_stream_req(stream_req, disable_streams)

    def del_stream(self, stream_req:StreamRequest):
        utils.debug_log("deleting stream", stream_req.stream_name)
        stream_reqs = self._event_streams.get(stream_req.event_name, {})
        stream_req = stream_reqs[stream_req.stream_name]
        stream_req.disabled = True
        stream_req._evaler.abort()
        #TODO: to enable delete we need to protect iteration in set_vars
        #del stream_reqs[stream_req.stream_name]

    def create_stream(self, stream_req:StreamRequest) -> int:
        # TODO: need to think more about overwrite behavior
        utils.debug_log("creating stream", stream_req.stream_name)
        stream_req._evaler = Evaler(stream_req.eval_expr)

        stream_reqs = self._event_streams.get(stream_req.event_name, None)
        if stream_reqs is None:
            stream_reqs = self._event_streams[stream_req.event_name] = {}
        stream_req.stream_index = self.stream_count
        self.stream_count += 1
        stream_reqs[stream_req.stream_name] = stream_req

    def get_stream_req(self, event_name:str, stream_name:str)->StreamRequest:
        stream_reqs = self._event_streams.get(event_name, None)
        if stream_reqs is not None:
            return stream_reqs.get(stream_name, None)
        return None

    def close(self):
        if not self.closed:
            ZmqPubSub.close()
            self._reset()
            utils.debug_log("WatchServer is closed", verbosity=1)

    def send_text(self, text:str, topic=""):
        self._publication.send_obj(text, topic)

    def _reset(self):
        self._event_streams:Dict[str, StreamRequests] = {}
        self._event_counts:Dict[str, int] = {}
        self._global_vars = {}
        self._event_vars = {}
        self._client_heartbeats = {}
        self.server_id = str(uuid.uuid4())
        
        self._publication = None 
        self._clisrv = None
        self.closed = True
        self.stream_count = 0
        utils.debug_log("WatchServer reset", verbosity=1)

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def _clisrv_callback(self, clisrv, clisrv_req):
        utils.debug_log("Received client request", clisrv_req.req_type, verbosity=6)

        if clisrv_req.req_type == CliSrvReqTypes.create_stream:
            return self.create_stream(clisrv_req.req_data)
        elif clisrv_req.req_type == CliSrvReqTypes.heartbeat:
            self._client_heartbeats[clisrv_req.req_data] = time.time()
            return None
        elif clisrv_req.req_type == CliSrvReqTypes.del_stream:
            return self.del_stream(clisrv_req.req_data)
        elif clisrv_req.req_type == CliSrvReqTypes.print_msg:
            print(clisrv_req.req_data)
            return None
        else:
            raise ValueError('ClientServer Request Type {} is not recognized'.format(clisrv_req))
     
    def _exec_event(self, event_name:str):
        event_index = self.get_event_index(event_name)
        self._event_counts[event_name] = event_index + 1
        stream_reqs = self._event_streams.get(event_name, {})

        if len(stream_reqs) == 0:
            utils.debug_log("Executing event but no streams", event_name, verbosity=5)
        else:
            utils.debug_log("Executing event", event_name, verbosity=5)

        # TODO: remove list() call - currently needed because of error dictionary
        # can't be changed - happens when multiple clients gets started
        for stream_req in list(stream_reqs.values()):
            if stream_req.disabled:
                continue

            # throttle should be applied before eval
            if stream_req.throttle is None or stream_req.last_sent is None or \
                    time.time() - stream_req.last_sent >= stream_req.throttle:

                # check if client is still alive, bypass if client doesn't send hb
                last_hb = self._client_heartbeats.get(stream_req.client_id, 0)
                if last_hb > 0 and time.time() - last_hb > 3: #TODO: make configurable
                    utils.debug_log("Event but no heartbeat since {} from ".format(last_hb, 
                                    stream_req.client_id), event_name, verbosity=4)
                else:
                    stream_req.last_sent = time.time()
                    event_data = EventData(self._global_vars, **self._event_vars[event_name])
                    utils.debug_log("Sending event data", event_name, verbosity=5)
                    self._eval_event_send(stream_req, event_data)
            else:
                utils.debug_log("Throttled", event_name, verbosity=5)

    def _end_stream_req(self, stream_req:StreamRequest, disable_stream:bool):
        eval_return = stream_req._evaler.post(ended=True, 
            continue_thread=not disable_stream)

        event_name = stream_req.event_name
        if disable_stream:
            stream_req.disabled = True
            utils.debug_log("{} stream disabled".format(stream_req.stream_name), verbosity=1)

        eval_result = EvalResult(event_name, self.get_event_index(event_name), 
            eval_return, stream_req.stream_name, self.server_id, stream_req.stream_index, ended=True)
        self._publication.send_obj(eval_result, TopicNames.event_eval)

    def _eval_event_send(self, stream_req:StreamRequest, event_vars:EventVars):
        eval_return = stream_req._evaler.post(event_vars)
        if eval_return.is_valid:
            event_name = stream_req.event_name
            event_index = self.get_event_index(event_name)
            eval_result = EvalResult(event_name, event_index,
                eval_return, stream_req.stream_name, self.server_id, stream_req.stream_index)
            self._publication.send_obj(eval_result, TopicNames.event_eval)
            utils.debug_log("eval_return sent", event_name, verbosity=5)
        else:
            utils.debug_log("Invalid eval_return not sent", verbosity=5)

                
    def _send_heartbeat(self):
        hb = ServerMgmtMsg('HB', self.server_id)
        self._publication.send_obj(hb, TopicNames.srv_mgmt)
        utils.debug_log("Sent - SeverMgmtevent", verbosity=6)
