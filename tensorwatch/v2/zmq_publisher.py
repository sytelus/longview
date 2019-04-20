from typing import Any
from .zmq_pub_sub import ZmqPubSub
from .publisher import Publisher
from .lv_types import StreamItem
from . import utils

# on writes send data on ZMQ transport
class ZmqPublisher(Publisher):
    DefaultPubSubPort = 40859
    DefaultTopic = 'StreamItem'

    def __init__(self, port_offset:int=0, topic=DefaultTopic, name:str=None, console_debug:bool=False):
        super(ZmqPublisher, self).__init__(name=name, console_debug=console_debug)

        self._reset()
        self.topic = topic
        self._open(port_offset)
        utils.debug_log('ZmqPublisher started', verbosity=1)

    def _reset(self):
        self._publication = None 
        self.closed = True
        utils.debug_log('ZmqPublisher reset', verbosity=1)

    def _open(self, port_offset:int):
        if self.closed:
            self._publication = ZmqPubSub.Publication(port = ZmqPublisher.DefaultPubSubPort+(port_offset or 0))
            self.closed = False
        else:
            raise RuntimeError('ZmqPublisher is already open and must be closed before open() call')

    def close(self):
        if not self.closed:
            self._publication.close()
            self._reset()
            utils.debug_log('ZmqPublisher is closed', verbosity=1)

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def write(self, val:Any):
        super(ZmqPublisher, self).write(val)
        self._publication.send_obj(val, self.topic)