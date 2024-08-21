"""
Android device interaction.
"""

import subprocess
import logging
import re
import cv2 as cv
from .tm import TM
import numpy as np
from pathlib import Path
from random import randint
from typing import List, Tuple, Union
from time import sleep

class Device:
    """
    A class of the android device controller that provides interface such as screenshots and clicking.
    """

    def __init__(self, timeout: int = 15, adb_path: str = 'adb',\
                  load_imgs: dict = None):
        """

        :param timeout: the timeout of executing commands.
        :param adb_path: the path to the adb executable.
        """

        self.logger = logging.getLogger('device')

        self.adb_path = adb_path

        self.timeout = timeout

        self.size = (1280, 720)

        # Template matcher
        self.tm = TM(method= TM.FROM_SHELL)

        for n, p in load_imgs.items():
            self.tm.load_image(name = n, im = p)

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

    def get_size(self) -> bool:
        """
        Get the resolution (screen size) of the device.

        :return: whether successful.
        """
        output = self.__run_cmd(['shell', 'wm', 'size'])
        for line in output:
            if line.startswith('Physical size'):
                self.size = tuple(map(int, re.findall(r'\d+', line)))
                self.logger.info('Got screen size {:d} x {:d}'.format(self.size[0], self.size[1]))
                return True
        self.logger.error('Failed to get screen size')
        self.logger.error('Error message: {}'.format('\n'.join(output)))
        return False

    def tap(self, x: int = 590, y: int = 230) -> bool:
        """
        Input a tap event at `pos`.

        :param x: the x coord in pixels.
        :param y: the y coord in pixels.
        :return: whether the event is successful.
        """
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

        :param x: the top x coord in pixels.
        :param y: the left y coord in pixels.
        :param w: the width in pixels.
        :param h: the height in pixels.
        :return: whether the event is successful.
        """
        x = randint(x, x + w - 1)
        y = randint(y, y + h - 1)
        return self.tap(x, y)

    def swipe(self, pos0: Tuple[int, int], pos1: Tuple[int, int], duration: int = 500) -> bool:
        """
        Input a swipe event from `pos0` to `pos1`, taking `duration` milliseconds.

        :param pos0: the start coordinates in pixels.
        :param pos1: the end coordinates in pixels.
        :param duration: the time (in milliseconds) the swipe will take.
        :return: whether the event is successful.
        """
        coords0 = '{:d} {:d}'.format(pos0[0], pos0[1])
        coords1 = '{:d} {:d}'.format(pos1[0], pos1[1])
        output = self.__run_cmd(['shell', 'input swipe {} {} {:d}'.format(coords0, coords1, duration)])
        for line in output:
            if line.startswith('error'):
                self.logger.error('Failed to swipe from {} to {} taking {:d}ms'.format(coords0, coords1, duration))
                self.logger.error('Error message: {}'.format('\n'.join(output)))
                return False
        self.logger.debug('Swiped from {} to {} taking {:d}ms'.format(coords0, coords1, duration))
        return True
    
    def exists(self, im: str, threshold: float = None) -> bool:
        """
        Check if a given image exists on screen.

        :param im: the name of the image
        :param threshold: threshold of matching
        """
        self.logger.debug("Whether {} exists".format(im))
        return self.tm.exists(im, threshold=threshold)
    
    def wait(self, sec: int = 1):
        """
        Wait some seconds and update the screen feed.

        :param sec: the seconds to wait
        """
        self.logger.debug('Sleep {} seconds.'.format(sec))
        sleep(sec)
    
    def wait_until(self, im: str, val: int=1) -> bool:
        """
        Wait until the given image appears. Useful when try to use skills, etc.
        """
        self.logger.debug("Wait until image '{}' appears.".format(im))
        
        while not self.exists(im):
            self.wait(val)
        else:
            return True

    def probability(self, im:str) -> float: 
        """
        Return the probability of the existence of given image.

        :param im: the name of the image.
        :return: the probability (confidence).
        """
        return self.tm.probability(im)
    
    def find_and_tap(self, im: str, threshold: float = None) -> bool:
        """
        Find the given image on screen and tap.

        :param im: the name of image
        :param threshold: the matching threshold
        :return: whether successful
        """
        x, y = self.tm.find(im, threshold)
        if (x, y) == (-1, -1):
            self.logger.warning('Failed to find image {} on screen.'.format(im))
            return False
        w, h = self.tm.getsize(im)
        return self.tap_rand(x, y, w, h)

