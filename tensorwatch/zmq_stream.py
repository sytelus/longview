from typing import Any
from .zmq_wrapper import ZmqPubSub
from .stream import Stream
from .lv_types import StreamItem, DefaultPorts, PublisherTopics
from . import utils

# on writes send data on ZMQ transport
class ZmqStream(Stream):
    def __init__(self, for_write, port_offset:int=0, topic=PublisherTopics.StreamItem, block_until_connected=True, 
                 stream_name:str=None, console_debug:bool=False):
        super(ZmqStream, self).__init__(name=stream_name, console_debug=console_debug)

        self.for_write = for_write
        self._zmq = None
        self.closed = True

        self.topic = topic
        self._open(for_write, port_offset, block_until_connected)
        utils.debug_log('ZmqStream started', verbosity=1)

    def _open(self, for_write:bool, port_offset:int, block_until_connected:bool):
        if self.closed:
            if for_write:
                self._zmq = ZmqPubSub.Publication(port=DefaultPorts.PubSub+port_offset,
                    block_until_connected=block_until_connected)
            else:
                self._zmq = ZmqPubSub.Subscription(port=DefaultPorts.PubSub+port_offset, 
                    topic=self.topic, callback=self._on_subscription_item)
            self.closed = False
        else:
            raise RuntimeError('ZmqStream is already open and must be closed before open() call')

    def close(self):
        if not self.closed:
            self._zmq.close()
            self._reset()
            utils.debug_log('ZmqStream is closed', verbosity=1)

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def _on_subscription_item(self, val:Any):
        utils.debug_log('Received subscription item', verbosity=5)
        self.write(val)

    def write(self, val:Any, topic=None):
        super(ZmqStream, self).write(val)
        if self.for_write:
            topic = topic or self.topic
            self._zmq.send_obj(val, topic)
