from tensorwatch.watcher import Watcher
from tensorwatch.stream import Stream

def main():
    watcher = Watcher()
    console_pub = Stream(stream_name = 'S1', console_debug=True)
    stream = watcher.get_stream(expr='lambda vars:vars.x**2')
    console_pub.subscribe(stream)

    for i in range(5):
        watcher.observe(x=i)

main()


