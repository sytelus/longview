from .publisher import Publisher
from .lv_types import StreamItem

class ArrayPublisher(Publisher):
    def __init__(self, array, stream_name:str=None, 
                 publisher_name:str=None, console_debug:bool=False):
        super(ArrayPublisher, self).__init__(name=publisher_name, console_debug=console_debug)

        self.stream_name = stream_name
        self.array = array

    def send_all(self):
        if self.array is not None:
            stream_item = StreamItem(item_index=0, value=self.array,
                stream_name=self.stream_name, source_id='', stream_index=0)
            self.write(stream_item)