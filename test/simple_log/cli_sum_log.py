import tensorwatch as tw
from tensorwatch import utils
utils.set_debug_verbosity(4)

import matplotlib.pyplot as plt
import time

#r = tw.create_vis(type='mpl-line')
#r.show()
#r2=tw.create_vis('map(lambda x:math.sqrt(x.sum), l)', cell=r.cell)
#r3=tw.create_vis('map(lambda x:math.sqrt(x.sum), l)', renderer=r2)

def show_mpl():
    cli = tw.ZmqWatcherClient()
    p = tw.mpl.LinePlot(title='Demo')
    s1 = cli.create_stream('lambda v:v.sum')
    p.add_subscription(s1, xtitle='Index', ytitle='sqrt(ev_i)')
    p.show()
    
    tw.plt_loop()

def show_text():
    text = tw.create_vis()
    text.show()
    input('Waiting')

#show_text()
show_mpl()