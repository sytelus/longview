import matplotlib.pyplot as plt
from ipywidgets import Layout, Output
from IPython.display import display, clear_output
import numpy as np
from .line_plot import LinePlot
from .. import utils

class EmbeddingsPlot(LinePlot):
    def __init__(self, cell=None, title=None, show_legend:bool=False, is_3d:bool=True, 
                 images=None, images_reshape=None, **plot_args):
        utils.set_default(plot_args, 'height', '8in')
        super(EmbeddingsPlot, self).__init__(cell, title, show_legend, is_3d=is_3d, **plot_args)
        if images is not None:
            plt.ioff()
            self.image_output = Output()
            self.image_figure = plt.figure(figsize=(1,1))
            self.image_ax = self.image_figure.add_subplot(111)
            self.cell.children += (self.image_output,)
            plt.ion()
        self.images, self.images_reshape = images, images_reshape

    def hover_fn(self, trace, points, state):
        if not points:
            return
        ind = points.point_inds[0]
        if ind > len(self.images) or ind < 0:
            return
        with self.image_output:
            plt.ioff()

            if self.images_reshape:
                img = np.reshape(self.images[ind], self.images_reshape)
            else:
                img = self.images[ind]
            if img is not None:
                clear_output(wait=True)    
                self.image_ax.imshow(img)
            display(self.image_figure)
            plt.ion()

        return None

    def _create_trace(self, stream_plot):
        stream_plot.stream_args.clear() #TODO remove this
        utils.set_default(stream_plot.stream_args, 'draw_line', False)
        utils.set_default(stream_plot.stream_args, 'draw_marker', True)
        utils.set_default(stream_plot.stream_args, 'draw_marker_text', True)
        utils.set_default(stream_plot.stream_args, 'hoverinfo', 'text')
        utils.set_default(stream_plot.stream_args, 'marker', {})

        marker = stream_plot.stream_args['marker']
        utils.set_default(marker, 'size', 6)
        utils.set_default(marker, 'colorscale', 'Jet')
        utils.set_default(marker, 'showscale', False)
        utils.set_default(marker, 'opacity', 0.8)

        return super(EmbeddingsPlot, self)._create_trace(stream_plot)

    def add(self, *kargs, **kwargs):
        super(EmbeddingsPlot, self).add(*kargs, **kwargs)
        stream_plot = next(iter(self._stream_plots.values()))
        if stream_plot.index == 0 and self.images is not None:
            self.widget.data[stream_plot.trace_index].on_hover(self.hover_fn)