from .base_plot import *
from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from ..lv_types import *
from .. import utils
import math
import numpy as np
import skimage.transform
import ipywidgets as widgets
from IPython import get_ipython

class ImagePlot(BasePlot):
    def init_stream_plot(self, stream, stream_plot, 
            rows=2, cols=5, img_width=None, img_height=None, img_channels=None,
            colormap=None, viz_img_scale=None):
        stream_plot.rows, stream_plot.cols = rows, cols
        stream_plot.img_channels, stream_plot.colormap = img_channels, colormap
        stream_plot.img_width, stream_plot.img_height = img_width, img_height
        stream_plot.viz_img_scale = viz_img_scale
        # subplots holding each image
        stream_plot.axs = [[None for _ in range(cols)] for _ in range(rows)] 
        # axis image
        stream_plot.ax_imgs = [[None for _ in range(cols)] for _ in range(rows)] 

    def clear_plot(self, stream_plot):
        for row in range(stream_plot.rows):
            for col in range(stream_plot.cols):
                img = stream_plot.ax_imgs[row][col]
                if img:
                    x, y = img.get_size()
                    img.set_data(np.zeros(x, y))

    @staticmethod
    def to_2d(stream_plot, img_in):
        if img_in is not None:
            if len(img_in.shape) == 1: # linearized pixels
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
            elif len(img_in.shape) == 2:
                img_in = np.swapaxes(img_in, 0, 1) # transpose H,W for imshow
            else:
                if img_in.shape[0] > 3:
                    img_in = img_in[0:1,:,:] # TODO allow config
                img_in = np.swapaxes(img_in, 2, 1) # transpose H,W for imshow

        return img_in

    def _plot_eval_result(self, vals, stream_plot, eval_result):
        if not vals:
            return

        row, col, i = 0, 0, 0
        for val in vals:
            val = val if isinstance(val, tuple) else (val,)
            unpacker = lambda a0,a1=None,a2=None,a3=None,a4=None:(a0,a1,a2,a3,a4)
            img_in, label_in, img_tar, img_out, img_tar_weights = unpacker(*val)
            img_in, img_tar, img_out, img_tar_weights = ImagePlot.to_2d(stream_plot, img_in), \
                ImagePlot.to_2d(stream_plot, img_tar), \
                ImagePlot.to_2d(stream_plot, img_out), \
                ImagePlot.to_2d(stream_plot, img_tar_weights)

            # combine in out images
            if img_out is not None and img_tar is not None and img_tar_weights is not None:
                img_viz = np.hstack((img_in, img_tar, img_out, img_tar_weights))
            elif img_out is not None and img_tar is not None:
                img_viz = np.hstack((img_in, img_tar, img_out))
            elif img_out is not None:
                img_viz = np.hstack((img_in, img_out))
            elif img_tar is not None:
                img_viz = np.hstack((img_in, img_tar, np.zeros_like(img_tar)))
            elif img_tar is not None:
                img_viz = np.hstack((img_in, img_tar, np.zeros_like(img_tar)))
            else:
                img_viz = img_in

            ax = stream_plot.axs[row][col]
            if ax is None:
                ax = stream_plot.axs[row][col] = \
                    self.figure.add_subplot(stream_plot.rows, stream_plot.cols, i+1)
                ax.set_xticks([])
                ax.set_yticks([]) 

            if img_viz is not None:
                dim = len(img_viz.shape)
                if dim == 1: # linearized pixels
                    channels = stream_plot.img_channels or 2
                    dim0 = dim1 = int(math.pow(img_viz.shape[0], 1/channels))
                    if channels > 2:
                        dim2 = img_viz.shape[0] - dim0 - dim1
                        img_viz = img_viz.reshape((dim0, dim1, dim2))
                    else:
                        img_viz = img_viz.reshape((dim0, dim1))
                elif dim == 3:
                    if img_viz.shape[0] == 1:
                        img_viz = np.squeeze(img_viz, axis=0)
                        dim = 2
                    else:
                        img_viz = np.swapaxes(img_viz, 0, 2)
                        img_viz = np.swapaxes(img_viz, 1, 0)
                img_viz = np.swapaxes(img_viz, 1, 0)  # transpose H,W for imshow


                # else leave things as-is

                cmap = 'Greys' if stream_plot.colormap is None and \
                    dim == 2 else stream_plot.colormap

                if stream_plot.viz_img_scale is not None:
                    if len(img_viz.shape) > 2:
                        scaled_shape = (*(img_viz.shape[:-1]*np.array(stream_plot.viz_img_scale)), img_viz.shape[-1])
                    else:
                        scaled_shape = tuple(img_viz.shape * np.array(stream_plot.viz_img_scale))
                    img_viz = skimage.transform.resize(img_viz, scaled_shape)

                stream_plot.ax_imgs[row][col] = ax.imshow(img_viz, interpolation="none", cmap=cmap)

            ax.set_title(label_in)

            row = row+1 if row < stream_plot.rows-1 else 0
            col = col+1 if col < stream_plot.cols-1 else 0
            i += 1
            if i >= stream_plot.rows * stream_plot.cols:
                break
