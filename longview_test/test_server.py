import longview as lv
import time
import random

lv.set_debug_verbosity(4)

srv = lv.WatchServer()

while(True):
    for i in range(1000):
        srv.set_vars("ev_i", val=i*random.random(), x=i)
        print('sent ev_i ', i)
        time.sleep(1)
        for j in range(5):
            srv.set_vars("ev_j", x=j, val=j*random.random())
            print('sent ev_j ', j)
            time.sleep(0.5)
        srv.end_event("ev_j")
    srv.end_event("ev_i")