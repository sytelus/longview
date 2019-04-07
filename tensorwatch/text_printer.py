from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *
from . import utils
import threading
import pandas as pd
import time
import ipywidgets as widgets
from IPython import get_ipython, display

class TextPrinter:
    def __init__(self, cell=None, title=None, **plot_args):
        self.lock = threading.Lock()
        self.cell = cell or widgets.HBox(layout=widgets.Layout(height='3in'))
        self.widget = widgets.HTML()
        self.cell.children += (self.widget,)
        self._stream_plots = {}
        self.is_shown = cell is not None
        self.title = title

        self.is_ipython = get_ipython() is not None
        self.df = pd.DataFrame([])

    @staticmethod
    def _get_key_name(stream_event, i):
        return '[S.{}]:{}'.format(stream_event.display_name(), i)

    def append(self, stream_event, stream_plot, vals):
        if vals is None:
            self.df = self.df.append(pd.Series({stream_plot._get_key_name(stream_event, 0) : None}), 
                                                   sort=False, ignore_index=True)
            return
        for val in vals:
            if val is None or utils.is_scalar(val):
                self.df = self.df.append(pd.Series({TextPrinter._get_key_name(stream_event, 0) : val}), 
                                          sort=False, ignore_index=True)
            elif utils.is_array_like(val):
                val_dict = {}
                for i,val_i in enumerate(val):
                    val_dict[TextPrinter._get_key_name(stream_event, i)] = val_i
                self.df = self.df.append(pd.Series(val_dict), sort=False, ignore_index=True)
            else:
                self.df = self.df.append(pd.Series(val.__dict__), sort=False, ignore_index=True)

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
                        self.df = self.df.append(pd.Series({'Ended':True}), 
                                                               sort=False, ignore_index=True)
                    else:
                        vals = TextPrinter._extract_vals(eval_result)
                        self.append(stream_event, stream_plot, vals)

                    # update for throttle
                    stream_plot.last_update = time.time()

                    if self.is_ipython:
                        if not stream_plot.only_summary:
                            self.widget.value = self.df.to_html(classes=['output_html', 'rendered_html'])
                        else:
                            self.widget.value = self.df.describe().to_html(classes=['output_html', 'rendered_html'])
                        # below doesn't work because of threading issue
                        #self.widget.clear_output(wait=True)
                        #with self.widget:
                        #    display.display(self.df)
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
            show:bool=None, only_summary=False, **stream_args):

        with self.lock:
            stream_plot = StreamPlot(stream, throttle, title, clear_after_end, 
                        clear_after_each, history_len=1, dim_history=True, opacity=1)
            stream_plot._clear_pending = False
            stream_plot.text = self._get_title(stream_plot)
            stream_plot.only_summary = only_summary
            self._stream_plots[stream.stream_name] = stream_plot
            stream.subscribe(self._add_eval_result)
            if show or (show is None and not self.is_shown):
                return self.show()

            return None
                
    def show(self):
        self.is_shown = True
        return self.cell if self.is_ipython else ''

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
