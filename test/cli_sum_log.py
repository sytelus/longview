import tensorwatch as tw
from tensorwatch import utils
utils.set_debug_verbosity(5)

import matplotlib.pyplot as plt
import time

#r = tw.open(type='mpl-line')
#r.show()
#r2=tw.open('map(lambda x:math.sqrt(x.sum), l)', cell=r.cell)
#r3=tw.open('map(lambda x:math.sqrt(x.sum), l)', renderer=r2)

cli = tw.WatchClient()
p = tw.mpl.LinePlot(title='Demo')
s1 = cli.create_stream('', 'map(lambda v:v.sum, l)')
p.add(s1, xtitle='Index', ytitle='sqrt(ev_i)')

while(True):
    plt.draw()
    plt.pause(0.01)
    time.sleep(1)