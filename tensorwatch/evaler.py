import dill
import math
import queue
import threading
import sys
from collections.abc import Iterable, Iterator
from .lv_types import EventVars

from functools import *
from itertools import *
from statistics import *
import numpy as np
from .evaler_utils import *

class Evaler:
    class EvalReturn:
        def __init__(self, result=None, is_valid=False, exception=None):
            self.result, self.exception, self.is_valid = \
                result, exception, is_valid
        def reset(self):
            self.result, self.exception, self.is_valid = \
                None, None, False

    class PostableIterator:
        def __init__(self, eval_wait):
            self.eval_wait = eval_wait
            self.post_wait = threading.Event()
            self.reset()

        def reset(self):
            self.ended = False
            self.event_vars, self.ended = None, False
            self.post_wait.clear()

        def abort(self):
            self.ended = True
            self.post_wait.set()

        def post(self, event_vars:EventVars=None, ended=False):
            self.event_vars, self.ended = event_vars, ended
            self.post_wait.set()

        def get_vals(self):
            while True:
                self.post_wait.wait()
                self.post_wait.clear()
                if self.ended:
                    break
                else:
                    yield self.event_vars
                    # below will cause result=None, is_valid=False when
                    # expression has reduce
                    self.eval_wait.set()

    def __init__(self, expr):
        self.eval_wait = threading.Event()
        self.reset_wait = threading.Event()
        self.g = Evaler.PostableIterator(self.eval_wait)
        self.expr = expr
        self.reset()

        self.th = threading.Thread(target=self._runner, daemon=True, name='evaler')
        self.th.start()
        self.running = True

    def reset(self):
        self.g.reset()
        self.eval_wait.clear()
        self.reset_wait.clear()
        self.eval_return = Evaler.EvalReturn()
        self.continue_thread = True
        
    def _runner(self):
        while True:
            l = self.g.get_vals() # this var will be used by eval
            try:
                result = eval(self.expr)
                if isinstance(result, Iterator):
                    for i, result in enumerate(result):
                        self.eval_return = Evaler.EvalReturn(result, True)
                else:
                    self.eval_return = Evaler.EvalReturn(result, True)
            except Exception as e:
                print(e, file=sys.stderr)
                self.eval_return = Evaler.EvalReturn(None, True, e)
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

    def post(self, event_vars:EventVars=None, ended=False, continue_thread=True):
        if not self.running:
            utils.debug_log('post was called when Evaler is not running')
            return None, False
        self.eval_return.reset()
        self.g.post(event_vars, ended)
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
