from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
import queue
from . import utils

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

class ClientServerRequest:
    def __init__(self, req_type:str, req_data:Any):
        self.req_type = req_type
        self.req_data = req_data

class ServerMgmtMsg:
    def __init__(self, event_name:str, event_args:Any=None):
        self.event_name = event_name
        self.event_args = event_args

class EvalReturn:
    def __init__(self, result=None, is_valid=False, exception=None):
        self.result, self.exception, self.is_valid = \
            result, exception, is_valid
    def reset(self):
        self.result, self.exception, self.is_valid = \
            None, None, False

class EvalResult:
    def __init__(self, event_name:str, event_index:int, eval_return:EvalReturn,
            stream_name:str, server_id:str, stream_index:int, ended:bool=False):
        self.event_name = event_name
        self.result = eval_return.result
        self.exception = eval_return.exception
        self.stream_name = stream_name
        self.event_index = event_index
        self.ended = ended
        self.server_id = server_id
        self.stream_index = stream_index

EventEvalFunc = Callable[[EventsVars], EvalResult]

class StreamEvent:
    class Type:
        eval_result = 'eval_result'
        reset = 'reset'

    def __init__(self, event_type, stream_name, eval_result):
        self.event_type, self.stream_name, self.eval_result = \
            event_type, stream_name, eval_result

    def display_name(self):
        if not utils.is_uuid4(self.stream_name) or self.eval_result is None:
            return self.stream_name  
        else:
           return str(self.eval_result.stream_index)

class StreamRequest:
    def __init__(self, event_name:str, eval_expr:str, stream_name:str, 
            throttle:float, client_id:str, stream_index:int=None):
        self.event_name = event_name
        self.eval_expr = eval_expr
        self.stream_name = stream_name
        self.client_id = client_id

        # below will be set by server side
        self.eval_f:EventEvalFunc = None
        self.disabled = False
        self._evaler = None
        self.throttle = throttle
        self.last_sent=None
        self.stream_index = stream_index

StreamRequests = Dict[str, StreamRequest] 

class TopicNames:
    event_eval = 'EventEval'
    srv_mgmt = 'ServerMgmt'

class CliSrvReqTypes:
    create_stream = 'CreateStream'
    del_stream = 'DeleteStream'
    print_msg = 'PrintMsg'
    heartbeat = 'Heartbeat'

class StreamPlot:
    def __init__(self, stream, throttle, title, clear_after_end, 
                clear_after_each, history_len, dim_history, opacity):
        self.stream = stream
        self.throttle = throttle
        self.title, self.opacity = title, opacity
        self.clear_after_end, self.clear_after_each = clear_after_end, clear_after_each
        self.history_len, self.dim_history = history_len, dim_history

