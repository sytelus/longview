from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *
from . import utils
from .base_plot import *


class ImagePlot(BasePlot):
    def init_stream_plot(self, stream, stream_plot, 
            rows=2, columns=5):
        stream_plot.columns = columns
        #stream_plot.rows = rows
        stream_plot.axs = [] 


class LinePlot(BasePlot):
    def init_stream_plot(self, stream, stream_plot, 
            xlabel='', ylabel='', color=None, alpha=1, xlim=None, ylim=None):
        stream_plot.xdata, stream_plot.ydata = [], []
        stream_plot.line = stream_plot.ax = None
        stream_plot.xylabel_texts = {}
        stream_plot.xylabel_refs = {}

        if len(self._stream_plots) == 0:
            stream_plot.ax = self.get_main_axis()
        else:
            stream_plot.ax = self.get_main_axis().twinx()
        color = color or plt.cm.hsv(1.0/(1+len(self._stream_plots)))
        stream_plot.label = stream_plot.label or ylabel

        stream_plot.line = matplotlib.lines.Line2D(stream_plot.xdata, stream_plot.ydata, 
            label=stream_plot.label, color=color) #, linewidth=3
        stream_plot.line.set_alpha(alpha)
        stream_plot.ax.add_line(stream_plot.line)

        if len(self._stream_plots) > 2:
            pos = (len(self._stream_plots)-2) * 160
            stream_plot.ax.spines['right'].set_position(('outward', pos))

        self._stream_plots[stream.stream_name] = stream_plot
        stream_plot.ax.set_xlabel(xlabel)
        stream_plot.ax.set_ylabel(ylabel)
        stream_plot.ax.yaxis.label.set_color(color)
        stream_plot.ax.yaxis.label.set_style('italic')
        stream_plot.ax.xaxis.label.set_style('italic')
        if xlim is not None:
            stream_plot.ax.set_xlim(*xlim)
        if ylim is not None:
            stream_plot.ax.set_ylim(*ylim)

        # redo the legend
        self.figure.legend(loc='center right', bbox_to_anchor=(1, 0.5))

    def on_eval_result(self, stream_plot, vals, eval_result):
        if stream_plot.redraw_keep > 0:
            self.clear(stream_plot)       
        if stream_plot.redraw_keep > 1 and stream_plot.line is not None:
            lines = stream_plot.ax.get_lines()
            for i in range(len(lines)-1, -1, -1):
                if i >= stream_plot.redraw_keep:
                    lines[i].remove()
                    lines.pop(0)
                else:
                    lines[i].set_alpha(0.5/(len(lines)-i))

            line = matplotlib.lines.Line2D(stream_plot.xdata, stream_plot.ydata, 
                color=stream_plot.line.get_color()) #, linewidth=3
            stream_plot.line = line
            stream_plot.ax.add_line(stream_plot.line)

    def on_eval_each_result(self, stream_plot, val, eval_result):
        x = eval_result.x or eval_result.event_index
        y = val
        pt_label = None

        # if val turns out to be array like, extract x,y
        val_l = utils.is_scaler_array(val)
        if val_l >= 2:
            x, y = val[0], val[1]
        if val_l > 2:
            pt_label = str(val[2])

        xi = len(stream_plot.xdata)
        if pt_label is not None:
            stream_plot.xylabel_texts[xi] = pt_label
        elif xi in stream_plot.xylabel_texts:
            del stream_plot.xylabel_texts[xi]
        stream_plot.xdata.append(x)
        stream_plot.ydata.append(y)

    def render_stream_plot(self, stream_plot):
        stream_plot.line.set_data(stream_plot.xdata, stream_plot.ydata)

        # sync xylabels
        for i, xylabel in stream_plot.xylabel_texts.items():
            if i in stream_plot.xylabel_refs:
                stream_plot.xylabel_refs[i].set_text(xylabel)
                stream_plot.xylabel_refs[i].set_position( \
                    (stream_plot.xdata[i], stream_plot.ydata[i]))
            else:
                stream_plot.xylabel_refs[i] = stream_plot.ax.text( \
                    stream_plot.xdata[i], stream_plot.ydata[i], xylabel)
        for i in list(stream_plot.xylabel_refs.keys()):
            if i not in stream_plot.xylabel_texts:
                label_info = stream_plot.xylabel_refs[i]
                label_info.set_visible(False)
                label_info.remove()
                del stream_plot.xylabel_refs[i]

        stream_plot.ax.relim()
        stream_plot.ax.autoscale_view()

    def clear(self, stream_plot):
        stream_plot.xdata.clear()
        stream_plot.ydata.clear()
        stream_plot.xylabel_texts.clear()

class TextPrinter():
    def __init__(self, prefix=None):
        self.prefix = prefix
    def _add_eval_result(self, eval_result:EvalResult):
        print(self.prefix, eval_result.event_index, eval_result.ended, eval_result.result)
    def show(self, *streams):
        for stream in streams:
            stream.subscribe(self._add_eval_result)

   
