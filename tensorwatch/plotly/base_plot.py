import plotly 
import plotly.graph_objs as go

import os, sys, time, threading, traceback, logging, queue
from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from abc import ABC, abstractmethod
from ..lv_types import *
from .. import utils
from IPython import get_ipython, display
import ipywidgets as widgets


class BasePlot(ABC):
    def __init__(self, cell=None, title=None, show_legend:bool=None, **plot_args):
        self.lock = threading.Lock()
        self._use_hbox = True
        utils.set_default(plot_args, 'width', '100%')
        utils.set_default(plot_args, 'height', '4in')

        self.widget = go.FigureWidget()

        self.cell = cell or widgets.HBox(layout=widgets.Layout(\
            width=plot_args['width'])) if self._use_hbox else None
		if self._use_hbox:
			self.cell.children += (self.widget,)
        self._stream_plots = {}
        self.is_shown = cell is not None
        self.title = title
        self.last_ex = None
        self.layout_dirty = False

        self.widget.layout.title = title
        self.widget.layout.showlegend = show_legend if show_legend is not None else True
      
    def _add_trace(self, stream_plot):
        stream_plot.trace_index = len(self.widget.data)
        trace = self._create_trace(stream_plot)
        if stream_plot.opacity is not None:
            trace.opacity = stream_plot.opacity
        self.widget.add_trace(trace)

    def _add_trace_with_history(self, stream_plot):
        # if history buffer isn't full
        if stream_plot.history_len > len(stream_plot.trace_history):
            self._add_trace(stream_plot)
            stream_plot.trace_history.append(len(self.widget.data)-1)
            stream_plot.cur_history_index = len(stream_plot.trace_history)-1
            #if stream_plot.cur_history_index:
            #    self.widget.data[trace_index].showlegend = False
        else:
            # rotate trace
            stream_plot.cur_history_index = (stream_plot.cur_history_index + 1) % stream_plot.history_len
            stream_plot.trace_index = stream_plot.trace_history[stream_plot.cur_history_index]
            self.clear_plot(stream_plot)
            self.widget.data[stream_plot.trace_index].opacity = stream_plot.opacity or 1

        cur_history_len = len(stream_plot.trace_history)
        if stream_plot.dim_history and cur_history_len > 1:
            max_opacity = stream_plot.opacity or 1
            min_alpha, max_alpha, dimmed_len = max_opacity*0.05, max_opacity*0.8, cur_history_len-1
            alphas = list(utils.frange(max_alpha, min_alpha, steps=dimmed_len))
            for i, thi in enumerate(range(stream_plot.cur_history_index+1, 
                                          stream_plot.cur_history_index+cur_history_len)):
                trace_index = stream_plot.trace_history[thi % cur_history_len]
                self.widget.data[trace_index].opacity = alphas[i]

    def add(self, stream, title=None, throttle=None, clear_after_end=True, clear_after_each=False, 
           show:bool=False, history_len=1, dim_history=True, opacity=None, **stream_args):
        with self.lock:
            self.layout_dirty = True

            stream_plot = StreamPlot(stream, throttle, title, clear_after_end, 
                clear_after_each, history_len, dim_history, opacity)
            stream_plot.index = len(self._stream_plots)
            #TODO: sync mpl and plotly code using common base
            stream_plot._clear_pending = False
            stream_plot.stream_args = stream_args
            stream_plot.pending_events = queue.Queue()
            stream_plot.q_last_processed = 0

            stream_plot.trace_history, stream_plot.cur_history_index = [], None
            self._stream_plots[stream.stream_name] = stream_plot
        
            self._add_trace_with_history(stream_plot)
            self._setup_layout(stream_plot)

            if not self.widget.layout.title:
                self.widget.layout.title = stream_plot.title
            # TODO: better way for below?
            if history_len > 1:
                self.widget.layout.showlegend = False

            stream.subscribe(self._add_eval_result)

            if show or (show is None and not self.is_shown):
                return self.show()

            return None
                
    def show(self):
        self.is_shown = True
        #plotly.offline.iplot(self.widget)
        return self.cell

    @staticmethod
    def get_pallet_color(i:int):
        return plotly.colors.DEFAULT_PLOTLY_COLORS[i % len(plotly.colors.DEFAULT_PLOTLY_COLORS)]

    @staticmethod
    def _get_axis_common_props(title:str, axis_range:tuple):
        props = {'showline':True, 'showgrid': True, 
                       'showticklabels': True, 'ticks':'inside'}
        if title:
            props['title'] = title
        if axis_range:
            props['range'] = list(axis_range)
        return props

    def _clear_history(self, stream_plot):
        for i in range(len(stream_plot.trace_history)):
            stream_plot.trace_index = i
            self.clear_plot(stream_plot)

    def _add_eval_result(self, stream_event:StreamEvent):
        """Callback whenever EvalResult becomes available"""
        with self.lock: # callbacks are from separate thread!
            stream_plot = self._stream_plots.get(stream_event.stream_name, None)
            if stream_plot is None:
                utils.debug_log("Unrecognized stream received: {}".format(stream_event.stream_name))
                return
            utils.debug_log("Stream received: {}".format(stream_event.stream_name), verbosity=5)
            stream_plot.pending_events.put(stream_event)
            if time.time() - stream_plot.q_last_processed > 0.5: # make configurable
                stream_plot.q_last_processed = time.time()
                self._on_update_internal(None)

    def _update_render(self, stream_plot):
        utils.debug_log("Plot updated", stream_plot.stream.stream_name, verbosity=5)

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

    def _process_event_results(self, stream_plot):
        eval_results, needs_clearing = [], False
        while not stream_plot.pending_events.empty():
            stream_event = stream_plot.pending_events.get()
            if stream_event.event_type == StreamEvent.Type.reset:
                utils.debug_log("Stream reset", stream_event.stream_name)
                eval_results.clear() # no need to process these events
                needs_clearing = True
            elif stream_event.event_type == StreamEvent.Type.eval_result:
                eval_result = stream_event.eval_result
                # check if there was an exception
                if eval_result.exception is not None:
                    #TODO: need better handling here?
                    print(eval_result.exception, file=sys.stderr)
                    raise eval_result.exception

                # state management for _clear_pending
                # if we need to clear plot before putting in data, do so
                if stream_plot._clear_pending:
                    eval_results.clear()
                    needs_clearing = True
                    stream_plot._clear_pending = False
                if stream_plot.clear_after_each or (eval_result.ended and stream_plot.clear_after_end):
                    stream_plot._clear_pending = True
                        
                # check throttle
                #TODO: throttle should be against server timestamp, not time.time()
                if eval_result.ended or \
                    stream_plot.throttle is None or stream_plot.last_update is None or \
                    time.time() - stream_plot.last_update >= stream_plot.throttle:

                    eval_results.append(eval_result)
                else:
                    utils.debug_log("Value not plotted due to throttle", 
                                    eval_result.event_name, verbosity=5)
            else:
                utils.debug_log("Unsupported event type received")

        return eval_results, needs_clearing

    def _on_update_internal(self, frame):
        """Called on every graph animation update"""
        with self.lock:
            for stream_plot in self._stream_plots.values():
                eval_results, needs_clearing = self._process_event_results(stream_plot)

                if needs_clearing:
                    self.clear_plot(stream_plot)

                # if we have something to render
                dirty = self._plot_eval_result(stream_plot, eval_results)
                if dirty:
                    self._update_render(stream_plot)
                    stream_plot.last_update = time.time()

    @staticmethod
    def _extract_vals(eval_results):
        vals = []
        for eval_result in eval_results:
            if eval_result.ended or eval_result.result is None:
                pass # no values to add
            else:
                if utils.is_array_like(eval_result.result, tuple_is_array=False):
                    vals.extend(eval_result.result)
                else:
                    vals.append(eval_result.result)
        return vals



    @abstractmethod
    def _setup_layout(self):
        pass
    @abstractmethod
    def _create_trace(self, stream_plot):
        pass
    @abstractmethod
    def _plot_eval_result(self, stream_plot, eval_results):
        pass      
    @abstractmethod
    def clear_plot(self, stream_plot):
        pass