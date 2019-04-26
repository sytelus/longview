from typing import Any
from .zmq_pub_sub import ZmqPubSub
from .stream import Stream
from .lv_types import StreamItem, DefaultPorts, PublisherTopics
from . import utils

# on writes send data on ZMQ transport
class ZmqStreamPub(Stream):
    def __init__(self, port_offset:int=0, default_topic=PublisherTopics.StreamItem, block_until_connected=True, name:str=None, console_debug:bool=False):
        super(ZmqStreamPub, self).__init__(name=name, console_debug=console_debug)

        self._reset()
        self.default_topic = default_topic
        self._open(port_offset, block_until_connected)
        utils.debug_log('ZmqStreamPub started', verbosity=1)

    def _reset(self):
        self._publication = None 
        self.closed = True
        utils.debug_log('ZmqStreamPub reset', verbosity=1)

    def _open(self, port_offset:int, block_until_connected:bool):
        if self.closed:
            self._publication = ZmqPubSub.Publication(port=DefaultPorts.PubSub+port_offset,
                                                      block_until_connected=block_until_connected)
            self.closed = False
        else:
            raise RuntimeError('ZmqStreamPub is already open and must be closed before open() call')

    def close(self):
        if not self.closed:
            self._publication.close()
            self._reset()
            utils.debug_log('ZmqStreamPub is closed', verbosity=1)

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def write(self, val:Any, topic=None):
        super(ZmqStreamPub, self).write(val)
        topic = topic or self.default_topic
        self._publication.send_obj(val, topic)