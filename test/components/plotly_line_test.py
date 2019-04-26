from tensorwatch.watcher import Watcher
from tensorwatch.plotly.line_plot import LinePlot
from tensorwatch.image_utils import plt_loop
from tensorwatch.publisher import Publisher
from tensorwatch.lv_types import StreamItem


def main():
    watcher = Watcher()
    line_plot = LinePlot()
    pub = watcher.create_stream('lambda vars:vars.x', subscribers=[line_plot])
    line_plot.subscribe(pub)
    line_plot.show()

    for i in range(5):
        watcher.observe(x=(i, i*i))

main()

