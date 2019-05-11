from typing import Any, Dict, Union, List, Tuple, Iterable
import uuid
from .zmq_wrapper import ZmqPubSub
from .lv_types import StreamItem, StreamRequest, CliSrvReqTypes, ClientServerRequest, DefaultPorts, PublisherTopics, ServerMgmtMsg
from .stream import Stream
from .zmq_stream import ZmqStream
from . import utils

class ZmqWatcherClient(Watcher):
    r"""Extends watcher to add methods so calls for create and delete stream can be sent to server.
    """
    def __init__(self, port_offset:int=0):
        super(ZmqWatcherClient, self).__init__()
        self.port_offset = port_offset
        self._open(port_offset)

    def _reset(self):
        self._zmq_srvmgmt_sub = None
        # client-server sockets allows to send create/del stream requests
        self._clisrv = None
        self._stream_reqs:Dict[str,StreamRequest] = {}
        utils.debug_log("ZmqWatcherClient reset", verbosity=1)
        super(ZmqWatcherClient, self)._reset()

    def _open(self, port_offset:int):
        self._clisrv = ZmqPubSub.ClientServer(port=DefaultPorts.CliSrv+port_offset, 
            is_server=False)
        # create subscription where we will receive server management events
        self._zmq_srvmgmt_sub = ZmqStream(for_write=False, port_offset=port_offset,
            stream_name='zmq_sub:'+str(port_offset), topic=PublisherTopics.ServerMgmt)
        self._zmq_srvmgmt_sub.add_callback(self._on_srv_mgmt)        

    def _on_srv_mgmt(self, mgmt_msg:Any):
        r"""Handles server management events.
        """
        utils.debug_log("Received - SeverMgmtevent", mgmt_msg)
        # if server was restarted then send create stream requests again
        if mgmt_msg.event_name == ServerMgmtMsg.EventServerStart:
            for stream_req in self._stream_reqs.values():
                self._send_get_stream(stream_req)

    def close(self):
        if not self.closed:
            self._clisrv.close()
            self._zmq_streamitem_sub.close()
            self._clisrv = self._zmq_streamitem_sub = None
            utils.debug_log("ZmqWatcherClient is closed", verbosity=1)
        super(ZmqWatcherServer, self).close()

    def create_stream_remote(self, stream_req:StreamRequest) -> None:
        utils.debug_log("sending create streamreq...")
        clisrv_req = ClientServerRequest(CliSrvReqTypes.create_stream, stream_req)
        self._clisrv.send_obj(clisrv_req)
        utils.debug_log("sent create streamreq")

        # save this for later for resend if server restarts
        self._stream_reqs[stream_name] = stream_req

    def del_stream_remote(self, stream_name:str) -> None:
        clisrv_req = ClientServerRequest(CliSrvReqTypes.del_stream, stream_name)
        self._clisrv.send_obj(clisrv_req)
        self._stream_reqs.pop(stream_name, None)
