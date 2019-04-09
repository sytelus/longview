from . import mpl
from . import plotly
from .watch_server import WatchServer
from .watch_client import WatchClient
from .text_vis import TextVis
from .model_graph.hiddenlayer import graph
from .array_stream import ArrayStream
from .stream_base import StreamBase
from .lv_types import ImagePlotItem

###### Import methods #########
from .receptive_field.rf_utils import plot_receptive_field, plot_grads_at
from .embeddings.tsne_utils import get_tsne_components
from .model_graph.torchstat_utils import model_stats
from .image_utils import show_image, open_image, img2pyt, linear_to_2d
from .data_utils import pyt_ds2list, sample_by_class, col2array, search_similar


default_servers = []
default_clients = []

########################## server APIs
def start_watch(srv_id=0, heartbeat_timeout=600):
    global default_servers
    if srv_id == len(default_servers):
        default_servers.append(WatchServer(heartbeat_timeout=heartbeat_timeout))
    #TODO error handling

def _ensure_server(srv_id):
    start_watch(srv_id)

def observe(event_name:str='', srv_id=0, **vars) -> None:
    _ensure_server(srv_id)
    default_servers[srv_id].observe(event_name, **vars)

def set_globals(srv_id=0, **vars):
    _ensure_server(srv_id)
    default_servers[srv_id].set_globals(**vars)

def stop_watch(srv_id=0):
    #TODO error handling
    default_servers[srv_id].close()

########################## client APIs
def _ensure_client(cli_id, heartbeat_timeout=600):
    global default_clients
    if cli_id == len(default_clients):
        default_clients.append(WatchClient(heartbeat_timeout=heartbeat_timeout))
    #TODO error handling

def _get_renderer(type, cell, title, images=None, images_reshape=None, width=None, height=None):
    if type is None:
        return TextVis(cell=cell, title=title)

    if type in ['text', 'summary']:
        return TextVis(cell=cell, title=title)
    elif type in ['line', 'plotly-line', 'scatter', 'plotly-scatter', 
                        'line3d', 'scatter3d', 'mesh3d']:
        return plotly.LinePlot(cell=cell, title=title, 
                                is_3d=type in ['line3d', 'scatter3d', 'mesh3d'])
    elif type in ['image', 'mpl-image']:
        return mpl.ImagePlot(cell=cell, title=title, width=width, height=height)
    elif type in ['mpl-line', 'mpl-scatter']:
        return mpl.LinePlot(cell=cell, title=title)
    elif type in ['tsne', 'embeddings', 'tsne2d', 'embeddings2d']:
        return plotly.EmbeddingsPlot(cell=cell, title=title, is_3d='2d' not in type, 
                                     images=images, images_reshape=images_reshape)
    else:
        raise ValueError('Render type parameter has invalid value: "{}"'.format(type))

def get_client(cli_id):
    return default_clients
def get_server(srv_id):
    return default_servers[srv_id]


def open(expr=None, event_name:str='', stream_name:str=None, throttle=1, 
            clear_after_end=True, clear_after_each=False,
            cell=None, title=None, vis=None, type=None, only_summary=False, 
            history_len=1, dim_history=True, opacity=None,
            separate_yaxis=True, xtitle=None, ytitle=None, ztitle=None, color=None,
            xrange=None, yrange=None, zrange=None, draw_line=True, draw_marker=False, cli_id=0,
            rows=2, cols=5, img_width=None, img_height=None, img_channels=None,
            colormap=None, viz_img_scale=None, images=None, images_reshape=None, width=None, 
            height=None, heartbeat_timeout=600):

    _ensure_client(cli_id, heartbeat_timeout=heartbeat_timeout)

    if type:
        draw_line = 'scatter' not in type
        only_summary = 'summary' == type

    vis = vis or _get_renderer(type, cell, title, images=images, images_reshape=images_reshape, width=width, height=height)
    
    if expr is None or isinstance(expr, str):
        stream = default_clients[cli_id].create_stream(event_name=event_name, 
            expr=expr, stream_name=stream_name, throttle=throttle)
    elif utils.is_array_like(expr):
        stream = ArrayStream(expr)
    elif isinstance(expr, StreamBase):
        stream = expr

    s = vis.add(stream, show=False, clear_after_end=clear_after_end, clear_after_each=clear_after_each, only_summary=only_summary,
                 history_len=history_len, dim_history=dim_history, opacity=opacity,
                 separate_yaxis=separate_yaxis, xtitle=xtitle, ytitle=ytitle, ztitle=ztitle, color=color,
                 xrange=xrange, yrange=yrange, zrange=zrange, draw_line=draw_line, draw_marker=draw_marker, 
                rows=rows, cols=cols, img_width=img_width, img_height=img_height, img_channels=img_channels,
                colormap=colormap, viz_img_scale=viz_img_scale)

    if isinstance(stream, ArrayStream):
        stream.send_all()

    return vis

def draw_model(model, input_shape=None, orientation='TB'): #orientation = 'LR' for landscpe
    g = graph.build_graph(model, input_shape)
    return g


