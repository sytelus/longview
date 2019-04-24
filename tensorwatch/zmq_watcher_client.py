from typing import Any, Dict, Union, List, Tuple, Iterable
from .zmq_pub_sub import ZmqPubSub
from .lv_types import StreamItem, StreamRequest, CliSrvReqTypes, ClientServerRequest, DefaultPorts, PublisherTopics, ServerMgmtMsg
from .publisher import Publisher
from .zmq_subscriber import ZmqSubscriber
from .filtered_stream import FilteredStream
from . import utils

class ZmqWatcherClient:
    def __init__(self, port_offset:int=0):
        self.closed = True
        self.port_offset = port_offset
        self._filtered_streams:Dict[str,Publisher] = {}
        self._streams:Tuple[Dict[str,Union[StreamRequest, str]], List[str]] = {}
        self._open(port_offset)

    def _open(self, port_offset:int):
        if self.closed:
            self._clisrv = ZmqPubSub.ClientServer(port=DefaultPorts.CliSrv+port_offset, 
                is_server=False)
            self._zmq_streamitem_sub = ZmqSubscriber(port_offset=port_offset, name='zmq_sub:'+str(port_offset), 
                                                     topic=PublisherTopics.StreamItem)
            self._zmq_srvmgmt_sub = ZmqSubscriber(port_offset=port_offset, name='zmq_sub:'+str(port_offset),
                                                     topic=PublisherTopics.ServerMgmt)
            self._zmq_srvmgmt_sub.add_callback(self._on_srv_mgmt)        
            
            self.closed = False
        else:
            raise RuntimeError("ZmqWatcherClient is already open and must be closed before open() call")

    def _on_srv_mgmt(self, mgmt_msg:Any):
        utils.debug_log("Received - SeverMgmtevent", mgmt_msg)
        if mgmt_msg.event_name == ServerMgmtMsg.EventServerStart:
            for stream_req, subscribers in self._streams.values():
                self._send_create_stream(stream_req, subscribers)

    def close(self):
        if not self.closed:
            self._clisrv.close()
            self._zmq_streamitem_sub.close()
            self.closed = True
            for stream in self._filtered_streams.values():
                stream.close()
            self._filtered_streams.clear()
            utils.debug_log("ZmqWatcherClient is closed", verbosity=1)

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    @staticmethod
    def _filter_stream(stream_name):
        def filter_Wrapped(val):
            if val.stream_name==stream_name:
                return (val, True)
            else:
               return (None, False)
        return filter_Wrapped

    def create_stream(self, stream_req:Union[StreamRequest, str], subscribers:Iterable[Publisher]=None,
                      srv_subscribers:List[str]=['zmq']) -> Publisher:
        stream_name = stream_req if isinstance(stream_req, str) else stream_req.stream_name
        publisher:FilteredStream = None

        # if server side subscribers include zmq then we would listen to client side as well
        srv_subscribers = list(srv_subscribers)
        for i in range(len(srv_subscribers)):
            if srv_subscribers[i] == 'zmq':
                srv_subscribers[i] = srv_subscribers[i] + ':' + str(self.port_offset)
                publisher = self._filtered_streams[stream_name] = FilteredStream(self._zmq_streamitem_sub, 
                    ZmqWatcherClient._filter_stream(stream_name), 
                    self._zmq_streamitem_sub.name+':'+stream_name)

        if subscribers is not None and len(subscribers):
            if publisher is not None:
                for subscriber in subscribers:
                    subscriber.add_subscription(publisher)
            else:
                raise ValueError('srv_subscribers must contain zmq if client side subscribers are needed')

        self._send_create_stream(stream_req, srv_subscribers)
        self._streams[stream_name] = (stream_req, srv_subscribers)
        return publisher

    def _send_create_stream(self, stream_req:Union[StreamRequest, str], subscribers:List[str]):
        utils.debug_log("sending create streamreq...")
        clisrv_req = ClientServerRequest(CliSrvReqTypes.create_stream, (stream_req, subscribers))
        self._clisrv.send_obj(clisrv_req)
        utils.debug_log("sent create streamreq")


    def del_stream(self, stream_name:str) -> None:
        clisrv_req = ClientServerRequest(CliSrvReqTypes.del_stream, stream_name)
        self._clisrv.send_obj(clisrv_req)
        self._streams.pop(stream_name, None)
