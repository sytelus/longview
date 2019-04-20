from .publisher import Publisher
from .lv_types import StreamItem


class FilteredStream(Publisher):
    def __init__(self, source_publisher:Publisher, filter_stream_name:str, publisher_name:str=None, console_debug:bool=False)->None:
        super(FilteredStream, self).__init__(name=publisher_name, console_debug=console_debug)
        source_publisher.add_subscriber(self)
        self.filter_stream_name = filter_stream_name

    def write(self, stream_item:StreamItem):
        if stream_item.stream_name == self.filter_stream_name:
            super(FilteredStream, self).write(stream_item)
