import tensorwatch as tw
from tensorwatch import utils
utils.set_debug_verbosity(5)

r = tw.open(type='line')
r.show()
#r2=tw.open('map(lambda x:math.sqrt(x.sum), l)', cell=r.cell)
#r3=tw.open('map(lambda x:math.sqrt(x.sum), l)', renderer=r2)

utils.wait_key()