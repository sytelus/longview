import plotly.graph_objs as go

from .base_plot import BasePlot
from ..lv_types import *
from .. import utils

class LinePlot(BasePlot):
    def _setup_layout(self, stream_plot, **layout_args):
        xtitle = layout_args.get('xtitle',None)
        ytitle = layout_args.get('ytitle',None)
        trace_id = stream_plot.trace_id

        if xtitle:
            xaxis = self.figwig.layout['xaxis' + str(trace_id+1)]
            xaxis.title = xtitle
        if ytitle:
            key = 'yaxis' + str(trace_id+1)
            self.figwig.layout[key] = {'title':ytitle, 
                                       'overlaying':'y', 'side':'left' if trace_id==0 else 'right' }

    def _get_trace(self, stream_plot):
        yaxis = 'y' + str(stream_plot.trace_id + 1)
        trace = go.Scatter(x=[], y=[], mode='lines', name=stream_plot.title, yaxis=yaxis)
        return trace

    def _plot_eval_result(self, vals, stream_plot, eval_result):
        trace = self.figwig.data[stream_plot.trace_id]
        xdata, ydata = list(trace.x), list(trace.y)
        for val in vals:
            x = eval_result.event_index
            y = val
            pt_label = None

            # if val turns out to be array-like, extract x,y
            val_l = utils.is_scaler_array(val)
            if val_l >= 2:
                x, y = val[0], val[1]
            if val_l > 2:
                pt_label = str(val[2])

            # TODO: below will cause O(n^2) perf issue
            # https://community.plot.ly/t/why-does-data-in-scatter-trace-gets-converted-from-list-to-tuple/20060
            xdata.append(x)
            ydata.append(y)

            # add annotation
            #if pt_label:
            #    stream_plot.xylabel_refs.append(stream_plot.ax.text( \
            #        x, y, pt_label))

        self.figwig.data[stream_plot.trace_id].x, self.figwig.data[stream_plot.trace_id].y = xdata, ydata   

    