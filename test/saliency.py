from tensorwatch.saliency import saliency
from tensorwatch import img_utils, imagenet_utils, pytorch_utils

print('ee')
model = pytorch_utils.get_model('vgg16')
raw_input, input, target_class = pytorch_utils.image_class2tensor('../data/images/elephant.png',
    image_transform=imagenet_utils.get_image_transform())
sal = saliency.get_saliency(model, input, target_class)
saliency.show_image_saliency(raw_input, sal)





