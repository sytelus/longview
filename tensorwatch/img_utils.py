import matplotlib.pyplot as plt
from PIL import Image
from torchvision import transforms
import numpy as np
import math

def show_image(img, size=None):
    if size is not None or (hasattr(img, 'shape') and len(img.shape) == 1):
        if size is None:
            # make guess for 1-dim tensors
            h = int(math.sqrt(img.shape[0]))
            w = int(img.shape[0] / h)
            size = h,w
        img = np.reshape(img, size)
    plt.imshow(img)

# convert_mode param is mode: https://pillow.readthedocs.io/en/5.1.x/handbook/concepts.html#modes
# use 'RGB' to force 3 channels
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
