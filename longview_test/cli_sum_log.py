import longview as lv
from longview import utils
utils.set_debug_verbosity(5)

r = lv.render(renderer='summary')
r.show()
#r2=lv.render('map(lambda x:math.sqrt(x.sum), l)', cell=r.cell)
#r3=lv.render('map(lambda x:math.sqrt(x.sum), l)', renderer=r2)

utils.wait_key()