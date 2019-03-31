from torchvision import transforms
from . import img_utils

def get_image_transform():
    transf = transforms.Compose([
        get_resize_transform(),
        transforms.ToTensor(),
        get_normalize_transform()
    ])    

    return transf

def get_resize_transform(): 
    return transforms.Resize((224, 224))

def get_normalize_transform():
    return transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                    std=[0.229, 0.224, 0.225])   
