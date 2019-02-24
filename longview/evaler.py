import dill
import math
import queue
import threading
from functools import *
from collections.abc import Iterable, Iterator

from itertools import *
from statistics import *
import numpy as np
from .evaler_utils import *

class Evaler:
    class PostableIterator:
        def __init__(self, xwait):
            self.xwait = xwait
            self.ewait = threading.Event()
            self.reset()

        def reset(self):
            self.ended = False
            self.val, self.ended = None, False
            self.ewait.clear()

        def abort(self):
            self.ended = True
            self.ewait.set()

        def post(self, val=None, ended=False):
            self.val, self.ended = val, ended
            self.ewait.set()

        def get_vals(self):
            while True:
                self.ewait.wait()
                self.ewait.clear()
                if self.ended:
                    break
                else:
                    yield self.val
                    self.xwait.set()

    def __init__(self, eval_f_s):
        self.xwait = threading.Event()
        self.rwait = threading.Event()
        self.g = Evaler.PostableIterator(self.xwait)
        self.eval_f_s = eval_f_s
        self.reset()

        self.th = threading.Thread(target=self._runner, name='evaler')
        self.th.start()

    def reset(self):
        self.g.reset()
        self.xwait.clear()
        self.rwait.clear()
        self.result, self.has_result = None, False
        self.continue_thread = True
        
    def _runner(self):
        while True:
            l = self.g.get_vals() # this var will be used by eval
            eval_result = eval(self.eval_f_s)
            if isinstance(eval_result, Iterator):
                for i,self.result in enumerate(eval_result):
                    self.has_result = True
            else:
                self.result = eval_result
                self.has_result = True
            self.xwait.set()
            self.rwait.wait()
            if not self.continue_thread:
                break
            self.reset()
        utils.debug_log('eval runner ended!', i)

    def abort(self):
        utils.debug_log('Evaler Aborted')
        self.g.abort()
        self.continue_thread = False
        self.xwait.set()
        self.rwait.set()

    def post(self, val=None, ended=False, continue_thread=True):
        self.result, self.has_result = None, False
        self.g.post(val, ended)
        self.xwait.wait()
        self.xwait.clear()
        r, b = self.result, self.has_result
        self.rwait.set()
        self.continue_thread = continue_thread
        if isinstance(r, Iterator):
            r = list(r)
        return r, b

    def join(self):
        self.th.join()
