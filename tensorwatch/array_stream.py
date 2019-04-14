from .stream import Stream
from .lv_types import *

class ArrayStream(Stream):
    def __init__(self, array, stream_name:str=None, throttle=None, event_name:str='',
                 annotations=None, texts=None, colors=None):
        super(ArrayStream, self).__init__(stream_name, throttle)

        self.array = array
        self.event_name = event_name

    def send_all(self):
        if self.array is not None:
            stream_item = StreamItem(event_name=self.event_name, event_index=0, value=self.array,
                stream_name=self.stream_name, source_id='', stream_index=0)
            self.send_data(stream_item)