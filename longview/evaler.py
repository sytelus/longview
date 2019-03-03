import dill
import math
import queue
import threading
import sys
from functools import *
from collections.abc import Iterable, Iterator

from itertools import *
from statistics import *
import numpy as np
from .lv_types import *
from .evaler_utils import *

class Evaler:
    class PostableIterator:
        def __init__(self, eval_wait):
            self.eval_wait = eval_wait
            self.post_wait = threading.Event()
            self.reset()

        def reset(self):
            self.ended = False
            self.val, self.ended = None, False
            self.post_wait.clear()

        def abort(self):
            self.ended = True
            self.post_wait.set()

        def post(self, val=None, ended=False):
            self.val, self.ended = val, ended
            self.post_wait.set()

        def get_vals(self):
            while True:
                self.post_wait.wait()
                self.post_wait.clear()
                if self.ended:
                    break
                else:
                    yield self.val
                    self.eval_wait.set()

    def __init__(self, eval_expr):
        self.eval_wait = threading.Event()
        self.reset_wait = threading.Event()
        self.g = Evaler.PostableIterator(self.eval_wait)
        self.eval_expr = eval_expr
        self.reset()

        self.th = threading.Thread(target=self._runner, name='evaler')
        self.th.start()
        self.running = True

    def reset(self):
        self.g.reset()
        self.eval_wait.clear()
        self.reset_wait.clear()
        self.eval_return = EvalReturn()
        self.continue_thread = True
        
    def _runner(self):
        while True:
            l = self.g.get_vals() # this var will be used by eval
            try:
                eval_result = eval(self.eval_expr)
                if isinstance(eval_result, Iterator):
                    for i, result in enumerate(eval_result):
                        self.eval_return = EvalReturn(result, True)
                else:
                    self.eval_return = EvalReturn(eval_result, True)
            except Exception as e:
                print(e, file=sys.stderr)
                self.eval_return = EvalReturn(None, True, e)
            self.eval_wait.set()
            self.reset_wait.wait()
            if not self.continue_thread:
                break
            self.reset()
        self.running = False
        utils.debug_log('eval runner ended!')

    def abort(self):
        utils.debug_log('Evaler Aborted')
        self.continue_thread = False
        self.g.abort()
        self.eval_wait.set()
        self.reset_wait.set()

    def post(self, val=None, ended=False, continue_thread=True):
        if not self.running:
            utils.debug_log('post was called when Evaler is not running')
            return None, False
        self.eval_return.reset()
        self.g.post(val, ended)
        self.eval_wait.wait()
        self.eval_wait.clear()
        # save result before it would get reset
        eval_return = self.eval_return
        self.reset_wait.set()
        self.continue_thread = continue_thread
        if isinstance(eval_return.result, Iterator):
            eval_return.result = list(eval_return.result)
        return eval_return

    def join(self):
        self.th.join()
