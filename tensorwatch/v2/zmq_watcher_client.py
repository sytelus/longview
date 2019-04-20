from typing import Any, Dict, Union, List
from .zmq_pub_sub import ZmqPubSub
from .lv_types import StreamItem, StreamRequest, CliSrvReqTypes, ClientServerRequest
from .publisher import Publisher
from .zmq_subscriber import ZmqSubscriber
from .filtered_stream import FilteredStream
from . import utils

class ZmqWatcherClient:
    DefaultCliSrvPort = 41459
          
    def __init__(self, port_offset:int=None):
        self.closed = True
        self.port_offset = port_offset or 0
        self._filtered_streams:Dict[str,Publisher] = {}
        self._open()

    def _open(self, port_offset:int=None):
        port_offset = port_offset or 0
        if self.closed:
            self._clisrv = ZmqPubSub.ClientServer(port=ZmqWatcherClient.DefaultCliSrvPort+port_offset, 
                is_server=False)
            self._zmq_subscriber = ZmqSubscriber(port_offset=port_offset, name='zmq_sub:'+str(port_offset))
            self.closed = False
        else:
            raise RuntimeError("ZmqWatcherClient is already open and must be closed before open() call")

    def close(self):
        if not self.closed:
            self._clisrv.close()
            self._zmq_subscriber.close()
            self.closed = True
            for stream in self._filtered_streams.values():
                stream.close()
            self._filtered_streams.clear()
            utils.debug_log("ZmqWatcherClient is closed", verbosity=1)

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def create_stream(self, stream_req:Union[StreamRequest, str], subscribers:List[str]=['zmq']) -> Publisher:
        utils.debug_log("sending create streamreq...")
        stream_name = stream_req if isinstance(stream_req, str) else stream_req.stream_name
        publisher:FilteredStream = None
        for i in range(len(subscribers)):
            if subscribers[i] == 'zmq':
                subscribers[i] = subscribers[i] + ':' + str(self.port_offset)
                publisher = self._filtered_streams[stream_name] = FilteredStream(self._zmq_subscriber, stream_name, 
                                                                                 self._zmq_subscriber.name+':'+stream_name)
        clisrv_req = ClientServerRequest(CliSrvReqTypes.create_stream, (stream_req, subscribers))
        self._clisrv.send_obj(clisrv_req)
        utils.debug_log("sent create streamreq")
        return publisher

    def del_stream(self, event_name:str, stream_name:str) -> None:
        clisrv_req = ClientServerRequest(CliSrvReqTypes.del_stream, event_name)
        self._clisrv.send_obj(clisrv_req)
