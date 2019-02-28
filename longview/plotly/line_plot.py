import plotly.graph_objs as go

from .base_plot import BasePlot
from ..lv_types import *
from .. import utils

class LinePlot(BasePlot):
    def _setup_layout(self, stream_plot):
        xtitle = stream_plot.stream_args.get('xtitle',None)
        ytitle = stream_plot.stream_args.get('ytitle',None)
        ztitle = stream_plot.stream_args.get('ztitle',None)
        
        yaxis = 'yaxis' + (str(stream_plot.index + 1) if stream_plot.separate_yaxis else '')
        if xtitle:
            xaxis = 'xaxis' + str(stream_plot.index+1)
            axis_props = BasePlot._get_axis_common_props(xtitle)
            self.figwig.layout[xaxis] = axis_props
        if ytitle:
            # handle multiple Y-Axis plots
            color = self.figwig.data[stream_plot.trace_index].line.color
            yaxis = 'yaxis' + (str(stream_plot.index + 1) if stream_plot.separate_yaxis else '')
            axis_props = BasePlot._get_axis_common_props(ytitle)
            axis_props['linecolor'] = color
            axis_props['tickfont']=axis_props['titlefont'] = dict(color=color)
            if stream_plot.index > 0 and stream_plot.separate_yaxis:
                axis_props['overlaying'] = 'y'
                axis_props['side'] = 'right'
                if stream_plot.index > 1:
                    self.figwig.layout.xaxis = dict(domain=[0, 1 - 0.085*(stream_plot.index-1)])
                    axis_props['anchor'] = 'free'
                    axis_props['position'] = 1 - 0.085*(stream_plot.index-2)
            self.figwig.layout[yaxis] = axis_props

    def _create_trace(self, stream_plot):
        separate_yaxis = stream_plot.stream_args.get('separate_yaxis', True)
        stream_plot.separate_yaxis = separate_yaxis

        yaxis = 'y' + (str(stream_plot.index + 1) if separate_yaxis else '')

        trace = go.Scatter(x=[], y=[], mode='lines', name=stream_plot.title, yaxis=yaxis,
                           line=dict(color=BasePlot.get_pallet_color(stream_plot.index)))
        return trace

    def _plot_eval_result(self, vals, stream_plot, eval_result):
        if not vals:
            return
        trace = self.figwig.data[stream_plot.trace_index]
        xdata, ydata = list(trace.x), list(trace.y)
        for val in vals:
            x =  eval_result.event_index
            y = val
            pt_label = None

            # if val turns out to be array-like, extract x,y
            val_l = utils.is_scaler_array(val)
            if val_l >= 2:
                x, y = val[0], val[1]
            if val_l > 2:
                pt_label = str(val[2])

            xdata.append(x)
            ydata.append(y)

            # add annotation
            #if pt_label:
            #    stream_plot.xylabel_refs.append(stream_plot.ax.text( \
            #        x, y, pt_label))

        self.figwig.data[stream_plot.trace_index].x, self.figwig.data[stream_plot.trace_index].y = xdata, ydata   

    