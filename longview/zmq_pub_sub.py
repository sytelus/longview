import zmq
import dill
from zmq.eventloop import ioloop, zmqstream
import zmq.utils.monitor
import functools
import sys
import time
from threading import Thread, Event
from . import utils

class ZmqPubSub:

    _thread:Thread = None
    _ioloop:ioloop.IOLoop = None
    _start_event:Event = None

    @staticmethod
    def initialize():
        # create thread that will wait on IO Loop
        if ZmqPubSub._thread is None:
            ZmqPubSub._thread = Thread(target=ZmqPubSub._run_io_loop, daemon=True)
            ZmqPubSub._start_event = Event()
            ZmqPubSub._thread.start()
            # this is needed to make sure IO Loop has enough time to start
            ZmqPubSub._start_event.wait() 

    @staticmethod
    def close():
        # terminate the IO Loop
        if ZmqPubSub._thread is not None:
            ZmqPubSub._ioloop.add_callback(ZmqPubSub._ioloop.stop)
            ZmqPubSub._thread = None
            ZmqPubSub._ioloop = None

    @staticmethod
    def _run_io_loop():
        if 'asyncio' in sys.modules:
            # tornado may be using asyncio,
            # ensure an eventloop exists for this thread
            import asyncio
            asyncio.set_event_loop(asyncio.new_event_loop())

        ZmqPubSub._ioloop = ioloop.IOLoop()
        while ZmqPubSub._thread is not None:
            try:
                ZmqPubSub._start_event.set()
                ZmqPubSub._ioloop.start()
            except zmq.ZMQError as e:
                if e.errno == errno.EINTR:
                    print("Cannot start IOLoop! ZMQError: {}".format(e), file=sys.stderr)
                    continue
                else:
                    raise

    # Utility method to run given function on IOLoop
    # this is blocking method if has_rresult=True
    # This can be called from any thread.
    @staticmethod
    def _io_loop_call(has_result, f, *kargs, **kwargs):
        class Result:
            def __init__(self, val=None):
                self.val = val

        def wrapper(f, e, r, *kargs, **kwargs):
            r.val = f(*kargs, **kwargs)
            e.set()

        # We will add callback in IO Loop and then wait for that
        # call back to be completed
        # If result is expected then we wait other wise fire and forget
        if has_result:
            e = Event()
            r = Result()
            f_wrapped = functools.partial(wrapper, f, e, r, *kargs, **kwargs)
            ZmqPubSub._ioloop.add_callback(f_wrapped)
            utils.debug_log("Waiting for call on ioloop", verbosity=5)
            e.wait()
            return r.val
        else:
            f_wrapped = functools.partial(f, *kargs, **kwargs)
            ZmqPubSub._ioloop.add_callback(f_wrapped)

    class Publication:
        def __init__(self, port, host="*"):
            ZmqPubSub.initialize()
            # make sure the call blocks until connection is made
            ZmqPubSub._io_loop_call(True, self._start_srv, port, host)

        def _start_srv(self, port, host):
            context = zmq.Context()
            self._socket = context.socket(zmq.PUB)
            self._socket.bind("tcp://%s:%d" % (host, port))
            self._mon_socket = self._socket.get_monitor_socket(zmq.EVENT_CONNECTED | zmq.EVENT_DISCONNECTED)
            self._mon_stream = zmqstream.ZMQStream(self._mon_socket)
            self._mon_stream.on_recv(self._on_mon)

        def send_obj(self, obj, topic=""):
            ZmqPubSub._io_loop_call(False, self._socket.send_multipart, 
                [topic.encode(), dill.dumps(obj)])

        def _on_mon(self, msg):
            ev = zmq.utils.monitor.parse_monitor_message(msg)
            event = ev['event']
            endpoint = ev['endpoint']
            if event == zmq.EVENT_CONNECTED:
                utils.debug_log("Subscriber connect event", endpoint, verbosity=1)
            elif event == zmq.EVENT_DISCONNECTED:
                utils.debug_log("Subscriber disconnect event", endpoint, verbosity=1)


    class Subscription:
        # subscribe to topic, call callback when object is received on topic
        def __init__(self, port, topic="", callback=None, host="localhost"):
            ZmqPubSub.initialize()
            ZmqPubSub._io_loop_call(False, self._add_sub,
                port, topic=topic, callback=callback, host=host)

        def _add_sub(self, port, topic, callback, host):
            def callback_wrapper(callback, msg):
                [topic, obj_s] = msg
                callback(dill.loads(obj_s))

            # connect to publisher socket
            context = zmq.Context()
            self.topic = topic.encode()
            self._socket = context.socket(zmq.SUB)

            utils.debug_log("Subscriber connecting...", verbosity=1)
            self._socket.connect("tcp://%s:%d" % (host, port))
            utils.debug_log("Subscriber connected!", verbosity=1)

            # setup socket filtering
            if topic != "":
                self._socket.setsockopt(zmq.SUBSCRIBE, self.topic)

            # if callback is specified then create a stream and set it 
            # for on_recv event - this would require running ioloop
            if callback is not None:
                self._stream = zmqstream.ZMQStream(self._socket)
                wrapper = functools.partial(callback_wrapper, callback)
                self._stream.on_recv(wrapper)
            #else use receive_obj

        def _receive_obj(self):
            [topic, obj_s] = self._socket.recv_multipart()
            if topic != self.topic:
                raise ValueError("Expected topic: %s, Received topic: %s" % (topic, self.topic)) 
            return dill.loads(obj_s)

        def receive_obj(self):
            return ZmqPubSub._io_loop_call(True, self._receive_obj)

        def _get_socket_identity(self):
            id = self._socket.getsockopt(zmq.LAST_ENDPOINT)
            return id

        def get_socket_identity(self):
            return ZmqPubSub._io_loop_call(True, self._get_socket_identity)


    class ClientServer:
        def __init__(self, port, is_server, callback=None, host=None):
            ZmqPubSub.initialize()
            # make sure call blocks until connection is made
            # otherwise variables would not be available
            ZmqPubSub._io_loop_call(True, self._connect,
                port, is_server, callback, host)

        def _connect(self, port, is_server, callback, host):
            def callback_wrapper(callback, msg):
                utils.debug_log("Server received request...", verbosity=5)

                [obj_s] = msg
                try:
                    ret = callback(self, dill.loads(obj_s))
                    # we must send reply to complete the cycle
                    self._socket.send_multipart([dill.dumps((ret, None))])
                except Exception as e:
                    print("ClientServer call raised exception: ", e, file=sys.stderr)
                    # we must send reply to complete the cycle
                    self._socket.send_multipart([dill.dumps((None, e))])
                
                utils.debug_log("Server sent response", verbosity=5)
                
            context = zmq.Context()
            if is_server:
                host = host or "127.0.0.1"
                self._socket = context.socket(zmq.REP)
                self._socket.bind("tcp://%s:%d" % (host, port))
            else:
                host = host or "localhost"
                self._socket = context.socket(zmq.REQ)
                self._socket.setsockopt(zmq.REQ_CORRELATE, 1)
                self._socket.setsockopt(zmq.REQ_RELAXED, 1)

                utils.debug_log("Client connecting...", verbosity=1)
                self._socket.connect("tcp://%s:%d" % (host, port))
                utils.debug_log("Client connected!", verbosity=1)

            if callback is not None:
                self._stream = zmqstream.ZMQStream(self._socket)
                wrapper = functools.partial(callback_wrapper, callback)
                self._stream.on_recv(wrapper)
            #else use receive_obj

        def send_obj(self, obj):
            ZmqPubSub._io_loop_call(False, self._socket.send_multipart,
                [dill.dumps(obj)])

        def receive_obj(self):
            [obj_s] = ZmqPubSub._io_loop_call(True, self._socket.recv_multipart)
            return dill.loads(obj_s)

        def request(self, req_obj):
            utils.debug_log("Client sending request...", verbosity=5)
            self.send_obj(req_obj)
            r = self.receive_obj()
            utils.debug_log("Client received response", verbosity=5)
            return r
