from .publisher import Publisher
from typing import Callable, Any

class FilteredStream(Publisher):
    def __init__(self, source_publisher:Publisher, filter_expr:Callable, publisher_name:str=None, console_debug:bool=False)->None:
        super(FilteredStream, self).__init__(name=publisher_name, console_debug=console_debug)
        source_publisher.add_subscriber(self)
        self.filter_expr = filter_expr

    def write(self, val:Any):
        result, is_valid = self.filter_expr(val)
        if is_valid:
            return super(FilteredStream, self).write(val)
            
