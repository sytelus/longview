from tensorwatch.stream import Stream

class c1:
    def m1(self,val):
        print('m1', val)

    def m2(self,val):
        print('m2', val)

k = c1()
p1 = Stream()
p1.add_callback(k.m1)
p1.add_callback(k.m2)

p1.write('ha1')
p1.write('ha2')

