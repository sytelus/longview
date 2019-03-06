import matplotlib.pyplot as plt
from PIL import Image
from torchvision import transforms
import numpy as np
import math

def show_image(img):
    if hasattr(img, 'shape'):
        if len(img.shape) == 1:
            h = int(math.sqrt(img.shape[0]))
            img = np.reshape(img, (h, int(img.shape[0] / h)))
    plt.imshow(img)

def open_image(path, resize=None, resample=Image.ANTIALIAS):
    img = Image.open(path)
    if resize is not None:
        img = img.resize(resize, Image.ANTIALIAS)
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
