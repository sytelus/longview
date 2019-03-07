from . import mpl
from . import plotly
from .watch_server import WatchServer
from .watch_client import WatchClient
from .text_printer import TextPrinter
from .model_graph.hiddenlayer import graph
from .receptive_field.rf_utils import plot_receptive_field, plot_grads_at
from .img_utils import show_image, open_image, img2pyt
from .data_utils import pyt_ds2list, sample_by_class

default_servers = []
default_clients = []

########################## server APIs
def start_watch(srv_id=0):
    global default_servers
    if srv_id == len(default_servers):
        default_servers.append(WatchServer())
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
def _ensure_client(cli_id):
    global default_clients
    if cli_id == len(default_clients):
        default_clients.append(WatchClient())
    #TODO error handling

def _get_renderer(type, cell, title):
    if type is None:
        return TextPrinter(cell=cell, title=title)

    if type in ['text', 'summary']:
        return TextPrinter(cell=cell, title=title)
    elif type in ['line', 'plotly-line', 'scatter', 'plotly-scatter', 
                        'line3d', 'scatter3d', 'mesh3d']:
        return plotly.LinePlot(cell=cell, title=title, 
                                is_3d=type in ['line3d', 'scatter3d', 'mesh3d'])
    elif type in ['image', 'mpl-image']:
        return mpl.ImagePlot(cell=cell, title=title)
    elif type in ['mpl-line', 'mpl-scatter']:
        return mpl.LinePlot(cell=cell, title=title)
    else:
        raise ValueError('Render type parameter has invalid value: "{}"'.format(type))

def get_client(cli_id):
    return default_clients
def get_server(srv_id):
    return default_servers[srv_id]


def open(expr:str=None, event_name:str='', stream_name:str=None, throttle=None, 
            clear_after_end=True, clear_after_each=False, show:bool=None, 
            cell=None, title=None, vis=None, type=None, only_summary=False, 
            history_len=1, dim_history=True, opacity=None,
            separate_yaxis=True, xtitle=None, ytitle=None, ztitle=None, color=None,
            xrange=None, yrange=None, zrange=None, draw_line=True, draw_marker=False, cli_id=0):

    _ensure_client(cli_id)

    if type:
        draw_line = 'scatter' not in type
        only_summary = 'summary' == type

    vis = vis or _get_renderer(type, cell, title)
    
    stream = default_clients[cli_id].create_stream(event_name=event_name, 
        expr=expr, stream_name=stream_name, throttle=throttle)

    vis.add(stream, clear_after_end=clear_after_end, clear_after_each=clear_after_each, only_summary=only_summary,
                 show=show, history_len=history_len, dim_history=dim_history, opacity=opacity,
                 separate_yaxis=separate_yaxis, xtitle=xtitle, ytitle=ytitle, ztitle=ztitle, color=color,
                 xrange=xrange, yrange=yrange, zrange=zrange, draw_line=draw_line, draw_marker=draw_marker)

    return vis

def draw_model(model, input_shape=None, orientation='TB'): #orientation = 'LR' for landscpe
    g = graph.build_graph(model, input_shape)
    return g

