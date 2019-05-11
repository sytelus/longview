from tensorwatch.watcher import Watcher
from tensorwatch.stream import Stream
from tensorwatch.file_stream import FileStream
from tensorwatch.mpl.line_plot import LinePlot
from tensorwatch.image_utils import plt_loop
import tensorwatch as tw

def file_write():
    watcher = Watcher()
    stream = watcher.create_stream(expr='lambda vars:(vars.x, vars.x**2)', 
        devices=[r'c:\temp\obs.txt'])

    for i in range(5):
        watcher.observe(x=i)

def file_read():
    watcher = Watcher()
    stream = watcher.open_stream(devices=[r'c:\temp\obs.txt'])
    vis = tw.create_vis(stream, type='mpl-line')
    vis.show()
    plt_loop()

def main():
    file_write()
    file_read()

main()

