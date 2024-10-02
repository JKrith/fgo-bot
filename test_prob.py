import logging
from fgobot import device
from pathlib import Path
logging.basicConfig(level=logging.DEBUG)

# 被测文件 逐个
quest = 'artsAlcas.png'
user_imgs = dict()
user_imgs[quest[0:-4]] = Path(quest).absolute()

a = device.Device()
if not a.connected():
    a.connect('127.0.0.1:16384')

a.load_image(im= user_imgs[quest[0:-4]], name= quest[0:-4] )
a.update_screen()
a.exists(quest[0:-4])