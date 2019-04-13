from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *
from . import utils
import threading
import pandas as pd
import time
import ipywidgets as widgets
from IPython import get_ipython, display

from .vis_base import VisBase

class TextVis(VisBase):
    def __init__(self, cell=None, title:str=None, show_legend:bool=None, **plot_args):
        super(TextVis, self).__init__(widgets.HTML(), cell, title, show_legend, **plot_args)
        self.df = pd.DataFrame([])

    def _get_column_prefix(self, stream_plot, i):
        return '[S.{}]:{}'.format(stream_plot.index, i)

    def append(self, stream_plot, vals):
        if vals is None:
            self.df = self.df.append(pd.Series({self._get_column_prefix(stream_plot, 0) : None}), 
                                                   sort=False, ignore_index=True)
            return
        for val in vals:
            if val is None or utils.is_scalar(val):
                self.df = self.df.append(pd.Series({self._get_column_prefix(stream_plot, 0) : val}), 
                                          sort=False, ignore_index=True)
            elif utils.is_array_like(val):
                val_dict = {}
                for i,val_i in enumerate(val):
                    val_dict[self._get_column_prefix(stream_plot, i)] = val_i
                self.df = self.df.append(pd.Series(val_dict), sort=False, ignore_index=True)
            else:
                self.df = self.df.append(pd.Series(val.__dict__), sort=False, ignore_index=True)

    def _post_stream_event(self):
        self._update_stream_plots(None)

    def _show_stream_items(self, stream_plot, stream_items):
        for stream_item in stream_items:
            if stream_item.ended:
                self.df = self.df.append(pd.Series({'Ended':True}), 
                                                        sort=False, ignore_index=True)
            else:
                vals = self._extract_vals((stream_item,))
                self.append(stream_plot, vals)
        return True

    def _post_update_stream_plot(self, stream_plot):
        if get_ipython():
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

    def _get_title(self, stream_plot):
        title = stream_plot.title or 'Stream ' + str(len(self._stream_plots))
        return title

    def _post_add(self, stream_plot, **stream_plot_args):
        only_summary = stream_plot_args.get('only_summary', False)
        stream_plot.text = self._get_title(stream_plot)
        stream_plot.only_summary = only_summary

    def clear_plot(self, stream_plot, clear_history):
        self.df = self.df.iloc[0:0]


    def _show_widget_native(self, blocking:bool):
        return None # we will be using console

    def _show_widget_notebook(self):
        return self.widget