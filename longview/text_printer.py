from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *
from . import utils

class TextPrinter():
    def __init__(self):
        self.prefix = prefix
    def _add_eval_result(self, eval_result:EvalResult):
        print(self.prefix, eval_result.event_index, eval_result.ended, eval_result.result)
    def show(self, *streams):
        for stream in streams:
            stream.subscribe(self._add_eval_result)
