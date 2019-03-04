import longview as lv
import time
from longview import utils
utils.set_debug_verbosity(4)

sum = 0
for i in range(1000):
    sum += i
    # print(i, sum)
    lv.observe(sum=sum)
    time.sleep(1)
