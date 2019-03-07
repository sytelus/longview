from .stream_base import StreamBase
from .lv_types import *

class ArrayStream(StreamBase):
    def __init__(self, array, stream_name:str=None, throttle=None, event_name:str=''):
        super(self, Stream).__init__(stream_name, throttle)
        self.array = array
        self.event_name = event_name

    def send_all(self):
        if self.array is not None:
            eval_return = EvalReturn(result=self.array, is_valid=True)
            eval_result = EvalResult(event_name=self.event_name, event_index=0, eval_return=eval_return,
                stream_name=self.stream_name, server_id='', stream_index=0, ended=False)
            self.send_data(eval_result)