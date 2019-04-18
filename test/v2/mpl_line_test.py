from tensorwatch.v2.watcher import Watcher
from tensorwatch.v2.mpl.line_plot import LinePlot
from tensorwatch.v2.image_utils import plt_loop
from tensorwatch.v2.publisher import Publisher
from tensorwatch.v2.lv_types import StreamItem


def main():
    watcher = Watcher()
    line_plot = LinePlot()
    pub = watcher.create_stream('lambda vars:vars.x', subscribers=[line_plot])
    line_plot.add_subscription(pub)
    line_plot.show()

    for i in range(5):
        watcher.observe(x=(i, i*i))
    plt_loop()

main()

