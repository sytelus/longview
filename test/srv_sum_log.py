import tensorwatch as tw
import time, math

sum = 0
for i in range(1000):
    sum += i
    tw.observe(sum=sum)
    time.sleep(1)
