import plotly 
import plotly.graph_objs as go

from ..vis_base import VisBase

import os, sys, time, threading, traceback, logging, queue
from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from abc import ABC, abstractmethod
from ..lv_types import *
from .. import utils
from IPython import get_ipython, display
import ipywidgets as widgets


class BasePlotlyPlot(VisBase):
    def __init__(self, cell=None, title=None, show_legend:bool=None, stream_name:str=None, console_debug:bool=False, **plot_args):
        super(BasePlotlyPlot, self).__init__(go.FigureWidget(), cell, title, show_legend, 
                                             stream_name=stream_name, console_debug=console_debug, **plot_args)

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
            self.clear_plot(stream_plot, False)
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

    def _can_update_stream_plots(self):
        return time.time() - self.q_last_processed > 0.5 # make configurable

    def _post_add_subscription(self, stream_plot, **stream_plot_args):
        stream_plot.trace_history, stream_plot.cur_history_index = [], None
        self._add_trace_with_history(stream_plot)
        self._setup_layout(stream_plot)

        if not self.widget.layout.title:
            self.widget.layout.title = stream_plot.title
        # TODO: better way for below?
        if stream_plot.history_len > 1:
            self.widget.layout.showlegend = False
                
    def _show_widget_native(self, blocking:bool):
        pass
        #TODO: save image, spawn browser?

    def _show_widget_notebook(self):
        #plotly.offline.iplot(self.widget)
        return None

    def _post_update_stream_plot(self, stream_plot):
        # not needed for plotly as FigureWidget stays upto date
        pass

    @abstractmethod
    def _setup_layout(self):
        pass
    @abstractmethod
    def _create_trace(self, stream_plot):
        pass
