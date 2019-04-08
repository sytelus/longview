import plotly.graph_objs as go
import ipywidgets as widgets
from IPython import get_ipython
from .base_plot import BasePlot
from ..lv_types import *
from .. import utils

class LinePlot(BasePlot):
    def __init__(self, cell=None, title=None, show_legend:bool=True, is_3d:bool=False, **plot_args):
        super(LinePlot, self).__init__(cell, title, show_legend, **plot_args)
        self.is_3d = is_3d

    def _setup_layout(self, stream_plot):
        # handle multiple y axis
        yaxis = 'yaxis' + (str(stream_plot.index + 1) if stream_plot.separate_yaxis else '')

        xaxis = 'xaxis' + str(stream_plot.index+1)
        axis_props = BasePlot._get_axis_common_props(stream_plot.xtitle, stream_plot.xrange)
        #axis_props['rangeslider'] = dict(visible = True)
        self.widget.layout[xaxis] = axis_props

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

        if self.is_3d:
            zaxis = 'zaxis' #+ str(stream_plot.index+1)
            axis_props = BasePlot._get_axis_common_props(stream_plot.ztitle, stream_plot.zrange)
            self.widget.layout.scene[zaxis] = axis_props
            self.widget.layout.margin = dict(l=0, r=0, b=0, t=0)
            self.widget.layout.hoverdistance = 1

    def _create_2d_trace(self, stream_plot, mode, hoverinfo, marker, line):
        yaxis = 'y' + (str(stream_plot.index + 1) if stream_plot.separate_yaxis else '')

        trace = go.Scatter(x=[], y=[], mode=mode, name=stream_plot.title or stream_plot.ytitle, yaxis=yaxis, hoverinfo=hoverinfo,
                           line=line, marker=marker)
        return trace

    def _create_3d_trace(self, stream_plot, mode, hoverinfo, marker, line):
        trace = go.Scatter3d(x=[], y=[], z=[], mode=mode, name=stream_plot.title or stream_plot.ytitle, hoverinfo=hoverinfo,
                           line=line, marker=marker)
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
        draw_marker_text = stream_plot.stream_args.get('draw_marker_text',False)
        hoverinfo = stream_plot.stream_args.get('hoverinfo',None)
        marker = stream_plot.stream_args.get('marker',{})
        line = stream_plot.stream_args.get('line',{})
        utils.set_default(line, 'color', stream_plot.color or BasePlot.get_pallet_color(stream_plot.index))
        
        mode = 'lines' if draw_line else ''
        if draw_marker:
            mode = ('' if mode=='' else mode+'+') + 'markers'
        if draw_marker_text:
            mode = ('' if mode=='' else mode+'+') + 'text'

        if self.is_3d:
            return self._create_3d_trace(stream_plot, mode, hoverinfo, marker, line)  
        else:
            return self._create_2d_trace(stream_plot, mode, hoverinfo, marker, line)  

    def _plot_eval_result(self, stream_plot, eval_result):
        vals = BasePlot._extract_vals(eval_result)
        if vals is None:
            return False

        # get trace data
        trace = self.widget.data[stream_plot.trace_index]
        xdata, ydata, zdata, anndata, txtdata, clrdata = list(trace.x), list(trace.y), [], [], [], []
        if self.is_3d:
            zdata = list(trace.z)

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
            x, y, z =  eval_result.event_index, None, None
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
            if txt is not None:
                txtdata.append(txt)
            if clr is not None:
                clrdata.append(clr)
            if ann: #TODO: yref should be y2 for different y axis
                anndata.append(dict(x=x, y=y, xref='x', yref='y', text=ann, showarrow=False))

        self.widget.data[stream_plot.trace_index].x = xdata
        self.widget.data[stream_plot.trace_index].y = ydata   
        if self.is_3d:
            self.widget.data[stream_plot.trace_index].z = zdata

        # add text
        if len(txtdata):
            exisitng = self.widget.data[stream_plot.trace_index].text
            exisitng = list(exisitng) if utils.is_array_like(exisitng) else []
            exisitng += txtdata
            self.widget.data[stream_plot.trace_index].text = exisitng

        # add annotation
        if len(anndata):
            existing = list(self.widget.layout.annotations)
            existing += anndata
            self.widget.layout.annotations = existing

        # add color
        if len(clrdata):
            exisitng = self.widget.data[stream_plot.trace_index].marker.color
            exisitng = list(exisitng) if utils.is_array_like(exisitng) else []
            exisitng += clrdata
            self.widget.data[stream_plot.trace_index].marker.color = exisitng

        return True

    def clear_plot(self, stream_plot):
        self.widget.data[stream_plot.trace_index].x = []
        self.widget.data[stream_plot.trace_index].y = []   
        if self.is_3d:
            self.widget.data[stream_plot.trace_index].z = []
        self.widget.data[stream_plot.trace_index].text = ""
        # TODO: avoid removing annotations for other streams
        self.widget.layout.annotations = []
