from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *

import matplotlib.pyplot as plt
import matplotlib.lines
from matplotlib.animation import FuncAnimation
import time
import threading

from . import utils

class BasePlot:
    class StreamPlot:
        def __init__(self, stream, throttle, clear_on_end, redraw_keep, label):
            self.stream = stream
            self.throttle = throttle
            self.clear_on_end = clear_on_end
            self.label = label
            self.redraw_keep = redraw_keep
            self.last_update = None

    def __init__(self, title=None):
        self._fig_init_done = False
        self._is_shown = False
        self.title = title
        self.figure = None
        self._ax_main = None
        self._stream_plots = {}
        self.lock = threading.Lock()

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
                if not eval_result.ended:
                    if eval_result.result is None:
                        return
                    # check throttle
                    if stream_plot.throttle is None or stream_plot.last_update is None or \
                            time.time() - stream_plot.last_update >= stream_plot.throttle:
                        # if we got set of values as result then break it down
                        if utils.is_array_like(eval_result.result, allow_tuple=False):
                            vals = eval_result.result
                        else:
                            vals = [eval_result.result]

                        # do we need to redraw at each eval?
                        if not self.on_eval_result(stream_plot, vals, eval_result):
                            # for each value we received, call derived class method
                            for val in vals:
                                self.on_eval_each_result(stream_plot, val, eval_result)

                        # update for throttle
                        stream_plot.last_update = time.time()
                else: # event ended
                    if stream_plot.clear_on_end:
                        self.clear(stream_plot)
            else:
                print("Unrecognized stream received: {}".format(eval_result.stream_name))

    def _on_update(self, frame):
        """Called on every graph animation update"""
        with self.lock:
            for stream_plot in self._stream_plots.values():
                self.render_stream_plot(stream_plot)

    def show(self, stream, label=None, final_show=True, 
             throttle=None, clear_on_end=False, redraw_keep=0, **kwargs):
        # make sure figure is initialized
        self.init_fig()

        if stream:
            stream_plot = BasePlot.StreamPlot(stream, throttle, clear_on_end, redraw_keep, label)
            self.init_stream_plot(stream, stream_plot, **kwargs) 
            self._stream_plots[stream.stream_name] = stream_plot
            stream.subscribe(self._add_eval_result)
        if final_show and not self._is_shown:
            self._is_shown = True
            return plt.show() #must be done only once

    def clear(self, stream_plot):
        """(for derived class) Clears the data in plot, without removing axes"""
        pass

    def on_eval_result(self, stream_plot, vals, eval_result):
        """(for derived class) Callback for derived class whenever EvalResult becomes available"""
        pass

    def on_eval_each_result(self, stream_plot, val, eval_result):
        """(for derived class) Callback for derived class whenever EvalResult becomes available"""
        pass

    def render_stream_plot(self, stream_plot):
        """(for derived class) Plot the data in given axes"""
        pass

    def init_stream_plot(self, stream, stream_plot):
        """(for derived class) Create new plot info for this stream"""
        pass

