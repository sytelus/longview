import tensorwatch as tw
import numpy as np
import matplotlib.pyplot as plt
import time

from dlc_lib import DlcDataset
ds = DlcDataset(linearize=False, data_root='D:\\datasets\\dlc\\current')

img_plot_data = [tw.ImagePlotItem((ds[i][0], ds[i][1]), title=str(i)) for i in range(5)]

img_plot = tw.open(img_plot_data, type='image', rows=2, cols=5, viz_img_scale=3)
img_plot.show()

tw.image_utils.plt_loop()