from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .zmq_pub_sub import ZmqPubSub
import threading
from .lv_types import *
from .evaler import Evaler
import time

class WatchServer:
    _port_start = 40859
    def __init__(self, pubsub_port:int=None, cliesrv_port:int=None):
        self._reset()
        self.open(pubsub_port, cliesrv_port)
        print("WatchServer started")

    def open(self, pubsub_port:int=None, cliesrv_port:int=None):
        if self.closed:
            self._publication = ZmqPubSub.Publication(port = pubsub_port or WatchServer._port_start)
            self._clisrv = ZmqPubSub.ClientServer(cliesrv_port or WatchServer._port_start+1, 
                True, callback=self._clisrv_callback)
            WatchServer._port_start += 2
            self.closed = False
        else:
            raise RuntimeError("WatchServer is already open and must be closed before opne() call")

    def _reset(self):
        self._event_streams:Dict[str, StreamRequests] = {}
        self._event_counts:Dict[str, int] = {}
        self._stream_req_count = 0
        self._log_globals = {}

        self._publication = None 
        self._clisrv = None
        self.closed = True

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def _clisrv_callback(self, clisrv, clisrv_req):
        if clisrv_req.req_type == CliSrvReqTypes.create_stream:
            return self.create_stream(clisrv_req.req_data)
        elif clisrv_req.req_type == CliSrvReqTypes.del_stream:
            return self.del_stream(clisrv_req.req_data)
        else:
            raise ValueError('ClientServer Request Type {} is not recognized'.format(clisrv_req))

    def log_globals(self, **vars):
        self._log_globals.update(vars)

    def log_event(self, event_name:str='', x=None, **vars) -> None:
        event_index = self.get_event_index(event_name)
        self._event_counts[event_name] = event_index + 1

        stream_reqs = self._event_streams.get(event_name, {})
        # TODO: remove list() call - currently needed because of error dictionary
        # can't be changed - happens when multiple clients gets started
        for stream_req in list(stream_reqs.values()):
            if stream_req.ended:
                continue
            if stream_req.eval_end < event_index:
                self._end_stream_req(stream_req)
            else:
                # throttle should be applied before eval
                if stream_req.throttle is None or stream_req.last_sent is None or \
                        time.time() - stream_req.last_sent >= stream_req.throttle:
                    event_data = EventData(self._log_globals, **vars)
                    self._eval_event_send(stream_req, event_data, x)
                    stream_req.last_sent = time.time()

    def get_event_index(self, event_name:str):
        return self._event_counts.get(event_name, -1)

    def end_event(self, event_name:str='', disable_streams=False) -> None:
        stream_reqs = self._event_streams.get(event_name, {})
        for stream_req in stream_reqs.values():
            self._end_stream_req(stream_req, disable_streams)
     
    def _end_stream_req(self, stream_req:StreamRequest, disable_stream:bool):
        result, has_result = stream_req._evaler.post(ended=True, continue_thread=disable_stream)
        event_name = stream_req.event_name
        if disable_stream:
            stream_req.ended = True
            print("{} stream disabled".format(stream_req.stream_name))
        eval_result = EvalResult(event_name, self.get_event_index(event_name), 
            result, stream_req.stream_name, ended=True)
        self._publication.send_obj(eval_result, TopicNames.event_eval)

    def del_stream(self, stream_req:StreamRequest):
        stream_reqs = self._event_streams.get(stream_req.event_name, {})
        stream_req = stream_reqs[stream_req.stream_name]
        stream_req.ended = True
        stream_req._evaler.abort()
        #TODO: to enable delete we need to protect iteration in log_event
        #del stream_reqs[stream_req.stream_name]
        print("{} stream deleted".format(stream_req.stream_name))
        return stream_req.stream_num

    def _eval_event_send(self, stream_req:StreamRequest, event_data:EventData, x=None):
        result, has_result = stream_req._evaler.post(event_data)
        if has_result:
            event_name = stream_req.event_name
            event_index = self.get_event_index(event_name)
            eval_result = EvalResult(event_name, event_index,
                result, stream_req.stream_name, x=x)
            self._publication.send_obj(eval_result, TopicNames.event_eval)
                
    def create_stream(self, stream_req:StreamRequest) -> int:
        stream_req._evaler = Evaler(stream_req.eval_f_s)
        stream_req.stream_num = self._stream_req_count
        self._stream_req_count += 1

        if stream_req.eval_start < 0:
            stream_req.eval_start += events_len
        if stream_req.eval_end < 0:
            stream_req.eval_end += events_len

        event_index = self.get_event_index(stream_req.event_name)
        if stream_req.eval_end >= event_index:
            stream_reqs = self._event_streams.get(stream_req.event_name, None)
            if stream_reqs is None:
                stream_reqs = self._event_streams[stream_req.event_name] = {}
            stream_reqs[stream_req.stream_name] = stream_req

        return stream_req.stream_num

    def close(self):
        if not self.closed:
            ZmqPubSub.close()
            self._reset()
            print("WatchServer is closed")

    def send_text(self, text:str, topic=""):
        self._publication.send_obj(text, topic)