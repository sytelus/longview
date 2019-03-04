import longview as lv
import time
import math
from longview import utils
utils.set_debug_verbosity(4)

def mpl_line_plot():
    cli = lv.WatchClient()
    p = lv.mpl.LinePlot('Demo')
    s1 = cli.create_stream('ev_i', 'map(lambda v:math.sqrt(v.val)*2, l)')
    p.add(s1, xtitle='Index', ytitle='sqrt(ev_i)')
    utils.wait_ley()

def mpl_history_plot():
    cli = lv.WatchClient()
    p2 = lv.mpl.LinePlot('History Demo')
    p2s1 = cli.create_stream('ev_j', 'map(lambda v:(v.val, math.sqrt(v.val)*2), l)')
    p2.add(p2s1, xtitle='Index', ytitle='sqrt(ev_j)', clear_after_end=True, history_len=15)

def show_stream():
    cli = lv.WatchClient()

    print("Subscribing to event ev_i...")
    s1 = cli.create_stream("ev_i", 'map(lambda v:math.sqrt(v.val), l)')
    r1 = lv.TextPrinter('L1')
    r1.show(s1)

    print("Subscribing to event ev_j...")
    s2 = cli.create_stream("ev_j", 'map(lambda v:v.val*v.val, l)')
    r2 = lv.TextPrinter('L2')
    r2.show(s2)
    
    print("Waiting for key...")

    utils.wait_ley()

def read_stream():
    cli = lv.WatchClient()

    with cli.create_stream("ev_i", 'map(lambda v:math.sqrt(v.val), l)') as s1:
        for eval_result in s1:
            print(eval_result.result)
    print('done')
    utils.wait_ley()

def plotly_line_graph():
    cli = lv.WatchClient()
    s1 = cli.create_stream("ev_i", 'map(lambda v:math.sqrt(v.val), l)')

    p = lv.plotly.LinePlot()
    p.add(s1)
    print(p.figwig)

    utils.wait_ley()

def plotly_history_graph():
    cli = lv.WatchClient()
    p = lv.plotly.LinePlot('Demo')
    s2 = cli.create_stream('ev_j', 'map(lambda v:(v.x, v.val), l)')
    p.add(s2, ytitle='ev_j', history_len=15)
    utils.wait_ley()
