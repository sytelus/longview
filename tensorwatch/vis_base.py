import os, sys, time, threading, traceback, logging, queue, functools
from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from types import MethodType
from abc import ABCMeta, abstractmethod

from .lv_types import *
from . import utils
from .stream import Stream

from IPython import get_ipython, display
import ipywidgets as widgets

class VisBase(Stream, metaclass=ABCMeta):
    def __init__(self, widget, cell, title:str, show_legend:bool, stream_name:str=None, console_debug:bool=False, **plot_args):
        super(VisBase, self).__init__(stream_name=stream_name, console_debug=console_debug)

        self.lock = threading.Lock()
        self._use_hbox = True
        utils.set_default(plot_args, 'width', '100%')

        self.widget = widget

        self.cell = cell or widgets.HBox(layout=widgets.Layout(\
            width=plot_args['width'])) if self._use_hbox else None
        if self._use_hbox:
            self.cell.children += (self.widget,)
        self._stream_plots = {}
        self.is_shown = cell is not None
        self.title = title
        self.last_ex = None
        self.layout_dirty = False
        self.q_last_processed = 0

    def subscribe(self, stream, title=None, clear_after_end=False, clear_after_each=False, 
            show:bool=False, history_len=1, dim_history=True, opacity=None, **stream_plot_args):
        # in this ovedrride we don't call base class method
        with self.lock:
            self.layout_dirty = True
        
            stream_plot = StreamPlot(stream, title, clear_after_end, 
                clear_after_each, history_len, dim_history, opacity,
                len(self._stream_plots), stream_plot_args, 0)
            stream_plot._clear_pending = False
            stream_plot._pending_items = queue.Queue()
            self._stream_plots[stream.stream_name] = stream_plot

            self._post_add_subscription(stream_plot, **stream_plot_args)

            write_fn = functools.partial(VisBase.write_stream_plot, self)
            stream_plot.write_fn = MethodType(write_fn, stream_plot) # weakref doesn't allow unfound methods
            stream.add_callback(stream_plot.write_fn)

            if show or (show is None and not self.is_shown):
                return self.show()

    def show(self, blocking:bool=False):
        self.is_shown = True
        if get_ipython():
            if self._use_hbox:
                display.display(self.cell) # this method doesn't need returns
                #return self.cell
            else:
                return self._show_widget_notebook()
        else:
            return self._show_widget_native(blocking)

    def write(self, val:Any):
        # let the base class know about new item, this will notify any subscribers
        super(VisBase, self).write(val)

        # use first stream_plot as default
        stream_plot = next(iter(self._stream_plots.values()))

        VisBase.write_stream_plot(self, stream_plot, val)

    @staticmethod
    def write_stream_plot(vis, stream_plot:StreamPlot, stream_item:StreamItem):
        with vis.lock: # this could be from separate thread!
            #if stream_plot is None:
            #    utils.debug_log('stream_plot not specified in VisBase.write')
            #    stream_plot = next(iter(vis._stream_plots.values())) # use first as default
            utils.debug_log("Stream received: {}".format(stream_item.stream_name), verbosity=5)
            stream_plot._pending_items.put(stream_item)

        # if we accumulated enough of pending items then let's process them
        if vis._can_update_stream_plots():
            vis._update_stream_plots()

    def _extract_results(self, stream_plot):
        stream_items, clear_current, clear_history = [], False, False
        while not stream_plot._pending_items.empty():
            stream_item = stream_plot._pending_items.get()
            if stream_item.stream_reset:
                utils.debug_log("Stream reset", stream_item.stream_name)
                stream_items.clear() # no need to process these events
                clear_current, clear_history = True, True
            else:
                # check if there was an exception
                if stream_item.exception is not None:
                    #TODO: need better handling here?
                    print(stream_item.exception, file=sys.stderr)
                    raise stream_item.exception

                # state management for _clear_pending
                # if we need to clear plot before putting in data, do so
                if stream_plot._clear_pending:
                    stream_items.clear()
                    clear_current = True
                    stream_plot._clear_pending = False
                if stream_plot.clear_after_each or (stream_item.ended and stream_plot.clear_after_end):
                    stream_plot._clear_pending = True
                        
                stream_items.append(stream_item)

        return stream_items, clear_current, clear_history

    def _extract_vals(self, stream_items):
        vals = []
        for stream_item in stream_items:
            if stream_item.ended or stream_item.value is None:
                pass # no values to add
            else:
                if utils.is_array_like(stream_item.value, tuple_is_array=False):
                    vals.extend(stream_item.value)
                else:
                    vals.append(stream_item.value)
        return vals

    @abstractmethod
    def clear_plot(self, stream_plot, clear_history):
        """(for derived class) Clears the data in specified plot before new data is redrawn"""
        pass
    @abstractmethod
    def _show_stream_items(self, stream_plot, stream_items):
        """(for derived class) Plot the data in given axes"""
        pass
    @abstractmethod
    def _post_add_subscription(self, stream_plot, **stream_plot_args):
        pass

    # typically we want to batch up items for performance
    def _can_update_stream_plots(self):
        return True

    @abstractmethod
    def _post_update_stream_plot(self, stream_plot):
        pass

    def _update_stream_plots(self):
        with self.lock:
            self.q_last_processed = time.time()
            for stream_plot in self._stream_plots.values():
                stream_items, clear_current, clear_history = self._extract_results(stream_plot)

                if clear_current:
                    self.clear_plot(stream_plot, clear_history)

                # if we have something to render
                dirty = self._show_stream_items(stream_plot, stream_items)
                if dirty:
                    self._post_update_stream_plot(stream_plot)
                    stream_plot.last_update = time.time()

    @abstractmethod
    def _show_widget_native(self, blocking:bool):
        pass
    @abstractmethod
    def _show_widget_notebook(self):
        pass