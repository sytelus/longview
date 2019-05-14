import uuid
from .zmq_wrapper import ZmqWrapper
from .watcher_base import WatcherBase
from .lv_types import CliSrvReqTypes
from .lv_types import DefaultPorts, PublisherTopics, ServerMgmtMsg
from . import utils
import threading, time

class Watcher(WatcherBase):
    def __init__(self, port_offset:int=0, srv_name:str=None):
        super(Watcher, self).__init__()

        # used to detect server restarts 
        self.srv_name = srv_name or str(uuid.uuid4())
        
        # define vars in __init__
        self._clisrv = None
        self._zmq_stream_pub = None
        self._th = None

        if port_offset is not None:
            self._open(port_offset)

    def _open(self, port_offset:int):
        self._clisrv = ZmqWrapper.ClientServer(port=DefaultPorts.CliSrv+port_offset, 
            is_server=True, callback=self._clisrv_callback)

        # notify existing listeners of our ID
        self._zmq_stream_pub = self._stream_factory.get_streams(stream_types=['tcp:'+str(port_offset)], for_write=True)[0]

        # ZMQ quirk: we must wait a bit after opening port and before sending message
        # TODO: can we do better?
        self._th = threading.Thread(target=self._send_server_start)
        self._th.start()

    def _send_server_start(self):
        time.sleep(2)
        self._zmq_stream_pub.write(ServerMgmtMsg(event_name=ServerMgmtMsg.EventServerStart, 
            event_args=self.srv_name), topic=PublisherTopics.ServerMgmt)

    def close(self):
        if not self.closed:
            if self._clisrv is not None:
                self._clisrv.close()
            if self._zmq_stream_pub is not None:
                self._zmq_stream_pub.close()
            utils.debug_log("Watcher is closed", verbosity=1)
        super(Watcher, self).close()

    def _reset(self):
        self._clisrv = None
        self._zmq_stream_pub = None
        self._th = None
        utils.debug_log("Watcher reset", verbosity=1)
        super(Watcher, self)._reset()

    def _clisrv_callback(self, clisrv, clisrv_req): # pylint: disable=unused-argument
        utils.debug_log("Received client request", clisrv_req.req_type)

        # request = create stream
        if clisrv_req.req_type == CliSrvReqTypes.create_stream:
            stream_req = clisrv_req.req_data
            self.create_stream(stream_name=stream_req.stream_name, devices=stream_req.devices, 
                event_name=stream_req.event_name, expr=stream_req.expr, throttle=stream_req.throttle, 
                vis_params=stream_req.vis_params)
            return None # ignore return as we can't send back stream obj
        elif clisrv_req.req_type == CliSrvReqTypes.del_stream:
            stream_name = clisrv_req.req_data
            return self.del_stream(stream_name)
        else:
            raise ValueError('ClientServer Request Type {} is not recognized'.format(clisrv_req))