from tensorwatch.watcher import Watcher
from tensorwatch.stream import Stream

def main():
    watcher = Watcher()
    console_pub = Stream(name = 'S1', console_debug=True)
    stream = watcher.create_stream('lambda vars:vars.x**2', subscribers=[console_pub])

    for i in range(5):
        watcher.observe(x=i)

main()


