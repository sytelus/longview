from tensorwatch.v2.watcher import Watcher
from tensorwatch.v2.publisher import Publisher

def main():
    watcher = Watcher()
    console_pub = Publisher(name = 'S1', console_debug=True)
    pub = watcher.create_stream('lambda vars:vars.x**2', subscribers=[console_pub])

    for i in range(5):
        watcher.observe(x=i)

main()


