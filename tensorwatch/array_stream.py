from .stream import Stream
from .lv_types import StreamItem
import uuid

class ArrayStream(Stream):
    def __init__(self, array, stream_name:str=None, console_debug:bool=False):
        super(ArrayStream, self).__init__(stream_name=stream_name, console_debug=console_debug)

        self.stream_name = stream_name
        self.array = array
        self.creator_id = str(uuid.uuid4())


    def load(self, from_stream:'Stream'=None):
        if self.array is not None:
            stream_item = StreamItem(item_index=0, value=self.array,
                stream_name=self.stream_name, creator_id=self.creator_id, stream_index=0)
            self.write(stream_item)