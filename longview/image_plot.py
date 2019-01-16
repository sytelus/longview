from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *
from . import utils
import math
from .base_plot import *
import numpy as np

class ImagePlot(BasePlot):
    def init_stream_plot(self, stream, stream_plot, 
            rows=2, cols=5, img_width=None, img_height=None, img_channels=None,
            colormap=None):
        stream_plot.rows, stream_plot.cols = rows, cols
        stream_plot.img_channels, stream_plot.colormap = img_channels, colormap
        stream_plot.img_width, stream_plot.img_height = img_width, img_height
        # subplots holding each image
        stream_plot.axs = [[None for _ in range(cols)] for _ in range(rows)] 
        # axis image
        stream_plot.ax_imgs = [[None for _ in range(cols)] for _ in range(rows)] 

    def clear_stream_plot(self, stream_plot):
        for row in range(stream_plot.rows):
            for col in range(stream_plot.cols):
                img = stream_plot.ax_imgs[row][col]
                if img:
                    x, y = img.get_size()
                    img.set_data(np.zeros(x, y))

    def render_stream_plot(self, stream_plot, vals, eval_result):
        row, col, i = 0, 0, 0
        for val in vals:
            # extract image, label
            img, label = None, None
            if isinstance(val, tuple):
                if len(val) > 0:
                    img = val[0]
                if len(val) > 1:
                    label = val[1]
            else:
                img = val

            ax = stream_plot.axs[row][col]
            if ax is None:
                ax = stream_plot.axs[row][col] = \
                    self.figure.add_subplot(stream_plot.rows, stream_plot.cols, i+1)
                ax.set_xticks([])
                ax.set_yticks([]) 
            if img is not None:
                if len(img.shape) == 1: # linearized pixels
                    channels = stream_plot.img_channels or 2
                    dim0 = dim1 = int(math.pow(img.shape[0], 1/channels))
                    if channels > 2:
                        dim2 = img.shape[0] - dim0 - dim1
                        img = img.reshape((dim0, dim1, dim2))
                    else:
                        img = img.reshape((dim0, dim1))
                cmap = 'Greys' if stream_plot.colormap is None and len(img.shape) == 2 else stream_plot.colormap
                stream_plot.ax_imgs[row][col] = ax.imshow(img, interpolation="none", cmap=cmap)
            ax.set_title(label)

            row = row+1 if row < stream_plot.rows-1 else 0
            col = col+1 if col < stream_plot.cols-1 else 0
            i += 1
            if i >= stream_plot.rows * stream_plot.cols:
                break
