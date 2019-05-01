from .stream import Stream
from typing import Callable, Any

class FilteredStream(Stream):
    def __init__(self, source_stream:Stream, filter_expr:Callable, stream_name:str=None, console_debug:bool=False)->None:
        super(FilteredStream, self).__init__(stream_name=stream_name, console_debug=console_debug)
        self.subscribe(source_stream)
        self.filter_expr = filter_expr

    def write(self, val:Any):
        result, is_valid = self.filter_expr(val)
        if is_valid:
            return super(FilteredStream, self).write(val)
            
