import matplotlib
import os
#if os.name == 'posix' and "DISPLAY" not in os.environ:
#    matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!

from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from ..lv_types import *
from .. import utils

import matplotlib.pyplot as plt
import matplotlib.lines
from matplotlib.animation import FuncAnimation
import time
import threading
import queue
import ipywidgets as widgets
from IPython import get_ipython

class BasePlot:
    def __init__(self, cell=None, title=None, show_legend:bool=True):
        # we initialize figure when first axis is added
        self._fig_init_done = False
        # has this plot be shown yet?
        self.is_shown = False
        self.title = title
        self.show_legend = show_legend
        # number of streams for this plot
        self._stream_plots = {}
        # lock to protect code from callback from seperate thread and render thread
        self.lock = threading.Lock()
        # graph objects
        self.figure = None
        self._ax_main = None
        # matplotlib animation
        self.animation = None

    def init_fig(self, anim_interval:float=1.0):
        """(for derived class) Initializes matplotlib figure"""
        if self._fig_init_done:
            return False

        # create figure and animation
        self.figure = plt.figure(figsize=(8, 3))

        if anim_interval:
            self.animation = FuncAnimation(self.figure, self._on_update, interval=anim_interval)
        plt.set_cmap('Dark2')
        plt.rcParams['image.cmap']='Dark2'

        self._fig_init_done = True
        return True

    def get_main_axis(self):
        # if we don't yet have main axis, create one
        if not self._ax_main:
            # by default assign one subplot to whole graph
            self._ax_main = self.figure.add_subplot(111)
            self._ax_main.grid(True)
            # change the color of the top and right spines to opaque gray
            self._ax_main.spines['right'].set_color((.8,.8,.8))
            self._ax_main.spines['top'].set_color((.8,.8,.8))
            if self.title is not None:
                title = self._ax_main.set_title(self.title)
                title.set_weight('bold')
        return self._ax_main

    def _add_eval_result(self, stream_event:StreamEvent):
        """Callback whenever EvalResult becomes available"""
        with self.lock: # callbacks are from separate thread!
            stream_plot = self._stream_plots.get(stream_event.stream_name, None)
            if stream_plot is None:
                utils.debug_log("Unrecognized stream received: {}".format(stream_event.stream_name))
                return
            stream_plot.pending_events.put(stream_event)

    def _on_update(self, frame):
        """Called on every graph animation update"""
        with self.lock:
            for stream_plot in self._stream_plots.values():
                # if we have something to render
                while not stream_plot.pending_events.empty():
                    stream_event = stream_plot.pending_events.get()
                    if stream_event.event_type == StreamEvent.Type.reset:
                        utils.debug_log("Stream reset", stream_event.stream_name)
                        self.clear_plot(stream_plot)
                    elif stream_event.event_type == StreamEvent.Type.eval_result:
                        eval_result = stream_event.eval_result
                        if eval_result.exception is not None:
                            print(eval_result.exception, file=sys.stderr)
                            raise eval_result.exception

                        # state management for _clear_pending
                        if stream_plot._clear_pending:
                            self.clear_plot(stream_plot)
                            stream_plot._clear_pending = False
                        if stream_plot.clear_after_each or (eval_result.ended and stream_plot.clear_after_end):
                            stream_plot._clear_pending = True

                        # check throttle
                        if eval_result.ended or \
                            stream_plot.throttle is None or stream_plot.last_update is None or \
                            time.time() - stream_plot.last_update >= stream_plot.throttle:

                            vals = BasePlot._extract_vals(eval_result)
                            self._plot_eval_result(vals, stream_plot, eval_result)

                            # update for throttle
                            stream_plot.last_update = time.time()
                        else:
                            utils.debug_log("Value not plotted due to throttle", 
                                            eval_result.event_name, verbosity=5)

    def add(self, stream, title=None, throttle=None, 
            clear_after_end=False, clear_after_each=False, show:bool=None, 
            history_len=0, dim_history=True, opacity=None, **stream_args):

        # make sure figure is initialized
        self.init_fig()

        if stream:
            stream_plot = StreamPlot(stream, throttle, title, clear_after_end, 
                clear_after_each, history_len, dim_history, opacity)
            stream_plot._clear_pending = False
            stream_plot.pending_events = queue.Queue()
            self.init_stream_plot(stream, stream_plot, **stream_args) 
            self._stream_plots[stream.stream_name] = stream_plot

            stream.subscribe(self._add_eval_result)

            if show or (show is None and not self.is_shown):
                return self.show()

        return None

    def show(self):
        self.is_shown = True
        return plt.show() #must be done only once

    @staticmethod
    def _extract_vals(eval_result):
        if eval_result.ended or eval_result.result is None:
            vals = None
        else:
            vals = eval_result.result
            if not utils.is_array_like(eval_result.result, tuple_is_array=False):
                vals = [vals]
        return vals

    def init_stream_plot(self, stream, stream_plot, **stream_args):
        """(for derived class) Create new plot info for this stream"""
        pass

    def clear_plot(self, stream_plot):
        """(for derived class) Clears the data in specified plot before new data is redrawn"""
        pass

    def _plot_eval_result(self, vals, stream_plot, eval_result):
        """(for derived class) Plot the data in given axes"""
        pass