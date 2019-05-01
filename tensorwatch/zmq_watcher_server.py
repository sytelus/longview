from typing import Any
import uuid
from .zmq_wrapper import ZmqPubSub
from .watcher import Watcher
from .stream_factory import StreamFactory
from .lv_types import StreamItem, StreamRequest, CliSrvReqTypes, DefaultPorts, PublisherTopics, ServerMgmtMsg
from . import utils
import threading, time

class ZmqWatcherServer(Watcher):
    def __init__(self, port_offset:int=0, srv_name:str=None):
        super(ZmqWatcherServer, self).__init__()
        self.srv_name = srv_name or str(uuid.uuid4()) # used to detect server restarts 
        self._stream_factory = StreamFactory()
        self._open(port_offset)

    def _open(self, port_offset:int):
        self._clisrv = ZmqPubSub.ClientServer(port=DefaultPorts.CliSrv+port_offset, 
            is_server=True, callback=self._clisrv_callback)

        # notify existing listeners of our ID
        self._zmq_stream_pub = self._stream_factory.create_stream('zmqpub')

        # ZMQ quirk: we must wait a bit after opening port and before sending message
        # TODO: can we do better?
        self._th = threading.Thread(target=self._send_server_start)
        self._th.start()

    def _send_server_start(self):
        time.sleep(2)
        self._zmq_stream_pub.write(ServerMgmtMsg(ServerMgmtMsg.EventServerStart, self.srv_name), 
                                  topic=PublisherTopics.ServerMgmt)

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
            subscribers = [self._stream_factory.create_stream(subscriber_spec) for subscriber_spec in subscriber_specs]
            self.create_stream(stream_req, subscribers) # ignore return as we can't send back stream obj
            return None
        elif clisrv_req.req_type == CliSrvReqTypes.del_stream:
            stream_name:str = clisrv_req.req_data
            return self.del_stream(stream_name)
        else:
            raise ValueError('ClientServer Request Type {} is not recognized'.format(clisrv_req))