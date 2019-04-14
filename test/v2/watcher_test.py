from tensorwatch.v2.watcher import Watcher
from tensorwatch.v2.publisher import Publisher


watcher = Watcher()
console_pub = Publisher(print_prefix = 'S1')
pub = watcher.create_stream('lambda vars:vars.x**2', subscribers=[console_pub])

for i in range(5):
    watcher.observe(x=i)

