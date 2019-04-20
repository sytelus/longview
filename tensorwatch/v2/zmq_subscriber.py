from typing import Any
from .zmq_pub_sub import ZmqPubSub
from .publisher import Publisher
from .lv_types import StreamItem
from . import utils

# on writes send data on ZMQ transport
class ZmqSubscriber(Publisher):
    DefaultPubSubPort = 40859
    DefaultTopic = 'StreamItem'

    def __init__(self, port_offset:int=0, topic=DefaultTopic, name:str=None, console_debug:bool=False):
        super(ZmqSubscriber, self).__init__(name=name, console_debug=console_debug)

        self._reset()
        self.topic = topic
        self._open(port_offset)
        utils.debug_log('ZmqSubscriber started', verbosity=1)

    def _reset(self):
        self._subscription = None 
        self.closed = True
        utils.debug_log('ZmqSubscriber reset', verbosity=1)

    def _open(self, port_offset:int):
        if self.closed:
            self._subscription = ZmqPubSub.Subscription(port=ZmqSubscriber.DefaultPubSubPort+(port_offset or 0), 
                                                       topic=self.topic, callback=self._on_subscription_item)
            self.closed = False
        else:
            raise RuntimeError('ZmqSubscriber is already open and must be closed before open() call')

    def close(self):
        if not self.closed:
            self._subscription.close()
            self._reset()
            utils.debug_log('ZmqPublisherServer is closed', verbosity=1)

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def _on_subscription_item(self, stream_item:StreamItem):
        utils.debug_log('Received stream_item', verbosity=5)
        self.write(stream_item)
