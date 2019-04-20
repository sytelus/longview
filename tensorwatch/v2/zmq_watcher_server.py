from typing import Any
from .zmq_pub_sub import ZmqPubSub
from .watcher import Watcher
from .publisher_factory import PublisherFactory
from .lv_types import StreamItem, StreamRequest, CliSrvReqTypes
from . import utils

class ZmqWatcherServer(Watcher):
    DefaultCliSrvPort = 41459

    def __init__(self, port_offset:int=None):
        super(ZmqWatcherServer, self).__init__()
        self._publisher_factory = PublisherFactory()
        self._open()

    def _open(self, port_offset:int=None):
        self._clisrv = ZmqPubSub.ClientServer(port=ZmqWatcherServer.DefaultCliSrvPort+(port_offset or 0), 
            is_server=True, callback=self._clisrv_callback)

    def close(self):
        if not self.closed:
            self._clisrv.close()
            utils.debug_log("ZmqWatcherServer is closed", verbosity=1)
        super(ZmqWatcherServer, self).close()

    def _reset(self, closed:bool):
        super(ZmqWatcherServer, self)._reset(closed)
        self._clisrv = None
        utils.debug_log("ZmqWatcherServer reset", verbosity=1)

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def _clisrv_callback(self, clisrv, clisrv_req):
        utils.debug_log("Received client request", clisrv_req.req_type)

        if clisrv_req.req_type == CliSrvReqTypes.create_stream:
            stream_req, subscriber_specs = clisrv_req.req_data
            subscriber_specs = subscriber_specs if subscriber_specs is not None else []
            subscribers = [self._publisher_factory.create_publisher(subscriber_spec) for subscriber_spec in subscriber_specs]
            return self.create_stream(stream_req, subscribers)
        elif clisrv_req.req_type == CliSrvReqTypes.del_stream:
            stream_name:str = clisrv_req.req_data
            return self.del_stream(stream_name)
        else:
            raise ValueError('ClientServer Request Type {} is not recognized'.format(clisrv_req))