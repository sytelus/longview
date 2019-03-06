import torch
import torchvision.models
import longview as lv

vgg16_model = torchvision.models.vgg16()

drawing = lv.draw_model(vgg16_model, [1, 3, 224, 224])

input("Press any key")