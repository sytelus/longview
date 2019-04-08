#from IPython import get_ipython, display
#if get_ipython():
#    get_ipython().magic('matplotlib notebook')

import matplotlib
import os
import sys
import traceback
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
import logging
from IPython import get_ipython, display
import ipywidgets as widgets
from ipywidgets.widgets.interaction import show_inline_matplotlib_plots
from ipykernel.pylab.backend_inline import flush_figures

class BasePlot:
    def __init__(self, cell=None, title=None, show_legend:bool=None, **plot_args):
        self.lock = threading.Lock()
        self._use_hbox = True

        utils.set_default(plot_args, 'width', '100%')
        utils.set_default(plot_args, 'height', '4in')

        self.cell = cell or widgets.HBox(layout=widgets.Layout(\
            width=plot_args['width'])) if self._use_hbox else None
        self.widget = widgets.Output()
        if self._use_hbox:
            self.cell.children += (self.widget,)
        self._stream_plots = {}
        self.is_shown = cell is not None
        self.title = title

        self._fig_init_done = False
        self.show_legend = show_legend
        # graph objects
        self.figure = None
        self._ax_main = None
        # matplotlib animation
        self.animation = None
        self.last_ex = None
        self.layout_dirty = False
        #print(matplotlib.get_backend())
        #display.display(self.cell)

    # anim_interval in seconds
    def init_fig(self, anim_interval:float=1.0):
        """(for derived class) Initializes matplotlib figure"""
        if self._fig_init_done:
            return False

        # create figure and animation
        self.figure = plt.figure(figsize=(8, 3))
        self.anim_interval = anim_interval

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
            utils.debug_log("Stream received: {}".format(stream_event.stream_name), verbosity=5)
            stream_plot.pending_events.put(stream_event)

    def _on_update(self, frame):
        try:
            self._on_update_internal(frame)
        except Exception as ex:
            # when exception occurs here, animation will stop and there
            # will be no further plot updates
            # TODO: may be we don't need all of below but none of them
            #   are popping up exception in Jupyter Notebook because these
            #   exceptions occur in background?
            self.last_ex = ex
            print(ex)
            logging.fatal(ex, exc_info=True) 
            traceback.print_exc(file=sys.stdout)

    def _on_update_internal(self, frame):
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
                            dirty = self._plot_eval_result(vals, stream_plot, eval_result)

                            if dirty:
                                utils.debug_log("Plot updated", eval_result.stream_name, verbosity=5)

                                if self.layout_dirty:
                                    # do not do tight_layout() call on every update 
                                    # that would jumble up the graphs! it should only called
                                    # once each time there is change in layout
                                    self.figure.tight_layout()
                                    self.layout_dirty = False

                                # below forces redraw and it was helpful to
                                # repaint even if there was error in interval loop
                                # but it does work in native UX and not in Jupyter Notebook
                                #self.figure.canvas.draw()
                                #self.figure.canvas.flush_events()

                                if self._use_hbox and get_ipython():
                                    self.widget.clear_output(wait=True)
                                    with self.widget:
                                        plt.show(self.figure)

                                        # everything else that doesn't work
                                        #self.figure.show()
                                        #display.clear_output(wait=True)
                                        #display.display(self.figure)
                                        #flush_figures()
                                        #plt.show()
                                        #show_inline_matplotlib_plots()
                                #elif not get_ipython():
                                #    self.figure.canvas.draw()

                            # update for throttle
                            stream_plot.last_update = time.time()
                        else:
                            utils.debug_log("Value not plotted due to throttle", 
                                            eval_result.event_name, verbosity=5)

    def add(self, stream, title=None, throttle=None, clear_after_end=False, clear_after_each=False, 
            show:bool=False, history_len=1, dim_history=True, opacity=None, **stream_args):
        with self.lock:
            self.layout_dirty = True
            # make sure figure is initialized
            self.init_fig()
        
            stream_plot = StreamPlot(stream, throttle, title, clear_after_end, 
                clear_after_each, history_len, dim_history, opacity)
            stream_plot.index = len(self._stream_plots)
            stream_plot._clear_pending = False
            stream_plot.stream_args = stream_args

            stream_plot.pending_events = queue.Queue()
            self.init_stream_plot(stream, stream_plot, **stream_args) 
            self._stream_plots[stream.stream_name] = stream_plot

            # redo the legend
            #self.figure.legend(loc='center right', bbox_to_anchor=(1.5, 0.5))
            if self.show_legend:
                self.figure.legend(loc='lower right')
            plt.subplots_adjust(hspace=0.6)

            stream.subscribe(self._add_eval_result)

            if show or (show is None and not self.is_shown):
                return self.show()

            return None

    def show(self, blocking=False):
        self.is_shown = True

        if self.anim_interval:
            self.animation = FuncAnimation(self.figure, self._on_update, interval=self.anim_interval*1000.0)

        #plt.show() #must be done only once
        if get_ipython():
            if self._use_hbox:
                display.display(self.cell) # this method doesn't need returns
                #return self.cell
            else:
                # no need to return anything because %matplotlib notebook will 
                # detect spawning of figure and paint it
                # if self.figure is returned then you will see two of them
                return None
                #plt.show()
                #return self.figure
        else:
            #plt.ion()
            #plt.show()
            return plt.show(block=blocking)

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

    def has_legend(self):
        return self.show_legend or True