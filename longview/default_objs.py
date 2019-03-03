from .watch_server import *
from .watch_client import *
from .text_printer import *

default_watch_server = None
default_watch_client = None

########################## server APIs
def start_watch():
    global default_watch_server
    if not default_watch_server:
        default_watch_server = WatchServer()

def _ensure_server():
    start_watch()

def log(event_name:str='', stream_name='', **vars) -> None:
    _ensure_server()
    default_watch_server.log(event_name, stream_name, **vars)

def observe(event_name:str='', **vars) -> None:
    _ensure_server()
    default_watch_server.observe(event_name, **vars)

def set_globals(**vars):
    _ensure_server()
    default_watch_server.set_globals(**vars)

def stop_watch():
    if default_watch_server:
        default_watch_server.close()
        default_watch_server = None

########################## client APIs
def _ensure_client():
    global default_watch_client
    if not default_watch_client:
        default_watch_client = WatchClient()

def as_text(eval_expr:str=None, event_name:str='', stream_name:str=None, throttle=None, 
            clear_after_end=True, clear_after_each=False):
    _ensure_client()

    render = TextPrinter()
    
    stream = default_watch_client.create_stream(event_name=event_name, 
        eval_expr=eval_expr or 'map(lambda x:x, l)', stream_name=stream_name, throttle=throttle)
    render.add(stream, clear_after_end=clear_after_end, clear_after_each=clear_after_each)

    return render
