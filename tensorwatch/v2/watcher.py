from typing import Dict, Iterable, List, Any, Union
from .lv_types import StreamRequest, EventVars, StreamItem
from . import utils
from .evaler import Evaler
from .publisher import Publisher
import uuid
import time

class Watcher:
    class StreamInfo:
        def __init__(self, req:StreamRequest, evaler:Evaler, publisher:Publisher, 
                     index:int, disabled=False, last_sent:float=None) -> None:
            self.req, self.evaler, self.publisher = req, evaler, publisher
            self.index, self.disabled, self.last_sent = index, disabled, last_sent

    def __init__(self) -> None:
        self._reset(False)

    def _reset(self, closed:bool):
        self._event_streams:Dict[str, Dict[str, Watcher.StreamInfo]] = {}
        self._event_counts:Dict[str, int] = {}
        self._global_vars:Dict[str, Any] = {}
        self._stream_count = 0
        self.source_id = str(uuid.uuid4())
        self.closed = closed

    def close(self):
        if not self.closed:
            self._reset(True)

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def create_stream(self, stream_req:Union[StreamRequest, str], subscribers:Iterable[Publisher]=None) -> Publisher:
        if isinstance(stream_req, str):
            stream_req = StreamRequest(expr=stream_req)

        # modify expression if needed
        expr = stream_req.expr
        if not expr:
            expr = 'map(lambda x:x, l)'
        elif expr.strip().startswith('lambda '):
            expr = 'map({}, l)'.format(expr)
        # else no rewrites

        # get requests for this event
        streams = self._event_streams.get(stream_req.event_name, None)
        # if first for this event, create dictionary
        if streams is None:
            streams = self._event_streams[stream_req.event_name] = {}
        stream = streams[stream.req.stream_name] = Watcher.StreamInfo(stream_req, Evaler(expr),
                                                     Publisher(), self._stream_count)

        self._stream_count += 1

        if subscribers is not None:
            for subscriber in subscribers:
                subscriber.add_subscription(stream.publisher)

        return stream.publisher

    def set_globals(self, **vars):
        self._global_vars.update(vars)

    def observe(self, event_name:str='', **vars) -> None:
        # update event index for this event
        event_index = self.get_event_index(event_name)
        self._event_counts[event_name] = event_index + 1

        # get stream requests for this event
        streams = self._event_streams.get(event_name, {})

        # TODO: remove list() call - currently needed because of error dictionary
        # can't be changed - happens when multiple clients gets started
        for stream in list(streams.values()):
            if stream.disabled:
                continue

            # apply throttle
            if stream.req.throttle is None or stream.last_sent is None or \
                    time.time() - stream.last_sent >= stream.req.throttle:
                stream.last_sent = time.time()
                
                events_vars = EventVars(self._global_vars, **vars)
                self._eval_event_send(stream, events_vars)
            else:
                utils.debug_log("Throttled", event_name, verbosity=5)

    def _eval_event_send(self, stream, event_vars:EventVars):
        eval_return = stream.evaler.post(event_vars)
        if eval_return.is_valid:
            event_name = stream.req.event_name
            event_index = self.get_event_index(event_name)
            stream_item = StreamItem(event_name, event_index,
                eval_return.result, stream.req.stream_name, self.source_id, stream.index,
                exception=eval_return.exception)
            stream.publisher.write(stream_item)
            utils.debug_log("eval_return sent", event_name, verbosity=5)
        else:
            utils.debug_log("Invalid eval_return not sent", verbosity=5)

    def end_event(self, event_name:str='', disable_streams=False) -> None:
        streams = self._event_streams.get(event_name, {})
        for stream in streams.values():
            if not stream.disabled:
                self._end_stream_req(stream, disable_streams)

    def _end_stream_req(self, stream, disable_stream:bool):
        eval_return = stream.evaler.post(ended=True, 
            continue_thread=not disable_stream)
        # TODO: check eval_return.is_valid ?
        event_name = stream.req.event_name
        if disable_stream:
            stream.disabled = True
            utils.debug_log("{} stream disabled".format(stream.req.stream_name), verbosity=1)

        stream_item = StreamItem(event_name, self.get_event_index(event_name), 
            eval_return.result, stream.req.stream_name, self.source_id, stream.index,
            exception=eval_return.exception, ended=True)
        stream.publisher.write(stream_item)

    def get_event_index(self, event_name:str):
        return self._event_counts.get(event_name, -1)

    def del_stream(self, event_name:str, stream_name:str):
        utils.debug_log("deleting stream", stream_name)
        streams = self._event_streams.get(event_name, {})
        stream = streams[stream_name]
        stream.disabled = True
        stream.evaler.abort()
        #TODO: to enable delete we need to protect iteration in set_vars
        #del stream_reqs[stream.req.stream_name]