import plotly 
import plotly.offline
import plotly.tools as tls
import plotly.graph_objs as go
import time

from ..lv_types import *
from .. import utils

class Plotter:
    def __init__(self, title=None, rows=None, cols=None, subplot_titles=None):
        self.title, self.rows, self.cols = title, rows, cols
        self._stream_plots = {}
        
        if rows or cols:
            subplot = tls.make_subplots(rows, cols, print_grid=False, 
                                        subplot_titles=subplot_titles)
            self.figwig = go.FigureWidget(subplot)
        else:
            self.figwig = go.FigureWidget()
            self.rows, self.cols = rows, cols
        self.figwig.layout.title = title
        
    @staticmethod
    def _get_subplot_id(row, col, cols):
        cols = cols or 1
        row, col = int(row or 0), int(col or 0)
        return str(row * cols + col + 1)

    def add(self, stream, style='line', title=None, row=None, col=None, 
            xtitle=None, ytitle=None, show:bool=True):
        if stream:
            plot_title = title or (stream.stream_name \
                if not utils.is_uuid4(stream.stream_name) else ytitle)

            stream_plot = StreamPlot(stream, throttle=None, redraw_on_end=False, 
                title=plot_title, redraw_after=float('inf'), keep_old=False, dim_old=True)
            self._stream_plots[stream.stream_name] = stream_plot
        
            # plotly rebuilds trace object after assigning to figwig :(
            trace = Plotter._get_trace(stream_plot, style)
            self.figwig.add_trace(trace, row=row, col=col)
            stream_plot.trace = self.figwig.data[-1]
            xaxis = self.figwig.layout['xaxis' + Plotter._get_subplot_id(row, col, self.cols)]
            xaxis.title = xtitle
            yaxis = self.figwig.layout['yaxis' + Plotter._get_subplot_id(row, col, self.cols)]
            yaxis.title = ytitle

            if not (self.title or self.rows or self.cols):
                self.title = stream_plot.title
                self.figwig.layout.title = self.title
            
            stream.subscribe(self._add_eval_result)
            if show:
                plotly.offline.iplot(self.figwig)
            return self.figwig
            
    def show(self):
        plotly.offline.iplot(self.figwig)
        return self.figwig
                
    @staticmethod
    def _get_trace(stream_plot, style):
        return go.Scatter(x=[], y=[], mode='lines', name=stream_plot.title)
         
    @staticmethod
    def _process_eval_result(stream_plot, eval_result, ):
        if eval_result.ended:
            if stream_plot.redraw_on_end:
                stream_plot.redraw_countdown = 0
            vals = None
        elif eval_result.result is not None:
            stream_plot.redraw_countdown -= 1
            vals = eval_result.result
            if not utils.is_array_like(eval_result.result, tuple_is_array=False):
                vals = [vals]
        return vals
    
    @staticmethod
    def _plot_eval_result(stream_plot, eval_result):
        vals = Plotter._process_eval_result(stream_plot, eval_result)
        if vals is None:
            return
        
        trace = stream_plot.trace
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
            xdata, ydata = list(trace.x), list(trace.y)
            xdata.append(x)
            ydata.append(y)
            trace.x, trace.y = xdata, ydata

            # add annotation
            #if pt_label:
            #    stream_plot.xylabel_refs.append(stream_plot.ax.text( \
            #        x, y, pt_label))

        
    def _add_eval_result(self, eval_result:EvalResult, stream_reset:bool):
        """Callback whenever EvalResult becomes available"""
        stream_plot = self._stream_plots.get(eval_result.stream_name, None)
        if stream_plot is not None:
            if stream_reset:
                utils.debug_log("Stream reset", eval_result.event_name)
                self.redraw_countdown = 0
            if eval_result is not None:
                # check throttle
                if stream_plot.throttle is None or stream_plot.last_update is None or \
                        time.time() - stream_plot.last_update >= stream_plot.throttle:

                    Plotter._plot_eval_result(stream_plot, eval_result)

                    # update for throttle
                    stream_plot.last_update = time.time()
                else:
                    utils.debug_log("Value not plotted due to throttle", 
                                    eval_result.event_name, verbosity=5)
        else:
            print("Unrecognized stream received: {}".format(eval_result.stream_name))
