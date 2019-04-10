import uuid
import queue
import threading 
import weakref

from .lv_types import *

class StreamBase:
    def __init__(self, stream_name:str=None, throttle=None):
        self.stream_name = stream_name if stream_name is not None else str(uuid.uuid4())
        # when values arrive from different thread than the one doind enumeration we need buffer
        self._res_buf = None 
        self._callbacks = []
        self.closed = False

    def send_data(self, stream_item:StreamItem):
        if self.closed:
            return
        se = StreamEvent(StreamEvent.Type.new_item, self.stream_name, stream_item)
        self._make_callbacks(se)
        if self._res_buf is not None:
            self._res_buf[0].put(stream_item)
            self._res_buf[1].set()

    def _make_callbacks(self, stream_event:StreamEvent):
        for callback in self._callbacks:
            if callback and callback():
                callback()(stream_event)

    def subscribe(self, callback):
        self._callbacks.append(weakref.WeakMethod(callback))
    def unsubscribe(self, callback):
        for i in reversed(range(len(self._callbacks))):
            if self._callbacks[i] and self._callbacks[i]() == callback:
                del self._callbacks[i]

    def _end_iterator(self):
        # stop any iterators in progress
        self.closed = True
        if self._res_buf is not None:
            self._res_buf[1].set()

    def _close(self):
        if not self.closed:
            self._callbacks = []
            self._res_buf = None
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def __del__(self):
        self._close()

    def __iter__(self):
        self._res_buf = (queue.Queue(), threading.Event())
        return self

    def __next__(self):
        if self._res_buf is None:
            raise RuntimeError("iter() wasn't called before next()")

        stream_item, stop_iter = None, False
        if not self.closed:
            if self._res_buf[0].empty():
                self._res_buf[1].wait()
                self._res_buf[1].clear()
            stream_item = self._res_buf[0].get()
            stop_iter = stream_item.ended
        else:
            stop_iter = True

        if stop_iter:
            self._res_buf = None
            raise StopIteration()
        else:
            return stream_item

    def send_reset(self):
        se = StreamEvent(StreamEvent.Type.reset, self.stream_name, None)
        self._make_callbacks(se)
