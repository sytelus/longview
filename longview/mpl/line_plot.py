from .base_plot import *

from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from ..lv_types import *
from .. import utils

import numpy as np

class LinePlot(BasePlot):
    def init_stream_plot(self, stream, stream_plot, 
            xtitle='', ytitle='', color=None, xrange=None, yrange=None):
        stream_plot.xylabel_refs = [] # annotation references

        # add main subplot
        if len(self._stream_plots) == 0:
            stream_plot.ax = self.get_main_axis()
        else:
            stream_plot.ax = self.get_main_axis().twinx()

        color = color or plt.cm.Dark2(1.0/(1+len(self._stream_plots)))

        # add default line in subplot
        stream_plot.line = matplotlib.lines.Line2D([], [], 
            label=stream_plot.title or ytitle, color=color) #, linewidth=3
        if stream_plot.opacity is not None:
            stream_plot.line.set_alpha(stream_plot.opacity)
        stream_plot.ax.add_line(stream_plot.line)

        # if more than 2 y-axis then place additional outside
        if len(self._stream_plots) > 1:
            pos = (len(self._stream_plots)) * 30
            stream_plot.ax.spines['right'].set_position(('outward', pos))

        self._stream_plots[stream.stream_name] = stream_plot
        stream_plot.ax.set_xlabel(xtitle)
        stream_plot.ax.set_ylabel(ytitle)
        stream_plot.ax.yaxis.label.set_color(color)
        stream_plot.ax.yaxis.label.set_style('italic')
        stream_plot.ax.xaxis.label.set_style('italic')
        if xrange is not None:
            stream_plot.ax.set_xlim(*xrange)
        if yrange is not None:
            stream_plot.ax.set_ylim(*yrange)

        # redo the legend
        #self.figure.legend(loc='center right', bbox_to_anchor=(1.5, 0.5))
        self.figure.legend(loc='lower right')
        self.figure.tight_layout()


    def clear_plot(self, stream_plot):
        lines = stream_plot.ax.get_lines() 
        # if we need to keep history
        if stream_plot.history_len > 1:
            while len(lines) > stream_plot.history_len-1:
                lines.pop(0).remove()
            # dim old lines
            if stream_plot.dim_history:
                alphas = np.linspace(0.05, 1, len(lines))
                for line, opacity in zip(lines, alphas):
                    line.set_alpha(opacity)
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

    def _plot_eval_result(self, vals, stream_plot, eval_result):
        if not vals:
            return
        line = stream_plot.ax.get_lines()[-1]
        for val in vals:
            x = eval_result.event_index
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


   
