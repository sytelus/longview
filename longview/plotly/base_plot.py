import plotly 
import plotly.graph_objs as go
import time
import sys
from abc import ABC, abstractmethod

from ..lv_types import *
from .. import utils

class BasePlot(ABC):
    def __init__(self, title=None, show_legend:bool=True):
        self.title = title
        self._stream_plots = {}
        
        self.figwig = go.FigureWidget()
        self.figwig.layout.title = title
        self.figwig.layout.showlegend = show_legend
        self.is_shown = False
      
    @abstractmethod
    def _setup_layout(self):
        pass
    @abstractmethod
    def _create_trace(self, stream_plot):
        pass
    @abstractmethod
    def _plot_eval_result(self, vals, stream_plot, eval_result):
        pass      
    @abstractmethod
    def clear_plot(self, stream_plot):
        pass

    def _add_trace(self, stream_plot):
        stream_plot.trace_index = len(self.figwig.data)
        trace = self._create_trace(stream_plot)
        self.figwig.add_trace(trace)

    def _add_trace_with_history(self, stream_plot):
        # if history buffer isn't full
        if stream_plot.history_len > len(stream_plot.trace_history):
            self._add_trace(stream_plot)
            stream_plot.trace_history.append(len(self.figwig.data)-1)
            stream_plot.cur_history_index = len(stream_plot.trace_history)-1
        else:
            # rotate trace
            stream_plot.cur_history_index = (stream_plot.cur_history_index + 1) % stream_plot.history_len
            stream_plot.trace_index = stream_plot.trace_history[stream_plot.cur_history_index]
            self.clear_plot(stream_plot)
            self.figwig.data[stream_plot.trace_index].opacity = 1

        cur_history_len = len(stream_plot.trace_history)
        if stream_plot.dim_history and cur_history_len > 1:
            min_alpha, max_alpha, dimmed_len = 0.05, 0.7, cur_history_len-1
            alphas = list(utils.frange(max_alpha, min_alpha, steps=dimmed_len))
            for i, thi in enumerate(range(stream_plot.cur_history_index+1, 
                                          stream_plot.cur_history_index+cur_history_len)):
                trace_index = stream_plot.trace_history[thi % cur_history_len]
                self.figwig.data[trace_index].opacity = alphas[i]

    def add(self, stream, show:bool=None, clear_after_end=True, clear_after_each=False, 
           history_len=0, dim_history=True, **stream_args):
        if stream:
            plot_title = self.title or (stream.stream_name \
                if not utils.is_uuid4(stream.stream_name) else stream_args['ytitle'])

            stream_plot = StreamPlot(stream, throttle=None, title=stream_args['ytitle'])
            stream_plot.clear_after_end, stream_plot.clear_after_each = clear_after_end, clear_after_each
            stream_plot.history_len, stream_plot.dim_history = history_len, dim_history
            stream_plot.trace_history, stream_plot.cur_history_index = [], None
            stream_plot._last_event_ended = False
            stream_plot.index = len(self._stream_plots)
            stream_plot.stream_args = stream_args
            self._stream_plots[stream.stream_name] = stream_plot
        
            self._add_trace_with_history(stream_plot)
            self._setup_layout(stream_plot)

            if not self.figwig.layout.title:
                self.figwig.layout.title = stream_plot.title

            stream.subscribe(self._add_eval_result)

            if show:
                return self.show()
            elif show is None and not self.is_shown:
                return self.show()

        return None
                
    def show(self):
        self.is_shown = True
        #plotly.offline.iplot(self.figwig)
        return self.figwig

    @staticmethod
    def get_pallet_color(i:int):
        return plotly.colors.DEFAULT_PLOTLY_COLORS[i % len(plotly.colors.DEFAULT_PLOTLY_COLORS)]

    @staticmethod
    def _extract_vals(stream_plot, eval_result):
        if eval_result.ended or eval_result.result is None:
            vals = None
        else:
            vals = eval_result.result
            if not utils.is_array_like(eval_result.result, tuple_is_array=False):
                vals = [vals]
        return vals

    @staticmethod
    def _get_axis_common_props(title:str):
        return {'title':title, 'showline':True, 'showgrid': True, 
                       'showticklabels': True, 'ticks':'inside'}

    def _clear_history(self, stream_plot):
        for i in len(stream_plot.trace_history):
            stream_plot.trace_index = i
            self.clear_plot(stream_plot)

    def _add_eval_result(self, stream_event:StreamEvent):
        stream_plot = self._stream_plots.get(stream_event.stream_name, None)
        if stream_plot is None:
            utils.debug_log("Unrecognized stream received: {}".format(eval_result.stream_name))
            return

        if stream_event.event_type == StreamEvent.Type.reset:
            utils.debug_log("Stream reset", stream_event.stream_name)
            self._clear_history(stream_plot)
        elif stream_event.event_type == StreamEvent.Type.eval_result:
            eval_result = stream_event.eval_result
            if eval_result.exception is not None:
                print(eval_result.exception, file=sys.stderr)
                raise eval_result.exception

            # state management for _last_event_ended
            if stream_plot._last_event_ended and stream_plot.clear_after_end:
                self._add_trace_with_history(stream_plot)
            stream_plot._last_event_ended = False
            if eval_result.ended:
                stream_plot._last_event_ended = True

            # check throttle
            if eval_result.ended or \
                stream_plot.throttle is None or stream_plot.last_update is None or \
                time.time() - stream_plot.last_update >= stream_plot.throttle:

                vals = BasePlot._extract_vals(stream_plot, eval_result)
                self._plot_eval_result(vals, stream_plot, eval_result)

                # update for throttle
                stream_plot.last_update = time.time()
            else:
                utils.debug_log("Value not plotted due to throttle", 
                                eval_result.event_name, verbosity=5)

        else:
            utils.debug_log("Unsupported event type received")
