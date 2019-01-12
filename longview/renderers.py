from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *
from . import utils
from .base_plot import *


class ImagePlot(BasePlot):
    def __init__(self, title=None):
        self.figure = plt.figure()
        self._is_shown = False
        self.ax = []

    def show(self, stream, cols = 5, throttle=None, clear_on_end=False, redraw_keep=0):
        items = list(stream)
        for i, data in enumerate(items):
            ax = self.figure.add_subplot()
            self.ax.append()
        if not self._is_shown:
            self._is_shown = True
            return plt.show() #must be done only once

class LinePlot(BasePlot):
    def init_plot_info(self, stream, plot_info, **kwargs):
        xlabel = kwargs.get('xlabel', '')
        ylabel = kwargs.get('ylabel', '')
        color = kwargs.get('color', None)
        alpha = kwargs.get('alpha', 1)
        xlim = kwargs.get('xlim', None)
        ylim = kwargs.get('ylim', None)

        plot_info.xdata, plot_info.ydata = [], []
        plot_info.line = plot_info.ax = None
        plot_info.xylabel_texts = {}
        plot_info.xylabel_refs = {}

        if len(self._plot_infos) == 0:
            plot_info.ax = self.ax_main
        else:
            plot_info.ax = self.ax_main.twinx()
        color = color or plt.cm.hsv(1.0/(1+len(self._plot_infos)))
        plot_info.label = plot_info.label or ylabel

        plot_info.line = matplotlib.lines.Line2D(plot_info.xdata, plot_info.ydata, 
            label=plot_info.label, color=color) #, linewidth=3
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

        # redo the legend
        self.figure.legend(loc='center right', bbox_to_anchor=(1, 0.5))

    def on_eval_result(self, plot_info, vals, eval_result):
        if plot_info.redraw_keep > 0:
            self.clear(plot_info)       
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

    def on_eval_each_result(self, plot_info, val, eval_result):
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

    def render_plot_info(self, plot_info):
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

    def clear(self, plot_info):
        plot_info.xdata.clear()
        plot_info.ydata.clear()
        plot_info.xylabel_texts.clear()

class TextPrinter():
    def __init__(self, prefix=None):
        self.prefix = prefix
    def _add_eval_result(self, eval_result:EvalResult):
        print(self.prefix, eval_result.event_index, eval_result.ended, eval_result.result)
    def show(self, *streams):
        for stream in streams:
            stream.subscribe(self._add_eval_result)

   
