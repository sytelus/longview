import longview as lv


e = lv.Evaler('reduce(lambda x,y: x+y, map(lambda x:x**2, filter(lambda x: x%2==0, l)))')
for i in range(5):
    r, b = e.post(i)
    print(i, r, b)
r, b = e.post(ended=True)
print(i, r, b)
