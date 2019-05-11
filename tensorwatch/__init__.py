from typing import Iterable, Sequence, Union

from .remote_watcher_client import RemoteWatcherClient
from .remote_watcher_server import RemoteWatcherServer
from .watcher import Watcher

from .text_vis import TextVis
from . import plotly
from . import mpl

from .stream import Stream
from .array_stream import ArrayStream
from .lv_types import ImagePlotItem, VisParams
from . import utils

###### Import methods for tw namespace #########
from .receptive_field.rf_utils import plot_receptive_field, plot_grads_at
from .embeddings.tsne_utils import get_tsne_components
from .model_graph.torchstat_utils import model_stats
from .image_utils import show_image, open_image, img2pyt, linear_to_2d, plt_loop
from .data_utils import pyt_ds2list, sample_by_class, col2array, search_similar


_default_servers = {}
_default_clients = {}
_watcher = None

########################## server APIs
def start_watch(srv_id=0):
    global _default_servers
    if srv_id not in _default_servers:
        server = RemoteWatcherServer(port_offset=srv_id)
        _default_servers[srv_id] = server
    return _default_servers[srv_id]

def get_server(srv_id):
    return start_watch(srv_id)

def observe(event_name:str='', srv_id=0, **vars) -> None:
    get_server(srv_id).observe(event_name, **vars)

def set_globals(srv_id=0, **vars):
    get_server(srv_id).set_globals(**vars)

def stop_watch(srv_id=0):
    global _default_servers
    if srv_id in _default_servers:
        _default_servers[srv_id].close()
        _default_servers.pop(srv_id, None)

########################## client APIs
def get_client(cli_id):
    global _default_clients
    if cli_id not in _default_clients:
        client = RemoteWatcherClient(port_offset=cli_id)
        _default_clients[cli_id] = client
    return _default_clients[cli_id]

def get_watcher():
    global _watcher
    if _watcher is None:
        _watcher = Watcher()
    return _watcher

def _get_vis(vis_type, cell, title, images=None, images_reshape=None, width=None, height=None, **vis_args):
    if vis_type is None:
        return TextVis(cell=cell, title=title, **vis_args)
    if vis_type in ['text', 'summary']:
        return TextVis(cell=cell, title=title, **vis_args)
    if vis_type in ['line', 'plotly-line', 'scatter', 'plotly-scatter', 
                        'line3d', 'scatter3d', 'mesh3d']:
        return plotly.LinePlot(cell=cell, title=title, 
                                is_3d=vis_type in ['line3d', 'scatter3d', 'mesh3d'], **vis_args)
    if vis_type in ['image', 'mpl-image']:
        return mpl.ImagePlot(cell=cell, title=title, width=width, height=height, **vis_args)
    if vis_type in ['mpl-line', 'mpl-scatter']:
        return mpl.LinePlot(cell=cell, title=title, **vis_args)
    if vis_type in ['tsne', 'embeddings', 'tsne2d', 'embeddings2d']:
        return plotly.EmbeddingsPlot(cell=cell, title=title, is_3d='2d' not in vis_type, 
                                     images=images, images_reshape=images_reshape, **vis_args)
    else:
        raise ValueError('Render vis_type parameter has invalid value: "{}"'.format(vis_type))

def _get_target(cli_id:int, srv_id:int)->Union[Watcher, RemoteWatcherServer, RemoteWatcherClient]:
    if cli_id is not None  and srv_id is not None:
        raise ValueError('cli_id and srv_id cannot both be not None')
    target = None
    if cli_id is not None:
        target = get_client(cli_id)
    elif srv_id is not None:
        target = get_server(srv_id)
    else:
        target = get_watcher()
    return target

def create_stream(stream_name:str=None, devices:Sequence[str]=None, event_name:str='',
        expr=None, throttle:float=1, vis_params:VisParams=None, cli_id:int=None, srv_id:int=None):
    target = _get_target(cli_id, srv_id)
    stream = target.create_stream(stream_name=stream_name, devices=devices,
        event_name=event_name, expr=expr, throttle=throttle, vis_params=vis_params)

    return stream

def create_vis(stream, vis_type=None, host_vis=None, 
            cell=None, title=None, 
            clear_after_end=False, clear_after_each=False, history_len=1, dim_history=True, opacity=None,
            images=None, images_reshape=None, width=None, height=None, vis_args={}, stream_vis_args={}):

    if vis_type:
        draw_line = 'scatter' not in vis_type
        only_summary = 'summary' == vis_type

    host_vis = host_vis or _get_vis(vis_type, cell, title, images=images, images_reshape=images_reshape, 
                               width=width, height=height, **vis_args)

    s = host_vis.subscribe(stream, show=False, clear_after_end=clear_after_end, clear_after_each=clear_after_each,
                 history_len=history_len, dim_history=dim_history, opacity=opacity, **stream_vis_args)

    if utils.has_method(stream, 'read_all'):
        stream.read_all()

    return host_vis

def draw_model(model, input_shape=None, orientation='TB'): #orientation = 'LR' for landscpe
    from .model_graph.hiddenlayer import graph
    g = graph.build_graph(model, input_shape)
    return g


