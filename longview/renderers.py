from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *
import matplotlib.pyplot as plt
import matplotlib.lines
from matplotlib.animation import FuncAnimation
import time
import threading
from . import utils

class LinePlot():
    class PlotInfo:
        def __init__(self, stream, throttle, clear_on_end, redraw_keep):
            self.xdata, self.ydata = [], []
            self.line = self.ax = None
            self.stream = stream
            self.throttle = throttle
            self.clear_on_end = clear_on_end
            self.redraw_keep = redraw_keep
            self.last_update = None
            self.xylabel_texts = {}
            self.xylabel_refs = {}

    def __init__(self, title=None):
        self._init_done = False
        self._is_shown = False
        self.title = title
        self._plot_infos = {}
        self.lock = threading.Lock()

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
        plt.set_cmap('hsv')
        plt.rcParams['image.cmap']='hsv'

    def _add_eval_result(self, eval_result:EvalResult):
        with self.lock:
            self._add_eval_result_unsafe(eval_result)

    def _add_eval_result_unsafe(self, eval_result:EvalResult):
        plot_info = self._plot_infos.get(eval_result.stream_name, None)
        if plot_info is not None:
            if not eval_result.ended:
                if eval_result.result is None:
                    return
                if plot_info.throttle is None or plot_info.last_update is None or \
                        time.time() - plot_info.last_update >= plot_info.throttle:
                    if utils.is_array_like(eval_result.result, allow_tuple=False):
                        vals = eval_result.result
                    else:
                        vals = [eval_result.result]
                    if plot_info.redraw_keep > 0:
                        plot_info.xdata.clear()
                        plot_info.ydata.clear()

                        if plot_info.redraw_keep > 1 and plot_info.line is not None:
                            lines = plot_info.ax.get_lines()
                            for i in range(len(lines)-1, -1, -1):
                                if i >= plot_info.redraw_keep:
                                    lines[i].remove()
                                    lines.pop(0)
                                else:
                                    lines[i].set_alpha(0.5/(len(lines)-i))

                            line = matplotlib.lines.Line2D(plot_info.xdata, plot_info.ydata, 
                                color=plot_info.line.get_color()) #, linewidth=3
                            plot_info.line = line
                            plot_info.ax.add_line(plot_info.line)
                    for val in vals:
                        x = eval_result.x or eval_result.event_index
                        y = val
                        pt_label = None

                        # if val turns out to be array like, extract x,y
                        val_l = utils.is_scaler_array(val)
                        if val_l >= 2:
                            x, y = val[0], val[1]
                        if val_l > 2:
                            pt_label = str(val[2])

                        xi = len(plot_info.xdata)
                        if pt_label is not None:
                            plot_info.xylabel_texts[xi] = pt_label
                        elif xi in plot_info.xylabel_texts:
                            del plot_info.xylabel_texts[xi]
                        plot_info.xdata.append(x)
                        plot_info.ydata.append(y)
                    plot_info.last_update = time.time()
            else:
                if plot_info.clear_on_end:
                    plot_info.xdata.clear()
                    plot_info.ydata.clear()
                    plot_info.xylabel_texts.clear()

    def _on_update(self, frame):
        with self.lock:
            self._on_update_unsafe(frame)

    def _on_update_unsafe(self, frame):
        for plot_info in self._plot_infos.values():
            plot_info.line.set_data(plot_info.xdata, plot_info.ydata)

            # sync xylabels
            for i, xylabel in plot_info.xylabel_texts.items():
                if i in plot_info.xylabel_refs:
                    plot_info.xylabel_refs[i].set_text(xylabel)
                    plot_info.xylabel_refs[i].set_position( \
                        (plot_info.xdata[i], plot_info.ydata[i]))
                else:
                    plot_info.xylabel_refs[i] = plot_info.ax.text( \
                        plot_info.xdata[i], plot_info.ydata[i], xylabel)
            for i in list(plot_info.xylabel_refs.keys()):
                if i not in plot_info.xylabel_texts:
                    label_info = plot_info.xylabel_refs[i]
                    label_info[i].set_visible(False)
                    label_info[i].remove()
                    del plot_info.xylabel_refs[i]

            plot_info.ax.relim()
            plot_info.ax.autoscale_view()

    def show(self, stream, xlabel='', ylabel='', label=None, final_show=True, 
             color=None, alpha=1, xlim=None, ylim=None, throttle=None, clear_on_end=False, redraw_keep=0):
        self._show_init()
        if stream is not None:
            plot_info = LinePlot.PlotInfo(stream, throttle, clear_on_end, redraw_keep)
            if len(self._plot_infos) == 0:
                plot_info.ax = self.ax_main
            else:
                plot_info.ax = self.ax_main.twinx()
            color = color or plt.cm.hsv(1.0/(1+len(self._plot_infos)))
            label = label or ylabel

            plot_info.line = matplotlib.lines.Line2D(plot_info.xdata, plot_info.ydata, 
                label=label, color=color) #, linewidth=3
            plot_info.line.set_alpha(alpha)
            plot_info.ax.add_line(plot_info.line)

            if len(self._plot_infos) > 2:
                pos = (len(self._plot_infos)-2) * 160
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
            self.figure.legend(loc='center right')
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

   
