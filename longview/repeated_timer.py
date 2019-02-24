import threading
import time

class RepeatedTimer:
    def __init__(self, secs, callback):
        self.secs = secs
        self.callback = callback
        self._thread = None
        self._last_ret = None
        self._running = False

    def start(self):
        self._running = True
        if self._thread is None or not self._thread.isAlive():
            self._thread = threading.Thread(target=self._runner, name='RepeatedTimer', daemon=True)
            self._thread.start()

    def stop(self, block=False):
        self._running = False
        if block and not (self._thread is None or not self._thread.isAlive()):
            self._thread.join()

    def is_running(self):
        return self._running

    def get_last_ret(self):
        return self._last_ret

    def _runner(self):
        while (self._running):
            if self.callback is not None:
                self._last_ret = self.callback()
            time.sleep(self.secs)
        self._thread = None