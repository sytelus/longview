from .line_plot import *
import numpy as np

class ArrayPlot(LinePlot):
    def __init__(self, title=None):
        super(ArrayPlot, self).__init__(title)
        self.figwig.layout.showlegend = False

    def _create_trace(self, stream_plot):
        super(ArrayPlot, self)._create_trace(stream_plot)

        # keep current trace in history
        stream_plot.trace_history = [stream_plot.trace_index]
        stream_plot.trace_history_index = 0
         
    def _plot_eval_result(self, vals, stream_plot, eval_result):
        history_len = stream_plot.stream_args.get('history_len', 0)
        new_on_end = stream_plot.stream_args.get('new_on_end', False)
        new_on_eval = stream_plot.stream_args.get('new_on_eval', False)
        dim_history = stream_plot.stream_args.get('dim_history', True)
        
        if new_on_eval or (new_on_end and eval_result.ended):
            if history_len > 0:
                if history_len > len(stream_plot.trace_history):
                    # add new trace
                    cur_history_index = len(stream_plot.trace_history)
                    trace = self._create_trace(stream_plot)
                    self.figwig.add_trace(trace)
                    stream_plot.trace_history.append(len(self.figwig.data)-1)
                else:
                    # rotate trace
                    cur_history_index = (stream_plot.trace_history_index + 1) % history_len

                stream_plot.trace_history_index = cur_history_index
                stream_plot.trace_index = stream_plot.trace_history[cur_history_index]
                if dim_history:
                    history_len = len(stream_plot.trace_history)
                    alphas = list(reversed(np.linspace(0.05, 1, history_len)))
                    for i, thi in enumerate(range(cur_history_index, cur_history_index+history_len)):
                        thi = thi % history_len
                        trace_index = stream_plot.trace_history[thi]
                        self.figwig.data[trace_index].opacity = alphas[i]

            self.figwig.data[stream_plot.trace_index].x = []
            self.figwig.data[stream_plot.trace_index].y = []   

        super(ArrayPlot, self)._plot_eval_result(vals, stream_plot, eval_result)

    def clear_plot(self, stream_plot):
        for thi in range(cur_history_index, cur_history_index+history_len):
            thi = thi % history_len
            trace_index = stream_plot.trace_history[thi]
            self.figwig.data[trace_index].x = []
            self.figwig.data[trace_index].y = []  

