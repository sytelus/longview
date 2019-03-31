import time
import tensorwatch as tw

sum = 0
for i in range(10000):
    sum += i
    tw.observe(sum=sum)
    time.sleep(1)
