import logging
from fgobot import device
from pathlib import Path
logging.basicConfig(level=logging.DEBUG)
quest = 'qp.png'
user_imgs = dict()
user_imgs['quest'] = Path(quest).absolute()
a = device.Device()
if not a.connected():
    a.connect('127.0.0.1:16384')

a.update_screen()
a.exists('turn_count')