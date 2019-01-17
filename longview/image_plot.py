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

    @staticmethod
    def linear_to_2d(stream_plot, img_in):
        if img_in is not None and len(img_in.shape) == 1: # linearized pixels
            channels = stream_plot.img_channels or 2
            if stream_plot.img_width:
                dim0, dim1 = stream_plot.img_width, stream_plot.img_height
            else:
                dim0 = dim1 = int(math.pow(img_in.shape[0], 1/channels))
            if channels > 2:
                dim2 = img_in.shape[0] - dim0 - dim1
                img_in = img_in.reshape((dim0, dim1, dim2))
            else:
                img_in = img_in.reshape((dim0, dim1))
        return img_in

    def render_stream_plot(self, stream_plot, vals, eval_result):
        row, col, i = 0, 0, 0
        for val in vals:
            val = val if isinstance(val, tuple) else (val,)
            unpacker = lambda a0,a1=None,a2=None,a3=None:(a0,a1,a2,a3)
            img_in, label_in, img_out, label_out = unpacker(*val)
            img_in, img_out = ImagePlot.linear_to_2d(stream_plot, img_in), \
                ImagePlot.linear_to_2d(stream_plot, img_out)

            # combine in out images
            if img_out is not None:
                img_in = np.hstack((img_in, img_out))
            if label_out is not None:
                label_in = label_in + ' ' + label_out

            ax = stream_plot.axs[row][col]
            if ax is None:
                ax = stream_plot.axs[row][col] = \
                    self.figure.add_subplot(stream_plot.rows, stream_plot.cols, i+1)
                ax.set_xticks([])
                ax.set_yticks([]) 
            if img_in is not None:
                dim = len(img_in.shape)
                if dim == 1: # linearized pixels
                    channels = stream_plot.img_channels or 2
                    dim0 = dim1 = int(math.pow(img_in.shape[0], 1/channels))
                    if channels > 2:
                        dim2 = img_in.shape[0] - dim0 - dim1
                        img_in = img_in.reshape((dim0, dim1, dim2))
                    else:
                        img_in = img_in.reshape((dim0, dim1))
                cmap = 'Greys' if stream_plot.colormap is None and \
                    (dim == 2 or (dim == 3 and img_in.shape[2] == 1)) else stream_plot.colormap
                stream_plot.ax_imgs[row][col] = ax.imshow(img_in, interpolation="none", cmap=cmap)
            ax.set_title(label_in)

            row = row+1 if row < stream_plot.rows-1 else 0
            col = col+1 if col < stream_plot.cols-1 else 0
            i += 1
            if i >= stream_plot.rows * stream_plot.cols:
                break
