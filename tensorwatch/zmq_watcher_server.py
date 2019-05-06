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
        self._zmq_stream_pub = self._stream_factory.get_stream(stream_types=['tcp'], for_write=True)

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

    def _reset(self):
        super(ZmqWatcherServer, self)._reset(closed)
        self._clisrv = None
        utils.debug_log("ZmqWatcherServer reset", verbosity=1)

    def _clisrv_callback(self, clisrv, clisrv_req):
        utils.debug_log("Received client request", clisrv_req.req_type)

        if clisrv_req.req_type == CliSrvReqTypes.get_stream:
            stream_req, srv_subscriber_specs = clisrv_req.req_data
            stream = self.get_stream(stream_req) 
            srv_subscriber_specs = srv_subscriber_specs if srv_subscriber_specs is not None else []
            for srv_subscriber_spec in srv_subscriber_specs:
                srv_subscriber = self._stream_factory.get_stream(for_write=True, srv_subscriber_spec)
                srv_subscriber.subscribe(stream)
            return None # ignore return as we can't send back stream obj
        elif clisrv_req.req_type == CliSrvReqTypes.del_stream:
            stream_name:str = clisrv_req.req_data
            return self.del_stream(stream_name)
        else:
            raise ValueError('ClientServer Request Type {} is not recognized'.format(clisrv_req))