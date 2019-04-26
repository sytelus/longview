import weakref, uuid
from typing import Any
from . import utils

class Stream:
    def __init__(self, name:str=None, console_debug:bool=False):
        self._callbacks = []
        self.closed = False
        self.console_debug = console_debug
        self.name = name or str(uuid.uuid4()) # useful to use as key and avoid circular references

    def write(self, val:Any):
        if self.closed:
            return
        if self.console_debug:
            print(self.name, val)
        self._make_callbacks(val)

    def _make_callbacks(self, val:Any):
        for callback in self._callbacks:
            if callback and callback():
                callback()(val)

    def add_callback(self, callback):
        self._callbacks.append(weakref.WeakMethod(callback))

    def remove_callback(self, callback):
        for i in reversed(range(len(self._callbacks))):
            if self._callbacks[i] and self._callbacks[i]() == callback:
                del self._callbacks[i]

    def subscribe(self, stream:'Stream'): # notify other stream
        utils.debug_log('{} added {} as subscription'.format(self.name, stream.name))
        stream.add_callback(self.write)

    def unsubscribe(self, stream:'Stream'):
        stream.remove_callback(self.write)

    def close(self):
        if not self.closed:
            self._callbacks = []
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

