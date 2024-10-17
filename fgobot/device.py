"""
Android device interaction.
"""
import subprocess
import logging
import re
import cv2 as cv
import numpy as np
from pathlib import Path
from random import randint
from typing import List, Tuple, Union
from time import sleep
from matplotlib import pyplot as plt

# the template matching method
TM_METHOD = cv.TM_CCOEFF_NORMED
FROM_SHELL = 0
SDCARD_PULL= 1    

class Device:
    """
    A class of the android device controller that provides interface such as screenshots and clicking.
    
    In this class:

    `tap` stand for 'click'.
    `rand` stand for 'random'.
    `pos` stand for 'position'
    """

    def __init__(self, timeout: int = 15, 
                 adb_path: str = 'adb', 
                 threshold: float = 0.85, 
                 load_imgs: dict = dict(), 
                 capture_method: int = FROM_SHELL,
                 port: str = '127.0.0.1:16384',
                 ):
        """

        :param timeout: the timeout of executing commands.

        :param adb_path: the path to the adb executable.

        :param threshold: the default threshold of matching.

        :param load_imgs: use's images need to be loaded, such as "quest" and "friend"

        :param capture_method:  Options are `FROM_SHELL` or `SDCARD_PULL`, which \
            decides the way to capture screen is `from adb shell` or `from sd-card`
        
        :param port: the connect port of device
        """

        self.logger = logging.getLogger('device')

        self.adb_path = adb_path

        self.timeout = timeout

        # record user's screen size
        self.screen_size = (1280, 720)

        # whether enable zoom
        self.zoom_switch = False
        self.zoom_factor = (1, 1)

        if not self.connected():
            # If no connection, try to connect through local port
            self.connect(port)
        
        self.get_screen_size()

        self.threshold = threshold

        # Load images in the path ' ./fgobot/images/ '
        self.images = {}
        self.load_images()

        # Template matcher, set the method to capture screen
        self.method = capture_method
        self.screen = None

        # Load images provided by user
        for n, p in load_imgs.items():
            self.load_image(name = n, im = p)

    def __run_cmd(self, cmd: List[str], raw: bool = False) -> Union[bytes, List[str]]:
        """
        Execute an adb command.
        Return the raw output if the `raw` parameter is set `True`.
        Else return the utf-8 encoded output, separated by line, as a list.

        :param cmd: the command to execute, separated as a string list.
        :param raw: whether to return the raw output
        :return: a list of the output, utf-8 decoded, separated by line, as a list.
        """
        cmd = [self.adb_path] + cmd
        self.logger.debug('Executing command: {}'.format(' '.join(cmd)))
        output = subprocess.check_output(cmd, timeout=self.timeout)
        if raw:
            return output
        else:
            return output.decode('utf-8').splitlines()

    def connect(self, addr: str = '127.0.0.1:62001', restart: bool = False) -> bool:
        """
        Connect to a device through adb.

        Attention: Only if connecting via tcp/ip this function needs to be called.
        Not needed if using USB or some emulator provided adb versions.

        :param addr: the ip address and port of the adb server.
        :param restart: if set True, run kill-server before connecting.
        :return: whether connection is successful.
        """
        if restart:
            self.__run_cmd(['kill-server'])
        output = self.__run_cmd(['connect', addr])
        for line in output:
            if line.startswith('connected'):
                self.logger.info('Connected to device at {}.'.format(addr))
                return True
        self.logger.error('Failed to connect to device at {}.'.format(addr))
        self.logger.error('Error message: {}'.format('\n'.join(output)))
        return False

    def connected(self) -> bool:
        """
        Check if a device is connected.
        """
        output = self.__run_cmd(['devices'])
        devices = 0
        for line in output:
            if line.endswith('device'):
                devices += 1
        if devices == 0:
            self.logger.error('No device connected.')
            return False
        elif devices > 1:
            self.logger.error('More than one device connected.')
            return False
        else:
            self.logger.info('OK device connected.')
            return True

    def screen_adapter(self, src):
        """
        resize screen.
        """
        if self.zoom_switch:
            self.logger.debug('Screen resized')
            src = cv.resize(src, (1280, 720))
        return src
    
    def tap_adapter(self, pos: tuple[int, int]) -> tuple[int, int]:
        """
        zoom the position of tap or swipe, return new position
        """
        if self.zoom_switch:
            x_float = pos[0]*self.zoom_factor[0]
            y_float = pos[1]*self.zoom_factor[1]
            npos = (int(x_float), int(y_float))
            self.logger.debug('position zoomed')
            return npos
        else:
            return pos
    
    def load_image(self, im: Path, name=''):
        """
        Load an image (in png format). May override default images.

        :param im: path to the image.
        :param name: specify the name of the image in the dict. If not given, use the filename as default.
        """
        assert im.is_file(), "cannot find your .png file"
        assert im.name.endswith('.png'),"quest is not a png"
        name = name or im.name[:-4]
        self.images[name] = cv.imread(str(im), cv.IMREAD_COLOR)
        # self.images[name] = cv.cvtColor(self.images[name], cv.COLOR_BGR2RGB)
        # plt.figure(name)
        # plt.imshow(self.images[name])
        # plt.show()
        self.logger.debug('Loaded image {}'.format(name))

    def load_images(self):
        """
        Load template images from directory.
        """
        im_dir = Path(__file__).absolute().parent / 'images'
        for im in im_dir.glob('*.png'):
            self.load_image(im)

        self.logger.info('Images loaded successfully.')

    def get_image_size(self, im: str) -> Tuple[int, int]:
        """
        Return the size of given image.

        :param im: the name of image
        :return: the size in (width, height)
        """
        h, w, _ = self.images[im].shape
        return w, h

    def get_screen_size(self) -> bool:
        """
        Get the resolution (screen size) of the device.

        :return: whether successful.
        """
        output = self.__run_cmd(['shell', 'wm', 'size'])
        for line in output:
            if line.startswith('Physical size'):
                y, x = map(int, re.findall(r'\d+', line))
                self.screen_size = (x, y)
                self.logger.info('Got screen size {:d} x {:d}'.format(self.screen_size[0], self.screen_size[1]))
                if self.screen_size != (1280, 720):
                    x_zoom = self.screen_size[0] / 1280
                    y_zoom = self.screen_size[1] / 720
                    self.zoom_switch = True
                    self.zoom_factor = (x_zoom, y_zoom)
                return True
            
        self.logger.error('Failed to get screen size')
        self.logger.error('Error message: {}'.format('\n'.join(output)))
        return False

    def tap(self, x: int = 590, y: int = 230) -> bool:
        """
        Input a tap event at `pos:(x, y)`.
        
        :param x: the x coord in pixels.
        :param y: the y coord in pixels.
        :return: whether the event is successful.
        """
        (x, y) = self.tap_adapter(pos=(x, y))
        coords = '{:d} {:d}'.format(x, y)
        output = self.__run_cmd(['shell', 'input tap {}'.format(coords)])
        for line in output:
            if line.startswith('error'):
                self.logger.error('Failed to tap at {}'.format(coords))
                self.logger.error('Error message: {}'.format('\n'.join(output)))
                return False
        self.logger.debug('Tapped at {}'.format(coords))
        return True

    def tap_rand(self, x: int, y: int, w: int, h: int) -> bool:
        """
         Input a tap event at `random pos` in rectangular area:
        `(x, y)` and `(x+w, y+h)`
        
        :param x: the top x coord in pixels.
        :param y: the left y coord in pixels.
        :param w: the width in pixels.
        :param h: the height in pixels.
        :return: whether the event is successful.
        """
        x = randint(x, x + w - 1)
        y = randint(y, y + h - 1)
        return self.tap(x, y)

    def swipe(self, pos0: Tuple[int, int], pos1: Tuple[int, int], duration: int = 1000) -> bool:
        """
        Input a swipe event from `pos0` to `pos1`, taking `duration` milliseconds.

        :param pos0: the start coordinates in pixels.
        :param pos1: the end coordinates in pixels.
        :param duration: the time (in milliseconds) the swipe will take.
        :return: whether the event is successful.
        """
        newpos = map(self.tap_adapter, [pos0, pos1])
        npos0, npos1 = list(newpos)
        coords0 = '{:d} {:d}'.format(npos0[0], npos0[1])
        coords1 = '{:d} {:d}'.format(npos1[0], npos1[1])
        output = self.__run_cmd(['shell', 'input swipe {} {} {:d}'.format(coords0, coords1, duration)])
        for line in output:
            if line.startswith('error'):
                self.logger.error('Failed to swipe from {} to {} taking {:d}ms'.format(coords0, coords1, duration))
                self.logger.error('Error message: {}'.format('\n'.join(output)))
                return False
        self.logger.debug('Swiped from {} to {} taking {:d}ms'.format(coords0, coords1, duration))
        return True
    
    @staticmethod
    def __png_sanitize(s: bytes) -> bytes:
        """
        Auto-detect and replace '\r\n' or '\r\r\n' by '\n' in the given byte string.

        :param s: the string to sanitize
        :return: the result string
        """
        logging.getLogger('device').debug('Sanitizing png bytes...')
        pos1 = s.find(b'\x1a')
        pos2 = s.find(b'\n', pos1)
        pattern = s[pos1 + 1:pos2 + 1]
        logging.getLogger('device').debug("Pattern detected: '{}'".format(pattern))
        return re.sub(pattern, b'\n', s)

    def __capture(self, method: int) -> Union[np.ndarray, None]:
        """
        Capture the screen.

        :param method: 'FROM_SHELL' or 'SDCARD_PULL'

        :return: a cv2 image as numpy ndarray
        """
        if method == FROM_SHELL:
            self.logger.debug('Capturing screen from shell...')
            img = self.__run_cmd(['shell', 'screencap -p'], raw=True)
            img = self.__png_sanitize(img)
            img = np.frombuffer(img, np.uint8)
            img = cv.imdecode(img, cv.IMREAD_COLOR)
            return img
        elif method == SDCARD_PULL:
            self.logger.debug('Capturing screen from sdcard pull...')
            self.__run_cmd(['shell', 'screen -p /sdcard/sc.png'])
            self.__run_cmd(['pull', '/sdcard/sc.png', './sc.png'])
            img = cv.imread('./sc.png', cv.IMREAD_COLOR)
            return img
        else:
            self.logger.error('Unsupported screen capturing method.')
            return None

    def update_screen(self):
        """
        Update the screencap image and resize screencap to 1280x720. 
        """
        self.screen = self.__capture(method= self.method)
        self.screen = self.screen_adapter(self.screen)
        self.logger.debug('Screen captured.')
    
    def match(self, img:str):
        """
        Match `img` with screen.
        
        :param img: the name of img
        :param threshold: the threshold of matching. If not given, will be set to the default threshold

        :return: match-value and match-location.
        
                match-location is a tuple(int, int)
        """
        try:
            template = self.images[img]
        except KeyError:
            self.logger.error('Unexpected image name {}'.format(img))
            return 0, (-1, -1)
        
        res = cv.matchTemplate(self.screen, template, TM_METHOD)
        _, max_val, _, max_loc = cv.minMaxLoc(res)
        self.logger.debug(f'image:{img}, max_val = {max_val}, max_loc = {max_loc}')
        
        return max_val, max_loc
    
    def updateScreen_and_exists(self, im: str, threshold: float = None) -> bool:
        """
        Capture screen, Check if a given image exists on screen.

        :param im: the name of the image
        :param threshold: threshold of matching, If not given, will be set to the default threshold
        """
        self.update_screen()
        return self.exists(im, threshold)
    
    def exists(self, im: str, threshold: float = None) -> bool:
        """
        Check if a given image exists on screen.

        :param im: the name of the image
        :param threshold: threshold of matching, If not given, will be set to the default threshold
        """
        threshold = threshold or self.threshold
        self.logger.debug("Whether {} exists".format(im))
        prob, _ = self.match(img= im)
        if prob >= threshold:
            return True
        else:
            return False
    
    def wait(self, sec: int = 1):
        """
        Wait some seconds 

        :param sec: the seconds to wait
        """
        self.logger.debug('Sleep {} seconds.'.format(sec))
        sleep(sec)

    def wait_and_updateScreen(self, sec:int = 1):
        """
        Wait some seconds, then Capture screen

        :param sec: the seconds to wait
        """
        self.logger.debug('Sleep {} seconds.'.format(sec))
        sleep(sec)
        self.update_screen()
    
    def wait_until(self, im: str, sec: int=1, threshold: float = None, countLimit: int = None) -> bool:
        """
        Wait and Update screen until the given image appears. 
        
        Useful when try to use skills, etc.
        
        :param im: the name of image
        :param sec: the seconds to wait
        :param threshold: threshold of matching, If not given, will be set to the default threshold

        :return: True after the im appears.
        """
        self.logger.debug("Wait until image '{}' appears.".format(im))
        threshold = self.threshold or threshold
        if countLimit is None:
            while not self.updateScreen_and_exists(im, threshold):
                self.wait(sec)
            else:
                return True
        else:
            while countLimit:
                if self.updateScreen_and_exists(im, threshold):
                    return True
                self.wait(sec)
                countLimit = countLimit - 1
            else:
                return False
    def wait_until_tap(self, im: str, sec: int=1, threshold: float = None) -> bool:
        """
        Wait, Update screen until the given image appears and Tap.

        :param im: the name of image
        :param sec: the seconds to wait
        :param threshold: threshold of matching, If not given, will be set to the default threshold

        :return: True after the click event is successful.
        """
        self.logger.debug("Wait until image '{}' appears.".format(im))
        prob = 0
        x, y = 0, 0
        threshold = threshold or self.threshold
        while prob < threshold :
            self.update_screen()
            prob, pos = self.match(img= im)
            self.wait(sec)
        else:
            x = pos[0]
            y = pos[1]
            return self.tap(x, y)

    def probability(self, im:str) -> float:
        """
        Return the probability of the existence of given image.

        :param im: the name of the image.
        :return: the probability (confidence).
        """
        max_val, _ = self.match(img= im)
        return max_val
    
    def tap_and_wait(self, x: int, y: int, sec: int = 1):
        """
        Input a tap event at `pos:(x, y)`, then wait for `sec` second.
        """
        success = self.tap(x, y)
        self.wait(sec)
        return success
    
    def find_and_tap(self, im: str, threshold: float = None, withPosition: bool = False) -> bool:
        """
        Find the given image on screencap, Tap on screen if found.

        :param im: the name of image
        :param threshold: the matching threshold, If not given, will be set to the default threshold.
        :return: if `im` found, Tap it and Return `True`,

                    else Don't tap and Return `False`  
        """
        threshold = threshold or self.threshold
        prob, (x, y) = self.match(img= im)
        if prob < threshold:
            self.logger.warning('Failed to find image {} on screen.'.format(im))
            if withPosition:
                return False, (-1, -1)
            else:
                return False
        
        w, h = self.get_image_size(im)
        self.logger.debug('find and tap image {}'.format(im))
        if withPosition:
            return self.tap_rand(x, y, w, h), (x, y)
        else:
            return self.tap_rand(x, y, w, h)

