from .stream import Stream
from .vis_base import VisBase
import ipywidgets as widgets

class Visualizer:
    def __init__(self, stream:Stream, vis_type:str=None, host:'Visualizer'=None, 
            cell:'Visualizer'=None, title:str=None, 
            clear_after_end=False, clear_after_each=False, history_len=1, dim_history=True, opacity=None,

            rows=2, cols=5, img_width=None, img_height=None, img_channels=None,
            colormap=None, viz_img_scale=None,

            # these image params are for hover on point for t-sne
            hover_images=None, hover_image_reshape=None, cell_width:str=None, cell_height:str=None, 

            only_summary=False, separate_yaxis=True, xtitle=None, ytitle=None, ztitle=None, color=None,
            xrange=None, yrange=None, zrange=None, draw_line=True, draw_marker=False,

            vis_args={}, stream_vis_args={})->None:

        cell = cell._host_base.cell if cell is not None else None

        if host:
            self._host_base = host._host_base
        else:
            self._host_base = self._get_vis_base(vis_type, cell, title, hover_images=hover_images, hover_image_reshape=hover_image_reshape, 
                                   cell_width=cell_width, cell_height=cell_height, 
                                   rows=rows, cols=cols, img_width=img_width, img_height=img_height, img_channels=img_channels,
                                   colormap=colormap, viz_img_scale=viz_img_scale,
                                   **vis_args)

        self._host_base.subscribe(stream, show=False, clear_after_end=clear_after_end, clear_after_each=clear_after_each,
            history_len=history_len, dim_history=dim_history, opacity=opacity, 
            only_summary=only_summary if 'summary' != vis_type else True,
            separate_yaxis=separate_yaxis, xtitle=xtitle, ytitle=ytitle, ztitle=ztitle, color=color,
            xrange=xrange, yrange=yrange, zrange=zrange, 
            draw_line=draw_line if vis_type is not None and 'scatter' in vis_type else True, 
            draw_marker=draw_marker, **stream_vis_args)

        stream.load()

    def show(self):
        return self._host_base.show()

    def _get_vis_base(self, vis_type, cell:widgets.Box, title, hover_images=None, hover_image_reshape=None, cell_width=None, cell_height=None, **vis_args)->VisBase:
        if vis_type is None:
            from .text_vis import TextVis
            return TextVis(cell=cell, title=title, **vis_args)
        if vis_type in ['text', 'summary']:
            from .text_vis import TextVis
            return TextVis(cell=cell, title=title, **vis_args)
        if vis_type in ['plotly-line', 'scatter', 'plotly-scatter', 
                            'line3d', 'scatter3d', 'mesh3d']:
            from . import plotly
            return plotly.LinePlot(cell=cell, title=title, 
                                    is_3d=vis_type in ['line3d', 'scatter3d', 'mesh3d'], **vis_args)
        if vis_type in ['image', 'mpl-image']:
            from . import mpl
            return mpl.ImagePlot(cell=cell, title=title, cell_width=cell_width, cell_height=cell_height, **vis_args)
        if vis_type in ['line', 'mpl-line', 'mpl-scatter']:
            from . import mpl
            return mpl.LinePlot(cell=cell, title=title, **vis_args)
        if vis_type in ['tsne', 'embeddings', 'tsne2d', 'embeddings2d']:
            from . import plotly
            return plotly.EmbeddingsPlot(cell=cell, title=title, is_3d='2d' not in vis_type, 
                                         hover_images=hover_images, hover_image_reshape=hover_image_reshape, **vis_args)
        else:
            raise ValueError('Render vis_type parameter has invalid value: "{}"'.format(vis_type))
