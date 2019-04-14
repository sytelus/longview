import weakref
from typing import Any

class Publisher:
    def __init__(self, print_prefix:str=None):
        self._callbacks = []
        self.closed = False
        self.print_prefix = print_prefix

    def write(self, val:Any):
        if self.closed:
            return
        if self.print_prefix is not None:
            print(self.print_prefix, val)
        self._make_callbacks(val)

    def _make_callbacks(self, val:Any):
        for callback in self._callbacks:
            if callback and callback():
                callback()(val)

    def subscribe(self, callback):
        self._callbacks.append(weakref.WeakMethod(callback))

    def unsubscribe(self, callback):
        for i in reversed(range(len(self._callbacks))):
            if self._callbacks[i] and self._callbacks[i]() == callback:
                del self._callbacks[i]

    def close(self):
        if not self.closed:
            self._callbacks = []
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

