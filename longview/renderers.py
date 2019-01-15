from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *
from . import utils
from .base_plot import *
import numpy as np

class ImagePlot(BasePlot):
    def init_stream_plot(self, stream, stream_plot, 
            rows=2, columns=5):
        stream_plot.columns = columns
        #stream_plot.rows = rows
        stream_plot.axs = [] 


class LinePlot(BasePlot):
    def init_stream_plot(self, stream, stream_plot, 
            xlabel='', ylabel='', color=None, alpha=1, xlim=None, ylim=None):
        stream_plot.xylabel_refs = [] # annotation references

        # add main subplot
        if len(self._stream_plots) == 0:
            stream_plot.ax = self.get_main_axis()
        else:
            stream_plot.ax = self.get_main_axis().twinx()

        color = color or plt.cm.hsv(1.0/(1+len(self._stream_plots)))
        stream_plot.label = stream_plot.label or ylabel

        # add default line in subplot
        stream_plot.line = matplotlib.lines.Line2D([], [], 
            label=stream_plot.label, color=color) #, linewidth=3
        stream_plot.line.set_alpha(alpha)
        stream_plot.ax.add_line(stream_plot.line)

        # if more than 2 y-axis then place additional outside
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
        self.figure.legend(loc='center right', bbox_to_anchor=(1.5, 0.5))

    def clear_stream_plot(self, stream_plot):
        lines = stream_plot.ax.get_lines() 
        # if we need to keep history
        if stream_plot.keep_old > 0:
            while len(lines) > stream_plot.keep_old:
                lines.pop(0).remove()
            # dim old lines
            if stream_plot.dim_old:
                alphas = np.linspace(0.05, 1, len(lines))
                for line, alpha in zip(lines, alphas):
                    line.set_alpha(alpha)
                    line.set_linewidth(1)
            # add new line
            line = matplotlib.lines.Line2D([], [], linewidth=3)
            stream_plot.ax.add_line(line)
        else: #clear current line
            lines[-1].set_data([], [])

        # remove annotations
        for label_info in stream_plot.xylabel_refs:
            label_info.set_visible(False)
            label_info.remove()
        stream_plot.xylabel_refs.clear()

    def render_stream_plot(self, stream_plot, vals, eval_result):
        line = stream_plot.ax.get_lines()[-1]
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

            xdata, ydata = line.get_data()
            xdata.append(x)
            ydata.append(y)
            line.set_data(xdata, ydata)

            # add annotation
            if pt_label:
                stream_plot.xylabel_refs.append(stream_plot.ax.text( \
                    x, y, pt_label))

            stream_plot.ax.relim()
            stream_plot.ax.autoscale_view()

class TextPrinter():
    def __init__(self, prefix=None):
        self.prefix = prefix
    def _add_eval_result(self, eval_result:EvalResult):
        print(self.prefix, eval_result.event_index, eval_result.ended, eval_result.result)
    def show(self, *streams):
        for stream in streams:
            stream.subscribe(self._add_eval_result)

   
