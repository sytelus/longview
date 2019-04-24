#from IPython import get_ipython, display
#if get_ipython():
#    get_ipython().magic('matplotlib notebook')

import matplotlib
#if os.name == 'posix' and "DISPLAY" not in os.environ:
#    matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!
import matplotlib.pyplot as plt
import matplotlib.lines
from matplotlib.animation import FuncAnimation
from ipywidgets.widgets.interaction import show_inline_matplotlib_plots
from ipykernel.pylab.backend_inline import flush_figures

from ..vis_base import VisBase

import os, sys, time, threading, traceback, logging, queue
from typing import List, Set, Dict, Tuple, Optional, Callable, Iterable, Union, Any
from abc import ABC, abstractmethod
from ..lv_types import *
from .. import utils
from IPython import get_ipython, display
import ipywidgets as widgets

class BaseMplPlot(VisBase):
    def __init__(self, cell=None, title:str=None, show_legend:bool=None, publisher_name:str=None, console_debug:bool=False, **plot_args):
        super(BaseMplPlot, self).__init__(widgets.Output(), cell, title, show_legend, publisher_name=publisher_name, console_debug=console_debug, **plot_args)

        self._fig_init_done = False
        self.show_legend = show_legend
        # graph objects
        self.figure = None
        self._ax_main = None
        # matplotlib animation
        self.animation = None
        #print(matplotlib.get_backend())
        #display.display(self.cell)

    # anim_interval in seconds
    def init_fig(self, anim_interval:float=1.0):
        """(for derived class) Initializes matplotlib figure"""
        if self._fig_init_done:
            return False

        # create figure and animation
        self.figure = plt.figure(figsize=(8, 3))
        self.anim_interval = anim_interval

        plt.set_cmap('Dark2')
        plt.rcParams['image.cmap']='Dark2'

        self._fig_init_done = True
        return True

    def get_main_axis(self):
        # if we don't yet have main axis, create one
        if not self._ax_main:
            # by default assign one subplot to whole graph
            self._ax_main = self.figure.add_subplot(111)
            self._ax_main.grid(True)
            # change the color of the top and right spines to opaque gray
            self._ax_main.spines['right'].set_color((.8,.8,.8))
            self._ax_main.spines['top'].set_color((.8,.8,.8))
            if self.title is not None:
                title = self._ax_main.set_title(self.title)
                title.set_weight('bold')
        return self._ax_main

    def _on_update(self, frame):
        try:
            self._update_stream_plots()
        except Exception as ex:
            # when exception occurs here, animation will stop and there
            # will be no further plot updates
            # TODO: may be we don't need all of below but none of them
            #   are popping up exception in Jupyter Notebook because these
            #   exceptions occur in background?
            self.last_ex = ex
            print(ex)
            logging.fatal(ex, exc_info=True) 
            traceback.print_exc(file=sys.stdout)

    def show(self, blocking=False):
        if not self.is_shown and self.anim_interval:
            self.animation = FuncAnimation(self.figure, self._on_update, interval=self.anim_interval*1000.0)
        super(BaseMplPlot, self).show(blocking)

    def _post_update_stream_plot(self, stream_plot):
        utils.debug_log("Plot updated", stream_plot.stream.name, verbosity=5)

        if self.layout_dirty:
            # do not do tight_layout() call on every update 
            # that would jumble up the graphs! it should only called
            # once each time there is change in layout
            self.figure.tight_layout()
            self.layout_dirty = False

        # below forces redraw and it was helpful to
        # repaint even if there was error in interval loop
        # but it does work in native UX and not in Jupyter Notebook
        #self.figure.canvas.draw()
        #self.figure.canvas.flush_events()

        if self._use_hbox and get_ipython():
            self.widget.clear_output(wait=True)
            with self.widget:
                plt.show(self.figure)

                # everything else that doesn't work
                #self.figure.show()
                #display.clear_output(wait=True)
                #display.display(self.figure)
                #flush_figures()
                #plt.show()
                #show_inline_matplotlib_plots()
        #elif not get_ipython():
        #    self.figure.canvas.draw()

    def _post_add_subscription(self, stream_plot, **stream_plot_args):
        # make sure figure is initialized
        self.init_fig()        
        self.init_stream_plot(stream_plot, **stream_plot_args) 

        # redo the legend
        #self.figure.legend(loc='center right', bbox_to_anchor=(1.5, 0.5))
        if self.show_legend:
            self.figure.legend(loc='lower right')
        plt.subplots_adjust(hspace=0.6)

    def _show_widget_native(self, blocking:bool):
        #plt.ion()
        #plt.show()
        return plt.show(block=blocking)

    def _show_widget_notebook(self):
        # no need to return anything because %matplotlib notebook will 
        # detect spawning of figure and paint it
        # if self.figure is returned then you will see two of them
        return None
        #plt.show()
        #return self.figure

    def _can_update_stream_plots(self):
        return False # we run interval timer which will flush the key

    @abstractmethod
    def init_stream_plot(self, stream_plot, **stream_plot_args):
        """(for derived class) Create new plot info for this stream"""
        pass
