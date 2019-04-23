from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from . import utils
import uuid


class EventVars:
    def __init__(self, globals, **vars):
        if globals is not None:
            for key in globals:
                setattr(self, key, globals[key])
        for key in vars:
            setattr(self, key, vars[key])

    def __str__(self):
        sb = []
        for key in self.__dict__:
            val = self.__dict__[key]
            if utils.is_scalar(val):
                sb.append('{key}={value}'.format(key=key, value=val))
            else:
                sb.append('{key}="{value}"'.format(key=key, value=val))
 
        return ', '.join(sb)

EventsVars = List[EventVars]

class StreamItem:
    def __init__(self, item_index:int, value:Any,
            stream_name:str, source_id:str, stream_index:int,
            ended:bool=False, exception:Exception=None, stream_reset:bool=False):
        self.value = value
        self.exception = exception
        self.stream_name = stream_name
        self.item_index = item_index
        self.ended = ended
        self.source_id = source_id
        self.stream_index = stream_index
        self.stream_reset = stream_reset

    def __repr__(self):
        return str(self.__dict__)

EventEvalFunc = Callable[[EventsVars], StreamItem]

class StreamRequest:
    def __init__(self, expr:str, event_name:str='', stream_name:str=None, 
            throttle:float=None, client_id:str=None):
        self.event_name = event_name
        self.expr = expr
        self.stream_name = stream_name or str(uuid.uuid4())
        # used to detect if client no longer exist in which case don't publish for them
        self.client_id = client_id 

        # max throughput n Lenovo P50 laptop for MNIST
        # text console -> 0.1s
        # matplotlib line graph -> 0.5s
        self.throttle = throttle

class ClientServerRequest:
    def __init__(self, req_type:str, req_data:Any):
        self.req_type = req_type
        self.req_data = req_data

class CliSrvReqTypes:
    create_stream = 'CreateStream'
    del_stream = 'DeleteStream'

class StreamPlot:
    def __init__(self, stream, throttle, title, clear_after_end, 
                clear_after_each, history_len, dim_history, opacity,
                index, stream_plot_args, last_update):
        self.stream = stream
        self.throttle = throttle
        self.title, self.opacity = title, opacity
        self.clear_after_end, self.clear_after_each = clear_after_end, clear_after_each
        self.history_len, self.dim_history = history_len, dim_history
        self.index, self.stream_plot_args, self.last_update = index, stream_plot_args, last_update

class ImagePlotItem:
    def __init__(self, images=None, title=None, alpha=None, cmap=None):
        if not isinstance(images, tuple):
            images = (images,)
        self.images, self.alpha, self.cmap, self.title = images, alpha, cmap, title

class DefaultPorts:
    PubSub = 40859
    CliSrv = 41459

class PublisherTopics:
    StreamItem = 'StreamItem'
    ServerMgmt = 'ServerMgmt'

class ServerMgmtMsg:
    EventServerStart = 'ServerStart'
    def __init__(self, event_name:str, event_args:Any=None):
        self.event_name = event_name
        self.event_args = event_args