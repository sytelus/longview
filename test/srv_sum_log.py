import tensorwatch as tw
import time, math
from tensorwatch import utils
utils.set_debug_verbosity(4)

sum, sumsq = 0, 0
for i in range(1000):
    sum += i
    sumsq += math.sqrt(i)
    # print(i, sum)
    lv.observe(sum=sum, sumsq=sumsq)
    time.sleep(1)
