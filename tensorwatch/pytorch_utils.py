from torchvision import models, transforms
import torch
from . import utils

def get_model(model_name):
    model = models.__dict__[model_name](pretrained=True)
    return model

def tensors2batch(tensors, preprocess_transform=None):
    if preprocess_transform:
        tensors = tuple(preprocess_transform(i) for i in tensors)
    if not utils.is_array_like(tensors):
        tensors = tuple(tensors)
    return torch.stack(tensors, dim=0)

def int2tensor(val):
    return torch.LongTensor([val])

def image_class2tensor(image_path, class_index=None, image_convert_mode=None, 
                       image_transform=None):
    raw_input = img_utils.open_image(image_path, convert_mode=image_convert_mode)
    if image_transform:
        input = image_transform(raw_input)
    else:
        input = transforms.ToTensor()(raw_input)
    input = input.unsqueeze() #convert to batch of 1
    target_class = int2tensor(class_index) if class_index is not None else None
    return raw_input, input, target_class
