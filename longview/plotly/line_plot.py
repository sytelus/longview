import plotly.graph_objs as go
import ipywidgets as widgets
from IPython import get_ipython
from .base_plot import BasePlot
from ..lv_types import *
from .. import utils

class LinePlot(BasePlot):
    def __init__(self, cell=None, title=None, show_legend:bool=True, is_3d:bool=False):
        super(LinePlot, self).__init__(cell, title, show_legend)
        self.is_3d = is_3d

    def _setup_layout(self, stream_plot):
        # handle multiple y axis
        yaxis = 'yaxis' + (str(stream_plot.index + 1) if stream_plot.separate_yaxis else '')

        if stream_plot.xtitle:
            xaxis = 'xaxis' + str(stream_plot.index+1)
            axis_props = BasePlot._get_axis_common_props(stream_plot.xtitle, stream_plot.xrange)
            self.widget.layout[xaxis] = axis_props
        if stream_plot.ytitle:
            # handle multiple Y-Axis plots
            color = self.widget.data[stream_plot.trace_index].line.color
            yaxis = 'yaxis' + (str(stream_plot.index + 1) if stream_plot.separate_yaxis else '')
            axis_props = BasePlot._get_axis_common_props(stream_plot.ytitle, stream_plot.yrange)
            axis_props['linecolor'] = color
            axis_props['tickfont']=axis_props['titlefont'] = dict(color=color)
            if stream_plot.index > 0 and stream_plot.separate_yaxis:
                axis_props['overlaying'] = 'y'
                axis_props['side'] = 'right'
                if stream_plot.index > 1:
                    self.widget.layout.xaxis = dict(domain=[0, 1 - 0.085*(stream_plot.index-1)])
                    axis_props['anchor'] = 'free'
                    axis_props['position'] = 1 - 0.085*(stream_plot.index-2)
            self.widget.layout[yaxis] = axis_props
        if self.is_3d and stream_plot.ztitle:
            zaxis = 'zaxis' #+ str(stream_plot.index+1)
            axis_props = BasePlot._get_axis_common_props(stream_plot.ztitle, stream_plot.zrange)
            self.widget.layout.scene[zaxis] = axis_props

    def _create_2d_trace(self, stream_plot, mode):
        yaxis = 'y' + (str(stream_plot.index + 1) if stream_plot.separate_yaxis else '')

        trace = go.Scatter(x=[], y=[], mode=mode, name=stream_plot.title or stream_plot.ytitle, yaxis=yaxis,
                           line=dict(color=(stream_plot.color or BasePlot.get_pallet_color(stream_plot.index))))
        return trace

    def _create_3d_trace(self, stream_plot, mode):
        trace = go.Scatter3d(x=[], y=[], z=[], mode=mode, name=stream_plot.title or stream_plot.ytitle,
                           line=dict(color=(stream_plot.color or BasePlot.get_pallet_color(stream_plot.index))))
        return trace


    def _create_trace(self, stream_plot):
        stream_plot.separate_yaxis = stream_plot.stream_args.get('separate_yaxis', True)
        stream_plot.xtitle = stream_plot.stream_args.get('xtitle',None)
        stream_plot.ytitle = stream_plot.stream_args.get('ytitle',None)
        stream_plot.ztitle = stream_plot.stream_args.get('ztitle',None)
        stream_plot.color = stream_plot.stream_args.get('color',None)
        stream_plot.xrange = stream_plot.stream_args.get('xrange',None)
        stream_plot.yrange = stream_plot.stream_args.get('yrange',None)
        stream_plot.zrange = stream_plot.stream_args.get('zrange',None)
        
        draw_line = stream_plot.stream_args.get('draw_line',True)
        draw_marker = stream_plot.stream_args.get('draw_marker',True)
        mode = 'lines' if draw_line else ''
        mode = ('' if mode=='' else mode+'+') + 'markers' if draw_marker else ''

        if self.is_3d:
            return self._create_3d_trace(stream_plot, mode)  
        else:
            return self._create_2d_trace(stream_plot, mode)  

    def _plot_eval_result(self, vals, stream_plot, eval_result):
        if not vals:
            return

        # get trace data
        trace = self.widget.data[stream_plot.trace_index]
        xdata, ydata, zdata, pt_labels = list(trace.x), list(trace.y), [], []
        if self.is_3d:
            zdata = list(trace.z)

        # add each value in trace data
        for val in vals:
            x =  eval_result.event_index
            y = val
            z = None
            pt_label = None

            # if val turns out to be array-like, extract x,y
            val_l = utils.is_scaler_array(val)
            if val_l > 1:
                x, y = val[0], val[1]
            if val_l > 2:
                if self.is_3d:
                    z = val[2]
                    if val_l > 3:
                        pt_label = str(val[3])
                else:
                    pt_label = str(val[2])

            xdata.append(x)
            ydata.append(y)
            zdata.append(z)

            if pt_label:
                pt_labels.append(dict(x=x, y=y, xref='x', yref='y', text=pt_label, showarrow=False))

        self.widget.data[stream_plot.trace_index].x = xdata
        self.widget.data[stream_plot.trace_index].y = ydata   
        if self.is_3d:
            self.widget.data[stream_plot.trace_index].z = zdata
        self.widget.layout.annotations = []
        for x, y, pt_label in zip(xdata, ydata, pt_labels):
            # add annotation
            if pt_label:
                self.widget.layout.annotations = pt_labels

    def clear_plot(self, stream_plot):
        self.widget.data[stream_plot.trace_index].x = []
        self.widget.data[stream_plot.trace_index].y = []   
        if self.is_3d:
            self.widget.data[stream_plot.trace_index].z = []
