from .stream import Stream
from .vis_base import VisBase
import ipywidgets as widgets

class Visualizer:
    def __init__(self, stream:Stream, vis_type:str=None, host:'Visualizer'=None, 
            cell:widgets.Box=None, title:str=None, 
            clear_after_end=False, clear_after_each=False, history_len=1, dim_history=True, opacity=None,
            images=None, images_reshape=None, width=None, height=None, 
            vis_args=None, stream_vis_args=None)->None:
        vis_args = vis_args or {}
        stream_vis_args = stream_vis_args or {}

        if host:
            self._host_base = host._host_base
        else:
            self._host_base = self._get_vis_base(vis_type, cell, title, images=images, images_reshape=images_reshape, 
                                   width=width, height=height, **vis_args)

        self._host_base.subscribe(stream, show=False, clear_after_end=clear_after_end, clear_after_each=clear_after_each,
                     history_len=history_len, dim_history=dim_history, opacity=opacity, **stream_vis_args)

        stream.load()

    def show(self):
        self._host_base.show()

    def _get_vis_base(self, vis_type, cell:widgets.Box, title, images=None, images_reshape=None, width=None, height=None, **vis_args)->VisBase:
        if vis_type is None:
            from .text_vis import TextVis
            return TextVis(cell=cell, title=title, **vis_args)
        if vis_type in ['text', 'summary']:
            from .text_vis import TextVis
            return TextVis(cell=cell, title=title, **vis_args)
        if vis_type in ['line', 'plotly-line', 'scatter', 'plotly-scatter', 
                            'line3d', 'scatter3d', 'mesh3d']:
            from . import plotly
            return plotly.LinePlot(cell=cell, title=title, 
                                    is_3d=vis_type in ['line3d', 'scatter3d', 'mesh3d'], **vis_args)
        if vis_type in ['image', 'mpl-image']:
            from . import mpl
            return mpl.ImagePlot(cell=cell, title=title, width=width, height=height, **vis_args)
        if vis_type in ['mpl-line', 'mpl-scatter']:
            from . import mpl
            return mpl.LinePlot(cell=cell, title=title, **vis_args)
        if vis_type in ['tsne', 'embeddings', 'tsne2d', 'embeddings2d']:
            from . import plotly
            return plotly.EmbeddingsPlot(cell=cell, title=title, is_3d='2d' not in vis_type, 
                                         images=images, images_reshape=images_reshape, **vis_args)
        else:
            raise ValueError('Render vis_type parameter has invalid value: "{}"'.format(vis_type))
