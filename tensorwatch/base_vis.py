import os, sys, time, threading, traceback, logging, queue
from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from abc import ABC, abstractmethod
from .lv_types import *
from . import utils
from IPython import get_ipython, display
import ipywidgets as widgets

class BaseVis(ABC):
    def __init__(self, widget, cell, title:str, show_legend:bool, **plot_args):
        self.lock = threading.Lock()
        self._use_hbox = True
        utils.set_default(plot_args, 'width', '100%')
        utils.set_default(plot_args, 'height', '4in')

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

    def add(self, stream, title=None, throttle=None, clear_after_end=False, clear_after_each=False, 
            show:bool=False, history_len=1, dim_history=True, opacity=None, **stream_plot_args):
        with self.lock:
            self.layout_dirty = True
        
            stream_plot = StreamPlot(stream, throttle, title, clear_after_end, 
                clear_after_each, history_len, dim_history, opacity,
                len(self._stream_plots), stream_plot_args, 0)
            stream_plot._clear_pending = False
            stream_plot._pending_events = queue.Queue()
            self._stream_plots[stream.stream_name] = stream_plot

            self._post_add(stream_plot, **stream_plot_args)

            stream.subscribe(self._on_stream_event)

            if show or (show is None and not self.is_shown):
                return self.show()

            return None

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

    def _on_stream_event(self, stream_event:StreamEvent):
        with self.lock: # this could be from separate thread!
            stream_plot = self._stream_plots.get(stream_event.stream_name, None)
            if stream_plot is None:
                utils.debug_log("Unrecognized stream received: {}".format(stream_event.stream_name))
                return
            utils.debug_log("Stream received: {}".format(stream_event.stream_name), verbosity=5)
            stream_plot._pending_events.put(stream_event)
        self._post_stream_event()

    def _extract_event_results(self, stream_plot):
        stream_items, clear_current, clear_history = [], False, False
        while not stream_plot._pending_events.empty():
            stream_event = stream_plot._pending_events.get()
            if stream_event.event_type == StreamEvent.Type.reset:
                utils.debug_log("Stream reset", stream_event.stream_name)
                stream_items.clear() # no need to process these events
                clear_current, clear_history = True, True
            elif stream_event.event_type == StreamEvent.Type.new_item:
                stream_item = stream_event.stream_item
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
                        
                # check throttle
                #TODO: throttle should be against server timestamp, not time.time()
                if stream_item.ended or \
                    stream_plot.throttle is None or \
                    time.time() - stream_plot.last_update >= stream_plot.throttle:

                    stream_items.append(stream_item)
                else:
                    utils.debug_log("Value not plotted due to throttle", 
                                    stream_item.event_name, verbosity=5)
            else:
                utils.debug_log("Unsupported event type received")

        return stream_items, clear_current, clear_history

    def _update_stream_plots(self, frame):
        with self.lock:
            self.q_last_processed = time.time()
            for stream_plot in self._stream_plots.values():
                stream_items, clear_current, clear_history = self._extract_event_results(stream_plot)

                if clear_current:
                    self.clear_plot(stream_plot, clear_history)

                # if we have something to render
                dirty = self._show_stream_items(stream_plot, stream_items)
                if dirty:
                    self._post_update_stream_plot(stream_plot)
                    stream_plot.last_update = time.time()

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
    def _post_add(self, stream_plot, **stream_plot_args):
        pass
    @abstractmethod
    def _show_widget_native(self, blocking:bool):
        pass
    @abstractmethod
    def _show_widget_notebook(self):
        pass
    @abstractmethod
    def _post_stream_event(self):
        pass
    @abstractmethod
    def _post_update_stream_plot(self, stream_plot):
        pass