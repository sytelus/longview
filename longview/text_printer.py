from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *
from . import utils

class TextPrinter():
    def __init__(self, prefix=''):
        self.prefix = prefix
    def _add_eval_result(self, eval_result:EvalResult, stream_reset:bool):
        print("{}- i:{}, ended:{}, result:{}, reset:{}".format(self.prefix, 
            eval_result.event_index, eval_result.ended, eval_result.result, stream_reset))
    def show(self, *streams):
        for stream in streams:
            stream.subscribe(self._add_eval_result)
