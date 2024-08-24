"""
Template matching.
"""

from typing import Callable, Union, Tuple
from pathlib import Path
import subprocess
import cv2 as cv
import re
import numpy as np
import logging
from matplotlib import pyplot as plt

logger = logging.getLogger('tm')

# the template matching method
TM_METHOD = cv.TM_CCOEFF_NORMED


class TM:
    def __init__(self, method:str = 'FROM_SHELL',\
                 adb_path: str = 'adb', timeout: int = 15, threshold: float = 0.85):
        """
        :param timeout: the timeout of executing commands.
        :param adb_path: the path to the adb executable.
        :param threshold: the default threshold of matching.
        :param method: methods of capturing the screen
        """

        self.threshold = threshold
        self.adb_path = adb_path
        self.timeout = timeout
        # template image set
        self.images = {}
        self.load_images()    

        # the screencap image. Needs to be updated before matching.
        self.method = method
        self.screen = None

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
        logger.debug('Loaded image {}'.format(name))

    def load_images(self):
        """
        Load template images from directory.
        """
        im_dir = Path(__file__).absolute().parent / 'images'
        for im in im_dir.glob('*.png'):
            self.load_image(im)

        logger.info('Images loaded successfully.')

    def getsize(self, im: str) -> Tuple[int, int]:
        """
        Return the size of given image.

        :param im: the name of image
        :return: the size in (width, height)
        """
        h, w, _ = self.images[im].shape
        return w, h

    def capture_screen(self):
        """
        Capture the screen image.
        """
        self.screen = self.capture(method= self.method)
        logger.debug('Screen captured.')

    PROBMODE = 0
    EXSTMODE = 1
    FINDMODE = 2
    ALLMODE  = 3
    def capture_and_match(self, img:str, threshold: float = None, mode: int = PROBMODE,\
                          doCapture: bool = True):
        """
        Capture the screen, match `img` with screen.
        
        :param img: the name of img
        :param threshold: the threshold of matching. If not given, will be set to the default threshold
        :param mode: select `PROBMODE` to return `match-value`, 
                    `FINDMODE` to return `match-location`,      
                    `EXSTMODE` to check if img exists, 
                    `ALLMODE` to return `match-value`, `match-location`
        :param doCapture: Whether Capture the screen before Match
        :return: match-value or match-location or whether exists
        """
        threshold = threshold or self.threshold
        if doCapture:
            self.capture_screen()
        try:
            template = self.images[img]
        except KeyError:
            logger.error('Unexpected image name {}'.format(img))
            if mode == self.PROBMODE :
                return 0
            elif mode == self.EXSTMODE:
                return None
            elif mode == self.FINDMODE:
                return -1, -1
            elif mode == self.ALLMODE:
                return 0, -1, -1
        
        res = cv.matchTemplate(self.screen, template, TM_METHOD)
        _, max_val, _, max_loc = cv.minMaxLoc(res)
        logger.debug('max_val = {}, max_loc = {}'.format(max_val, max_loc))
        
        if mode == self.PROBMODE:
            return max_val
        elif mode == self.EXSTMODE:
            return True if max_val >= threshold else False
        elif mode == self.FINDMODE:
            return max_loc if max_val >= threshold else (-1, -1)
        elif mode == self.ALLMODE:
            return max_val, max_loc
    
    def capture_and_probability(self, im: str) -> float:
        """
        Capture screen, Return the probability of the existence of given image.

        :param im: the name of the image.
        :return: the probability (confidence).
        """
        return self.capture_and_match(img= im, mode= self.PROBMODE)
    
    def capture_and_find(self, im: str, threshold: float) -> Tuple[int, int]:
        """
        Capture screen, Find the template image on screen and return its top-left coords.

        Return None if the matching value is less than `threshold`.

        :param im: the name of the image
        :param threshold: the threshold of matching. If not given, will be set to the default threshold.
        :return: the top-left coords of the result. Return (-1, -1) if not found.
        """
        threshold = threshold or self.threshold
        return self.capture_and_match(img= im, threshold= threshold, mode= self.FINDMODE)

    def capture_and_exists(self, im: str, threshold: float) -> bool:
        """
        Capture screen, Check if a given image exists on screen.

        :param im: the name of the image
        :param threshold: the threshold of matching. If not given, will be set to the default threshold.
        """
        threshold = threshold or self.threshold
        logger.debug("Whether {} exists".format(im))
        return self.capture_and_match(img= im, mode= self.EXSTMODE, threshold= threshold)
    
    def __run_cmd(self, cmd: list[str], raw: bool = False) -> Union[bytes, list[str]]:
        """
        Execute an adb command.
        Return the raw output if the `raw` parameter is set `True`.
        Else return the utf-8 encoded output, separated by line, as a list.

        :param cmd: the command to execute, separated as a string list.
        :param raw: whether to return the raw output
        :return: a list of the output, utf-8 decoded, separated by line, as a list.
        """
        cmd = [self.adb_path] + cmd
        logger.debug('Executing command: {}'.format(' '.join(cmd)))
        output = subprocess.check_output(cmd, timeout=self.timeout)
        if raw:
            return output
        else:
            return output.decode('utf-8').splitlines()
        
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

    def capture(self, method='FROM_SHELL') -> Union[np.ndarray, None]:
        """
        Capture the screen.

        :param method: 'FROM_SHELL' or 'SDCARD_PULL'

        :return: a cv2 image as numpy ndarray
        """
        if method == 'FROM_SHELL':
            logger.debug('Capturing screen from shell...')
            img = self.__run_cmd(['shell', 'screencap -p'], raw=True)
            img = self.__png_sanitize(img)
            img = np.frombuffer(img, np.uint8)
            img = cv.imdecode(img, cv.IMREAD_COLOR)
            return img
        elif method == 'SDCARD_PULL':
            logger.debug('Capturing screen from sdcard pull...')
            self.__run_cmd(['shell', 'screen -p /sdcard/sc.png'])
            self.__run_cmd(['pull', '/sdcard/sc.png', './sc.png'])
            img = cv.imread('./sc.png', cv.IMREAD_COLOR)
            return img
        else:
            logger.error('Unsupported screen capturing method.')
            return None