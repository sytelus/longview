import tensorwatch as tw
import time
import math
from tensorwatch import utils
utils.set_debug_verbosity(4)

def mpl_line_plot():
    cli = tw.ZmqWatcherClient()
    p = tw.mpl.LinePlot(title='Demo')
    s1 = cli.create_stream(tw.StreamRequest(event_name='ev_i', expr='map(lambda v:math.sqrt(v.val)*2, l)'))
    p.add_subscription(s1, xtitle='Index', ytitle='sqrt(ev_i)')
    p.show()
    tw.plt_loop()

def mpl_history_plot():
    cli = tw.ZmqWatcherClient()
    p2 = tw.mpl.LinePlot(title='History Demo')
    p2s1 = cli.create_stream(tw.StreamRequest(event_name='ev_j', expr='map(lambda v:(v.val, math.sqrt(v.val)*2), l)'))
    p2.add_subscription(p2s1, xtitle='Index', ytitle='sqrt(ev_j)', clear_after_end=True, history_len=15)
    p2.show()
    tw.plt_loop()

def show_stream():
    cli = tw.ZmqWatcherClient()

    print("Subscribing to event ev_i...")
    s1 = cli.create_stream(tw.StreamRequest(event_name="ev_i", expr='map(lambda v:math.sqrt(v.val), l)'))
    r1 = tw.TextVis(title='L1')
    r1.add_subscription(s1)
    r1.show()

    print("Subscribing to event ev_j...")
    s2 = cli.create_stream(tw.StreamRequest(event_name="ev_j", expr='map(lambda v:v.val*v.val, l)'))
    r2 = tw.TextVis(title='L2')
    r2.add_subscription(s2)

    r2.show()
    
    print("Waiting for key...")

    utils.wait_key()

# this no longer directly supported
# TODO: create publisher that allows enumeration from buffered values
def read_stream():
    cli = tw.ZmqWatcherClient()

    with cli.create_stream(tw.StreamRequest(event_name="ev_i", expr='map(lambda v:math.sqrt(v.val), l)')) as s1:
        for stream_item in s1:
            print(stream_item.value)
    print('done')
    utils.wait_key()

def plotly_line_graph():
    cli = tw.ZmqWatcherClient()
    s1 = cli.create_stream(tw.StreamRequest(event_name="ev_i", expr='map(lambda v:math.sqrt(v.val), l)'))

    p = tw.plotly.LinePlot()
    p.add_subscription(s1)
    p.show()

    utils.wait_key()

def plotly_history_graph():
    cli = tw.ZmqWatcherClient()
    p = tw.plotly.LinePlot(title='Demo')
    s2 = cli.create_stream(tw.StreamRequest(event_name='ev_j', expr='map(lambda v:(v.x, v.val), l)'))
    p.add_subscription(s2, ytitle='ev_j', history_len=15)
    p.show()
    utils.wait_key()


#mpl_line_plot()
#mpl_history_plot()
#show_stream()
plotly_line_graph()
plotly_history_graph()
