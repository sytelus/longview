import time
import tensorwatch as tw
from tensorwatch import utils

utils.set_debug_verbosity(5)

srv = tw.RemoteWatcherServer()

sum = 0
for i in range(10000):
    sum += i
    srv.observe(i=i, sum=sum)
    #print(i, sum)
    time.sleep(1)
