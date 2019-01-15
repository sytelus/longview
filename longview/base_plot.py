from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *

import matplotlib.pyplot as plt
import matplotlib.lines
from matplotlib.animation import FuncAnimation
import time
import threading
import queue

from . import utils

class BasePlot:
    class StreamPlot:
        def __init__(self, stream, throttle, redraw_on_end, label, 
                redraw_after=float('inf'), keep_old=0, dim_old=True):
            self.stream = stream
            self.throttle = throttle
            self.redraw_on_end = redraw_on_end
            self.label = label
            self.last_update = None
            self.pending_evals = queue.Queue()
            self.redraw_after = redraw_after
            self.keep_old = keep_old
            self.dim_old = dim_old
            self.redraw_countdown = redraw_after
            
    def __init__(self, title=None):
        self._fig_init_done = False
        self._is_shown = False
        self.title = title
        self._stream_plots = {}
        self.lock = threading.Lock()
        # graph objects
        self.figure = None
        self._ax_main = None
        self.animation = None

    def init_fig(self, anim_interval:float=1.0):
        """(for derived class) Initializes matplotlib figure"""
        if self._fig_init_done:
            return False
        self.figure = plt.figure()

        if anim_interval:
            self.animation = FuncAnimation(self.figure, self._on_update, interval=anim_interval)
        plt.set_cmap('hsv')
        plt.rcParams['image.cmap']='hsv'
        self._fig_init_done = True
        return True

    def get_main_axis(self):
        if not self._ax_main:
            self._ax_main = self.figure.add_subplot(111)
            self._ax_main.grid(True)
            # change the color of the top and right spines to opaque gray
            self._ax_main.spines['right'].set_color((.8,.8,.8))
            self._ax_main.spines['top'].set_color((.8,.8,.8))
            if self.title is not None:
                title = self._ax_main.set_title(self.title)
                title.set_weight('bold')
        return self._ax_main

    def _add_eval_result(self, eval_result:EvalResult):
        """Callback whenever EvalResult becomes available"""
        with self.lock:
            stream_plot = self._stream_plots.get(eval_result.stream_name, None)
            if stream_plot is not None:
                # check throttle
                if stream_plot.throttle is None or stream_plot.last_update is None or \
                        time.time() - stream_plot.last_update >= stream_plot.throttle:

                    stream_plot.pending_evals.put(eval_result)

                    # update for throttle
                    stream_plot.last_update = time.time()
            else:
                print("Unrecognized stream received: {}".format(eval_result.stream_name))

    def _on_update(self, frame):
        """Called on every graph animation update"""
        with self.lock:
            for stream_plot in self._stream_plots.values():
                # if we have something to render
                while not stream_plot.pending_evals.empty():
                    eval_result = stream_plot.pending_evals.get()

                    if eval_result.ended:
                        if stream_plot.redraw_on_end:
                            stream_plot.redraw_countdown = 0
                    elif eval_result.result is not None:
                        # if we need to redraw this plot
                        if stream_plot.redraw_countdown <= 0:
                            # clear the plot
                            self.clear_stream_plot(stream_plot)
                            # reset count down
                            stream_plot.redraw_countdown = stream_plot.redraw_after
                        else:
                            stream_plot.redraw_countdown -= 1
                        vals = eval_result.result
                        if not utils.is_array_like(eval_result.result, allow_tuple=False):
                            vals = [vals]
                        self.render_stream_plot(stream_plot, vals, eval_result)
                    else:
                        pass # ignore None result

    def show(self, stream, label=None, final_show=True, 
             throttle=None, redraw_on_end=False, redraw_after=float('inf'), 
             keep_old=0, dim_old=True, **kwargs):
        # make sure figure is initialized
        self.init_fig()

        if stream:
            stream_plot = BasePlot.StreamPlot(stream, throttle, redraw_on_end, label, 
                redraw_after, keep_old, dim_old)
            self.init_stream_plot(stream, stream_plot, **kwargs) 
            self._stream_plots[stream.stream_name] = stream_plot
            stream.subscribe(self._add_eval_result)
        if final_show and not self._is_shown:
            self._is_shown = True
            return plt.show() #must be done only once


    def init_stream_plot(self, stream, stream_plot, **kwargs):
        """(for derived class) Create new plot info for this stream"""
        pass

    def clear_stream_plot(self, stream_plot):
        """(for derived class) Clears the data in specified plot before new data is redrawn"""
        pass

    def render_stream_plot(self, stream_plot, vals, eval_result):
        """(for derived class) Plot the data in given axes"""
        pass