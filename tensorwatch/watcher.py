from typing import Dict, Iterable, List, Any, Union, Sequence
from .lv_types import EventVars, StreamItem, StreamCreateRequest, VisParams
from . import utils
from .evaler import Evaler
from .stream import Stream
from .stream_factory import StreamFactory
from .filtered_stream import FilteredStream
import uuid
import time
from . import utils


class Watcher:
    class StreamInfo:
        def __init__(self, req:StreamCreateRequest, evaler:Evaler, stream:Stream, 
                     index:int, disabled=False, last_sent:float=None)->None:
            r"""Holds togaher stream_req, stream and evaler
            """
            self.req, self.evaler, self.stream = req, evaler, stream
            self.index, self.disabled, self.last_sent = index, disabled, last_sent
            self.item_count = 0 # creator of StreamItem needs to set to set item num

    def __init__(self) -> None:
        self._reset()

    def _reset(self):
        # for each event, store (stream_name, stream_info)
        self._stream_infos:Dict[str, Dict[str, Watcher.StreamInfo]] = {}

        self._global_vars:Dict[str, Any] = {}
        self._stream_count = 0

        # factory streams are shared per watcher instance
        self._stream_factory = StreamFactory()

        # each StreamItem should be stamped by its creator
        self.creator_id = str(uuid.uuid4())
        self.closed = False

    def close(self):
        if not self.closed:
            # close all the streams
            for stream_infos in self._stream_infos.values(): # per event
                for stream_info in stream_infos.values():
                    stream_info.stream.close()
            self._stream_factory.close()
            self._reset() # clean variables
            self.closed = True

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def open_stream(self, stream_name:str=None, devices:Sequence[str]=None, 
                 event_name:str='')->Stream:
        r"""Opens stream from specified devices or returns one by name if
        it was created before.
        """
        # TODO: what if devices were specified AND stream exist in cache?

        # create devices is any
        devices:Sequence[str] = None
        if devices is not None:
            # we open devices in read-only mode
            devices = self._stream_factory.get_streams(stream_types=devices, 
                                                       for_write=False)
        # if no devices then open stream by name from cache
        if devices is None:
            if stream_name is None:
                raise ValueError('Both devices and stream_name cannot be None')

            # first search by event
            stream_infos = self._stream_infos.get(event_name, None)
            if stream_infos is None:
                raise ValueError('Requested event was not found: ' + event_name)
            # then search by stream name
            stream_info = stream_infos.get(stream_name, None)
            if stream_info is None:
                raise ValueError('Requested stream was not found: ' + stream_name)
            return stream_info.stream
        
        # if we have devices, first create stream and then attach devices to it
        stream = Stream(stream_name=stream_name)
        for device in devices:
            # each device may have multiple streams so let's filter it
            device_stream = FilteredStream(device, 
                (lambda steam_item: (steam_item, steam_item.stream_name == stream_name))) \
                    if stream_name is not None \
                    else None
            stream.subscribe(device_stream)
        return stream

    def create_stream(self, stream_name:str=None, devices:Sequence[str]=None, event_name:str='',
        expr=None, throttle:float=None, vis_params:VisParams=None)->Stream:

        r"""Create stream with or without expression and attach to devices where 
        it will be written to.
        """

        stream_name = stream_name or str(uuid.uuid4())

        # we allow few shortcuts, so modify expression if needed
        expr = expr
        if expr=='' or expr=='x':
            expr = 'map(lambda x:x, l)'
        elif expr.strip().startswith('lambda '):
            expr = 'map({}, l)'.format(expr)
        # else no rewrites

        # if no expression specified then we don't create evaler
        evaler = Evaler(expr) if expr is not None else None

        # get stream infos for this event
        stream_infos = self._stream_infos.get(event_name, None)
        # if first for this event, create dictionary
        if stream_infos is None:
            stream_infos = self._stream_infos[event_name] = {}

        stream_info = stream_infos.get(stream_name, None)
        if not stream_info:
            utils.debug_log("Creating stream", stream_name)
            stream = Stream(stream_name=stream_name)
            devices:Sequence[str] = None
            if devices is not None:
                # attached devices are opened in write-only mode
                devices = self._stream_factory.get_streams(stream_types=devices, 
                                                           for_write=True)
                for device in devices:
                    device.subscribe(stream)
            stream_req = StreamCreateRequest(stream_name=stream_name, devices=devices, event_name=event_name,
                     expr=expr, throttle=throttle, vis_params=vis_params)
            stream_info = stream_infos[stream_name] = Watcher.StreamInfo(
                stream_req, evaler, stream, self._stream_count)
            self._stream_count += 1
        else:
            # TODO: throw error?
            utils.debug_log("Stream already exist, not creating again", stream_name)

        return stream_info.stream

    def set_globals(self, **vars):
        self._global_vars.update(vars)

    def observe(self, event_name:str='', **vars) -> None:
        # get stream requests for this event
        stream_infos = self._stream_infos.get(event_name, {})

        # TODO: remove list() call - currently needed because of error dictionary
        # can't be changed - happens when multiple clients gets started
        for stream_info in list(stream_infos.values()):
            if stream_info.disabled or stream_info.evaler is None:
                continue

            # apply throttle
            if stream_info.req.throttle is None or stream_info.last_sent is None or \
                    time.time() - stream_info.last_sent >= stream_info.req.throttle:
                stream_info.last_sent = time.time()
                
                events_vars = EventVars(self._global_vars, **vars)
                self._eval_wrie(stream_info, events_vars)
            else:
                utils.debug_log("Throttled", event_name, verbosity=5)

    def _eval_wrie(self, stream_info:Watcher.StreamInfo, event_vars:EventVars):
        eval_return = stream_info.evaler.post(event_vars)
        if eval_return.is_valid:
            event_name = stream_info.req.event_name
            stream_item = StreamItem(stream_info.item_count,
                eval_return.result, stream_info.req.stream_name, self.creator_id, stream_info.index,
                exception=eval_return.exception)
            stream_info.stream.write(stream_item)
            stream_info.item_count += 1
            utils.debug_log("eval_return sent", event_name, verbosity=5)
        else:
            utils.debug_log("Invalid eval_return not sent", verbosity=5)

    def end_event(self, event_name:str='', disable_streams=False) -> None:
        stream_infos = self._stream_infos.get(event_name, {})
        for stream_info in stream_infos.values():
            if not stream_info.disabled:
                self._end_stream_req(stream_info, disable_streams)

    def _end_stream_req(self, stream_info:Watcher.StreamInfo, disable_stream:bool):
        eval_return = stream_info.evaler.post(ended=True, 
            continue_thread=not disable_stream)
        # TODO: check eval_return.is_valid ?
        event_name = stream_info.req.event_name
        if disable_stream:
            stream_info.disabled = True
            utils.debug_log("{} stream disabled".format(stream_info.req.stream_name), verbosity=1)

        stream_item = StreamItem(item_index=stream_info.item_count, 
            value=eval_return.result, stream_name=stream_info.req.stream_name, 
            creator_id=self.creator_id, stream_index=stream_info.index,
            exception=eval_return.exception, ended=True)
        stream_info.stream.write(stream_item)
        stream_info.item_count += 1

    def del_stream(self, stream_name:str) -> None:
        utils.debug_log("deleting stream", stream_name)
        for stream_infos in self._stream_infos.values(): # per event
            stream_info = stream_infos.get(stream_name, None)
            if stream_info:
                stream_info.disabled = True
                stream_info.evaler.abort()
                return True
                #TODO: to enable delete we need to protect iteration in set_vars
                #del stream_reqs[stream_info.req.stream_name]
        return False