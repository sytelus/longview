from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
import queue

class EventData:
    def __init__(self, globals, **vars):
        if globals is not None:
            for key in globals:
                setattr(self, key, globals[key])
        for key in vars:
            setattr(self, key, vars[key])

EventsData = List[EventData]

class ClientServerRequest:
    def __init__(self, req_type:str, req_data:Any):
        self.req_type = req_type
        self.req_data = req_data

class ServerMgmtMsg:
    def __init__(self, event_name:str, event_args:Any=None):
        self.event_name = event_name
        self.event_args = event_args

class EvalResult:
    def __init__(self, event_name:str, event_index:int, result:Any, 
            stream_name:str, server_id:str, ended:bool=False):
        self.event_name = event_name
        self.result = result
        self.stream_name = stream_name
        self.event_index = event_index
        self.ended = ended
        self.server_id = server_id

EventEvalFunc = Callable[[EventsData], EvalResult]

class StreamEvent:
    class Type:
        eval_result = 'eval_result'
        reset = 'reset'

    def __init__(self, event_type, stream_name, eval_result):
        self.event_type, self.stream_name, self.eval_result = \
            event_type, stream_name, eval_result

class StreamRequest:
    def __init__(self, event_name:str, eval_f_s:str, stream_name:str, 
            eval_start:int, eval_end:int, throttle:float, client_id:str):
        self.event_name = event_name
        self.eval_f_s = eval_f_s
        self.stream_name = stream_name
        self.eval_start = eval_start
        self.eval_end = eval_end
        self.client_id = client_id

        # below will be set by server side
        self.eval_f:EventEvalFunc = None
        self.disabled = False
        self._evaler = None
        self.throttle = throttle
        self.last_sent=None

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
    def __init__(self, stream, throttle, redraw_on_end, title, 
            redraw_after, keep_old, dim_old):
        self.stream = stream
        self.throttle = throttle
        self.redraw_on_end = redraw_on_end
        self.title = title
        self.last_update = None
        self.pending_evals = queue.Queue()
        self.redraw_after = redraw_after
        self.keep_old = keep_old
        self.dim_old = dim_old
        self.redraw_countdown = redraw_after
