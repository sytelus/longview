from .base_mpl_plot import BaseMplPlot
import matplotlib
import matplotlib.pyplot as plt
from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from ..lv_types import *
from .. import utils
import ipywidgets as widgets
from IPython import get_ipython
import numpy as np

class LinePlot(BaseMplPlot):
    def __init__(self, cell=None, title=None, show_legend:bool=True, is_3d:bool=False, **plot_args):
        super(LinePlot, self).__init__(cell, title, show_legend, **plot_args)
        self.is_3d = is_3d #TODO: not implemented for mpl

    def init_stream_plot(self, stream_plot, 
            xtitle='', ytitle='', color=None, xrange=None, yrange=None, **stream_plot_args):
        stream_plot.xylabel_refs = [] # annotation references

        # add main subplot
        if len(self._stream_plots) == 0:
            stream_plot.ax = self.get_main_axis()
        else:
            stream_plot.ax = self.get_main_axis().twinx()

        color = color or plt.cm.Dark2((len(self._stream_plots)%8)/8)

        # add default line in subplot
        stream_plot.line = matplotlib.lines.Line2D([], [], 
            label=stream_plot.title or ytitle or str(stream_plot.index), color=color) #, linewidth=3
        if stream_plot.opacity is not None:
            stream_plot.line.set_alpha(stream_plot.opacity)
        stream_plot.ax.add_line(stream_plot.line)

        # if more than 2 y-axis then place additional outside
        if len(self._stream_plots) > 1:
            pos = (len(self._stream_plots)) * 30
            stream_plot.ax.spines['right'].set_position(('outward', pos))

        self._stream_plots[stream_plot.stream.stream_name] = stream_plot
        stream_plot.ax.set_xlabel(xtitle)
        stream_plot.ax.set_ylabel(ytitle)
        stream_plot.ax.yaxis.label.set_color(color)
        stream_plot.ax.yaxis.label.set_style('italic')
        stream_plot.ax.xaxis.label.set_style('italic')
        if xrange is not None:
            stream_plot.ax.set_xlim(*xrange)
        if yrange is not None:
            stream_plot.ax.set_ylim(*yrange)

    def clear_plot(self, stream_plot, clear_history):
        lines = stream_plot.ax.get_lines() 
        # if we need to keep history
        if stream_plot.history_len > 1:
            # make sure we have history len - 1 lines
            lines_keep = 0 if clear_history else stream_plot.history_len-1
            while len(lines) > lines_keep:
                lines.pop(0).remove()
            # dim old lines
            if stream_plot.dim_history and len(lines) > 0:
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

    def _show_eval_results(self, stream_plot, eval_results):
        vals = self._extract_vals(eval_results)
        if not len(vals):
            return False

        line = stream_plot.ax.get_lines()[-1]
        xdata, ydata = line.get_data()
        zdata, anndata, txtdata, clrdata = [], [], [], []

        unpacker = lambda a0=None,a1=None,a2=None,a3=None,a4=None,a5=None, *_:(a0,a1,a2,a3,a4,a5)

        # add each value in trace data
        # each value is of the form:
        # 2D graphs:
        #   y
        #   x [, y [, annotation [, text [, color]]]]
        #   y
        #   x [, y [, z, [annotation [, text [, color]]]]]
        for val in vals:
            # set defaults
            x, y, z =  len(xdata), None, None
            ann, txt, clr = None, None, None

            # if val turns out to be array-like, extract x,y
            val_l = utils.is_scaler_array(val)
            if val_l >= 0:
                if self.is_3d:
                    x, y, z, ann, txt, clr = unpacker(*val)
                else:
                    x, y, ann, txt, clr, _ = unpacker(*val)
            elif isinstance(val, EventVars):
                x = val.x if hasattr(val, 'x') else x
                y = val.y if hasattr(val, 'y') else y
                z = val.z if hasattr(val, 'z') else z
                ann = val.ann if hasattr(val, 'ann') else ann
                txt = val.txt if hasattr(val, 'txt') else txt
                clr = val.clr if hasattr(val, 'clr') else clr

                if y is None:
                    y = next(iter(val.__dict__.values()))
            else:
                y = val

            if ann is not None:
                ann = str(ann)
            if txt is not None:
                txt = str(txt)

            xdata.append(x)
            ydata.append(y)
            zdata.append(z)
            if (txt):
                txtdata.append(txt)
            if clr:
                clrdata.append(clr)
            if ann: #TODO: yref should be y2 for different y axis
                anndata.append(dict(x=x, y=y, xref='x', yref='y', text=ann, showarrow=False))

        line.set_data(xdata, ydata)
        for ann in anndata:
            stream_plot.xylabel_refs.append(stream_plot.ax.text( \
                ann['x'], ann['y'], ann['text']))

        stream_plot.ax.relim()
        stream_plot.ax.autoscale_view()

        return True



   
