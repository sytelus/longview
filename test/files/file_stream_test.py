from tensorwatch.watcher import Watcher
from tensorwatch.stream import Stream
from tensorwatch.file_stream import FileStream
from tensorwatch.mpl.line_plot import LinePlot
from tensorwatch.image_utils import plt_loop
import tensorwatch as tw

def file_write():
    watcher = Watcher()
    file_obs = FileStream(file_name=r'c:\temp\obs.txt', for_write=True, console_debug=True)
    stream = watcher.create_stream('lambda vars:(vars.x, vars.x**2)', subscribers=[file_obs])

    for i in range(5):
        watcher.observe(x=i)

def file_read():
    file_obs = FileStream(file_name=r'c:\temp\obs.txt', for_write=False)
    vis = tw.create_vis(file_obs, type='mpl-line')
    vis.show()
    plt_loop()

def main():
    file_write()
    file_read()

main()

