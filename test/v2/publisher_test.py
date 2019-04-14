from tensorwatch.v2.publisher import Publisher

class c1:
    def m1(self,val):
        print('m1', val)

    def m2(self,val):
        print('m2', val)

k = c1()
p1 = Publisher()
p1.subscribe(k.m1)
p1.subscribe(k.m2)

p1.write('ha1')
p1.write('ha2')

