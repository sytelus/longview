from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from .lv_types import *
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class LinePlot():
    def __init__(self):
        self.x_data = []
        self.y_data = []
        self.figure = plt.figure()
        self.line, = plt.plot(self.x_data, self.y_data)
        self.animation = FuncAnimation(self.figure, self._on_update, interval=200) #ms

    def _add_eval_result(self, eval_result:EvalResult):
        if not eval_result.ended:
            self.x_data.append(eval_result.event_index)
            self.y_data.append(eval_result.result)
        #else:
        #    self.animation.event_source.stop()

    def _on_update(self, frame):
        print('on update')
        self.line.set_data(self.x_data, self.y_data)
        self.figure.gca().relim()
        self.figure.gca().autoscale_view()
        return self.line,

    def show(self, *streams):
        for stream in streams:
            stream.subscribe(self._add_eval_result)
        return plt.show()

class TextPrinter():
    def __init__(self, prefix=None):
        self.prefix = prefix
    def _add_eval_result(self, eval_result:EvalResult):
        print(self.prefix, eval_result.event_index, eval_result.ended, eval_result.result)
    def show(self, *streams):
        for stream in streams:
            stream.subscribe(self._add_eval_result)

   
