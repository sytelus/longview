from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *
import matplotlib.pyplot as plt
import matplotlib.lines
from matplotlib.animation import FuncAnimation
import time
from . import utils

class LinePlot():
    class PlotInfo:
        def __init__(self, stream, x_f, y_f, throttle):
            self.xdata, self.ydata = [], []
            self.line = self.ax = None
            self.stream = stream
            self.x_f, self.y_f = x_f or self.get_x, y_f or self.get_y
            self.throttle = throttle
            self.last_update = time.time()

        def get_x(self, eval_result):
            if utils.is_list_like(eval_result.result) and len(eval_result.result) > 1:
                return eval_result.result[0]
            else:
                return eval_result.x or eval_result.event_index

        def get_y(self, eval_result):
            if utils.is_list_like(eval_result.result) and len(eval_result.result) > 1:
                return eval_result.result[1]
            else:
                return eval_result.result


    def __init__(self, title=None):
        self._init_done = False
        self._is_shown = False
        self.title = title
        self._plot_infos = {}

    def _show_init(self):
        if self._init_done:
            return
        self.figure = plt.figure()
        self.ax_main = self.figure.add_subplot(111)
        self.ax_main.grid(True)
        # change the color of the top and right spines to opaque gray
        self.ax_main.spines['right'].set_color((.8,.8,.8))
        self.ax_main.spines['top'].set_color((.8,.8,.8))
        if self.title is not None:
            title = self.ax_main.set_title(self.title)
            title.set_weight('bold')
        self.animation = FuncAnimation(self.figure, self._on_update, interval=1000) #ms
        self._init_done = True

    def _add_eval_result(self, eval_result:EvalResult):
        plot_info = self._plot_infos.get(eval_result.stream_name, None)
        if plot_info is not None and not eval_result.ended and eval_result.result is not None:
            if plot_info.throttle is None or \
                    time.time() - plot_info.last_update >= plot_info.throttle:
                plot_info.xdata.append(plot_info.x_f(eval_result))
                plot_info.ydata.append(plot_info.y_f(eval_result))
                plot_info.last_update = time.time()

    def _on_update(self, frame):
        for plot_info in self._plot_infos.values():
            plot_info.line.set_data(plot_info.xdata, plot_info.ydata)
            plot_info.ax.relim()
            plot_info.ax.autoscale_view()

    def show(self, stream, xlabel='', ylabel='', label=None, final_show=True, 
             color=None, x_f=None, y_f=None, xlim=None, ylim=None, throttle=None):
        self._show_init()
        if stream is not None:
            plot_info = LinePlot.PlotInfo(stream, x_f, y_f)
            if len(self._plot_infos) == 0:
                plot_info.ax = self.ax_main
            else:
                plot_info.ax = self.ax_main.twinx()
            color = color or plt.cm.viridis(1.0/(1+len(self._plot_infos)))
            label = label or ylabel
            plot_info.line = matplotlib.lines.Line2D(plot_info.xdata, plot_info.ydata, 
                label=label, color=color) #, linewidth=3
            plot_info.ax.add_line(plot_info.line)

            if len(self._plot_infos) > 2:
                pos = (len(self._plot_infos)-2) * 60
                plot_info.ax.spines['right'].set_position(('outward', pos))

            self._plot_infos[stream.stream_name] = plot_info
            plot_info.ax.set_xlabel(xlabel)
            plot_info.ax.set_ylabel(ylabel)
            plot_info.ax.yaxis.label.set_color(color)
            plot_info.ax.yaxis.label.set_style('italic')
            plot_info.ax.xaxis.label.set_style('italic')
            if xlim is not None:
                plot_info.ax.set_xlim(*xlim)
            if ylim is not None:
                plot_info.ax.set_ylim(*ylim)
            #plot_info.ax.yaxis.label.set_size(10)
            self.figure.legend(loc=1)
            stream.subscribe(self._add_eval_result)
        if final_show and not self._is_shown:
            self._is_shown = True
            return plt.show() #must be done only once

class TextPrinter():
    def __init__(self, prefix=None):
        self.prefix = prefix
    def _add_eval_result(self, eval_result:EvalResult):
        print(self.prefix, eval_result.event_index, eval_result.ended, eval_result.result)
    def show(self, *streams):
        for stream in streams:
            stream.subscribe(self._add_eval_result)

   
