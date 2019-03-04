from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *
from . import utils
import threading
import pandas as pd
import time
import ipywidgets as widgets
from IPython import get_ipython, display

class TextPrinter():
    def __init__(self):
        self.is_ipython = get_ipython() is not None
        self._stream_plots = {}
        self.is_shown = False
        self.widget = widgets.HBox(layout=widgets.Layout(overflow='visible'))
        self.df = pd.DataFrame([])
        self.lock = threading.Lock()

    def _add_eval_result(self, stream_event:StreamEvent):
        with self.lock:
            stream_plot = self._stream_plots.get(stream_event.stream_name, None)
            if stream_plot is None:
                utils.debug_log("Unrecognized stream received: {}".format(stream_event.stream_name))
                return

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

                    if eval_result.ended:
                        self.df = self.df.append(pd.Series(), ignore_index=True)
                    else:
                        vals = TextPrinter._extract_vals(eval_result)
                        if vals is not None:
                            for val in vals:
                                if val is not None:
                                    self.df = self.df.append([val.__dict__])

                    # update for throttle
                    stream_plot.last_update = time.time()

                    if self.is_ipython:
                        stream_plot.out_widget.clear_output(wait=True)
                        with stream_plot.out_widget:
                            display.display(self.df)
                    else:
                        last_recs = self.df.iloc[[-1]].to_dict('records')
                        if len(last_recs) == 1:
                            print(last_recs[0])
                        else:
                            print(last_recs)

                else:
                    utils.debug_log("Value not plotted due to throttle", 
                                    eval_result.event_name, verbosity=5)

            else:
                utils.debug_log("Unsupported event type received")

    def _get_title(self, stream_plot):
        title = stream_plot.title or 'Stream ' + str(len(self._stream_plots))
        return title

    def add(self, stream, title=None, throttle=None, clear_after_end=True, clear_after_each=False, 
            show:bool=None, **stream_args):

        with self.lock:
            stream_plot = StreamPlot(stream, throttle, title, clear_after_end, 
                        clear_after_each, history_len=1, dim_history=True, opacity=1)
            stream_plot._clear_pending = False
            stream_plot.out_widget = widgets.Output()
            self.widget.children = self.widget.children + (stream_plot.out_widget,)
            stream_plot.text = self._get_title(stream_plot)
            self._stream_plots[stream.stream_name] = stream_plot
            stream.subscribe(self._add_eval_result)
            if show or (show is None and not self.is_shown):
                return self.show()

            return None
                
    def show(self):
        self.is_shown = True
        return self.widget if self.is_ipython else ''

    def clear_plot(self, stream_plot):
        self.df = self.df.iloc[0:0]

    @staticmethod
    def _extract_vals(eval_result):
        if eval_result.ended or eval_result.result is None:
            vals = None
        else:
            vals = eval_result.result
            if not utils.is_array_like(eval_result.result, tuple_is_array=False):
                vals = [vals]
        return vals
