from .base_mpl_plot import BaseMplPlot
from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from ..lv_types import *
from .. import utils, image_utils
import math, time
import numpy as np
import skimage.transform
import ipywidgets as widgets
from IPython import get_ipython

class ImagePlot(BaseMplPlot):
    def init_stream_plot(self, stream_plot, 
            rows=2, cols=5, img_width=None, img_height=None, img_channels=None,
            colormap=None, viz_img_scale=None, **stream_plot_args):
        stream_plot.rows, stream_plot.cols = rows, cols
        stream_plot.img_channels, stream_plot.colormap = img_channels, colormap
        stream_plot.img_width, stream_plot.img_height = img_width, img_height
        stream_plot.viz_img_scale = viz_img_scale
        # subplots holding each image
        stream_plot.axs = [[None for _ in range(cols)] for _ in range(rows)] 
        # axis image
        stream_plot.ax_imgs = [[None for _ in range(cols)] for _ in range(rows)] 

    def clear_plot(self, stream_plot, clear_history):
        for row in range(stream_plot.rows):
            for col in range(stream_plot.cols):
                img = stream_plot.ax_imgs[row][col]
                if img:
                    x, y = img.get_size()
                    img.set_data(np.zeros((x, y)))

    def _show_stream_items(self, stream_plot, stream_items):
        # as we repaint each image plot, select last if multiple events were pending
        stream_item = None
        for er in reversed(stream_items):
            if not(er.ended or er.value is None):
                stream_item = er
                break
        if stream_item is None:
            return False

        row, col, i = 0, 0, 0
        dirty = False
        # stream_item.value is expected to be ImagePlotItems
        for image_list in stream_item.value:
            # convert to imshow compatible, stitch images
            images = [image_utils.to_imshow_array(img, stream_plot.img_width, stream_plot.img_height) \
                for img in image_list.images if img is not None]
            img_viz = image_utils.stitch_horizontal(images, width_dim=1)

            # resize if requested
            if stream_plot.viz_img_scale is not None:
                img_viz = skimage.transform.rescale(img_viz, 
                    (stream_plot.viz_img_scale, stream_plot.viz_img_scale), mode='reflect', preserve_range=True)

            # create subplot if it doesn't exist
            ax = stream_plot.axs[row][col]
            if ax is None:
                ax = stream_plot.axs[row][col] = \
                    self.figure.add_subplot(stream_plot.rows, stream_plot.cols, i+1)
                ax.set_xticks([])
                ax.set_yticks([])  

            cmap = image_list.cmap or ('Greys' if stream_plot.colormap is None and \
                len(img_viz.shape) == 2 else stream_plot.colormap)

            stream_plot.ax_imgs[row][col] = ax.imshow(img_viz, interpolation="none", cmap=cmap, alpha=image_list.alpha)
            dirty = True

            # set title
            title = image_list.title
            if len(title) > 12: #wordwrap if too long
                title = utils.wrap_string(title) if len(title) > 24 else title
                fontsize = 8
            else:
                fontsize = 12
            ax.set_title(title, fontsize=fontsize) #'fontweight': 'light'

            #ax.autoscale_view() # not needed
            col = col + 1
            if col >= stream_plot.cols:
                col = 0
                row = row + 1
                if row >= stream_plot.rows:
                    break
            i += 1

        return dirty

    
    def has_legend(self):
        return self.show_legend or False