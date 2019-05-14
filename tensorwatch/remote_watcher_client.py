from typing import Any, Dict, Sequence
from .zmq_wrapper import ZmqWrapper
from .lv_types import CliSrvReqTypes, ClientServerRequest, DefaultPorts
from .lv_types import VisParams, PublisherTopics, ServerMgmtMsg, StreamCreateRequest
from .stream import Stream
from .zmq_mgmt_stream import ZmqMgmtStream
from . import utils
from .watcher import Watcher

class RemoteWatcherClient(Watcher):
    r"""Extends watcher to add methods so calls for create and delete stream can be sent to server.
    """
    def __init__(self, port_offset:int=0):
        super(RemoteWatcherClient, self).__init__()
        self.port_offset = port_offset
        self._open(port_offset)

    def _reset(self):
        self._zmq_srvmgmt_sub = None
        # client-server sockets allows to send create/del stream requests
        self._clisrv = None
        utils.debug_log("RemoteWatcherClient reset", verbosity=1)
        super(RemoteWatcherClient, self)._reset()

    def _open(self, port_offset:int):
        self._clisrv = ZmqWrapper.ClientServer(port=DefaultPorts.CliSrv+port_offset, 
            is_server=False)
        # create subscription where we will receive server management events
        self._zmq_srvmgmt_sub = ZmqMgmtStream(clisrv=self._clisrv, for_write=False, port_offset=port_offset,
            stream_name='zmq_sub:'+str(port_offset), topic=PublisherTopics.ServerMgmt)
    
    def close(self):
        if not self.closed:
            self._zmq_srvmgmt_sub.close()
            self._clisrv.close()
            utils.debug_log("RemoteWatcherClient is closed", verbosity=1)
        super(RemoteWatcherClient, self).close()

    # override to send request to server
    def create_stream(self, stream_name:str=None, devices:Sequence[str]=['tcp'], event_name:str='',
        expr=None, throttle:float=1, vis_params:VisParams=None)->Stream:

        stream_req = StreamCreateRequest(stream_name=stream_name, devices=devices, event_name=event_name,
            expr=expr, throttle=throttle, vis_params=vis_params)

        self._zmq_srvmgmt_sub.add_stream_req(stream_req)

        if stream_req.devices is not None:
            stream = self.open_stream(stream_name=stream_req.stream_name, 
                devices=stream_req.devices, event_name=stream_req.event_name)
        else: # we cannot return remote streams that are not backed by a device
            stream = None
        return stream

    # override to send request to server
    def del_stream(self, stream_name:str) -> None:
        self._zmq_srvmgmt_sub.del_stream(stream_req)

