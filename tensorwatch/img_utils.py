import matplotlib.pyplot as plt
from PIL import Image
from torchvision import transforms
import numpy as np
import math
import time

def _resize_image(img, size=None):
    if size is not None or (hasattr(img, 'shape') and len(img.shape) == 1):
        if size is None:
            # make guess for 1-dim tensors
            h = int(math.sqrt(img.shape[0]))
            w = int(img.shape[0] / h)
            size = h,w
        img = np.reshape(img, size)
    return img

def show_image(img, size=None, alpha=None, cmap=None, 
               img2=None, size2=None, alpha2=None, cmap2=None, ax=None):
    img =_resize_image(img, size)
    img2 =_resize_image(img2, size2)

    (ax or plt).imshow(img, alpha=alpha, cmap=cmap)

    if img2 is not None:
        (ax or plt).imshow(img2, alpha=alpha2, cmap=cmap2)

    return ax or plt.show()

# convert_mode param is mode: https://pillow.readthedocs.io/en/5.1.x/handbook/concepts.html#modes
# use convert_mode='RGB' to force 3 channels
def open_image(path, resize=None, resample=Image.ANTIALIAS, convert_mode=None):
    img = Image.open(path)
    if resize is not None:
        img = img.resize(resize, Image.ANTIALIAS)
    if convert_mode is not None:
        img = img.convert(convert_mode)
    return img

def img2pyt(img, add_batch_dim=True, resize=None):
    ts = []
    if resize is not None:
        ts.append(transforms.RandomResizedCrop(resize))
    ts.append(transforms.ToTensor())
    img_pyt = transforms.Compose(ts)(img)
    if add_batch_dim:
        img_pyt.unsqueeze_(0)
    return img_pyt

def linear_to_2d(img, size=None):
    if size is not None or (hasattr(img, 'shape') and len(img.shape) == 1):
        if size is None:
            # make guess for 1-dim tensors
            h = int(math.sqrt(img.shape[0]))
            w = int(img.shape[0] / h)
            size = h,w
        img = np.reshape(img, size)
    return img

def stack_images(imgs):
    return np.hstack(imgs)

def plt_loop(sleep_time=1, plt_pause=0.01):
    plt.ion()
    plt.show(block=False)
    while(True):
        #plt.draw()
        plt.pause(plt_pause)
        time.sleep(sleep_time)