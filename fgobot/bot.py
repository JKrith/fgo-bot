"""
Game auto-playing bot.
"""

import logging

from functools import partial
from typing import Dict, Any, Callable
from .tm import TM
from .device import Device
import json
from pathlib import Path
from time import sleep
from typing import Tuple, List, Union
from random import randint

logger = logging.getLogger('bot')

#time for waitting between operations
INTERVAL_SHORT = 1
INTERVAL_MID = 4
INTERVAL_LONG = 15


class BattleBot:
    """
    A class of the bot that automatically play battles.
    """

    def __init__(self,
                 quest: str = 'quest.png',
                 friend_class: str = 'caster',
                 friend: Union[str, List[str]] = 'friend.png',
                 stage_count = 3,
                 ap: List[str] = None,
                 quest_threshold: float = 0.97,
                 friend_threshold: float = 0.97
                 ):
        """

        :param quest: path to image of the quest to play
        :param friend: path to image(s) of the preferred friend servant
        :param stage_count: the number of states in a battle
        :param ap: the preferred AP regeneration item.
                   Options are 'silver_apple', 'gold_apple', 'quartz'.
                   i.e. ['silver_apple', 'gold_apple'] means: to use silver apple first
                   and to use gold apple if silver ones run out.
                   If not given, the bot will stop when AP runs out.
        :param quest_threshold: threshold of quest matching
        :param friend_threshold: threshold of friend matching
        """

        # A dict of the handler functions that are called repeatedly at each stage.
        # Use `at_stage` to register functions.
        self.stage_handlers = {}

        # A dict of configurations.
        self.config = {}

        self.stage_count = stage_count
        logger.info('Stage count set to {}.'.format(self.stage_count))

        # Device
        self.device = Device()

        # Template matcher
        self.tm = TM(feed=partial(self.device.capture, method=Device.FROM_SHELL))

        # Target quest
        path = Path(quest).absolute()
        self.tm.load_image(path, name='quest')

        self.friend_class = friend_class

        if isinstance(friend, str):
            friend = [friend]

        # Count of expected friend servants
        self.friend_count = len(friend)
        logger.info('Friend count is {}.'.format(self.friend_count))

        for fid in range(self.friend_count):
            path = Path(friend[fid]).absolute()
            self.tm.load_image(path, name='f_{}'.format(fid))

        # AP strategy
        self.ap = ap
        logger.info('AP strategy is {}.'.format(self.ap))

        self.quest_threshold = quest_threshold
        self.friend_threshold = friend_threshold

        # Load button coords from config
        btn_path = Path(__file__).absolute().parent / 'config' / 'buttons.json'
        with open(btn_path) as f:
            self.buttons = json.load(f)

        logger.debug('Bot initialized.')

    def __add_stage_handler(self, stage: int, f: Callable):
        """
        Register a handler function to a given stage of the battle.

        :param stage: the stage number
        :param f: the handler function
        """
        assert not self.stage_handlers.get(stage), 'Cannot register multiple function to a single stage.'
        logger.debug('Function {} registered to stage {}'.format(f.__name__, stage))
        self.stage_handlers[stage] = f

    def __button(self, btn):
        """
        Return the __button coords and size.

        :param btn: the name of __button
        :return: (x, y, w, h)
        """
        btn = self.buttons[btn]
        return btn['x'], btn['y'], btn['w'], btn['h']

    def __swipe(self, track):
        """
        Swipe in given track.

        :param track:
        :return:
        """
        x1, y1, x2, y2 = map(lambda x: x, self.buttons['swipe'][track])
        self.device.swipe((x1, y1), (x2, y2))

    def __find_and_tap(self, im: str, threshold: float = None) -> bool:
        """
        Find the given image on screen and tap.

        :param im: the name of image
        :param threshold: the matching threshold
        :return: whether successful
        """
        x, y = self.tm.find(im, threshold=threshold)
        if (x, y) == (-1, -1):
            logger.warning('Failed to find image {} on screen.'.format(im))
            return False
        w, h = self.tm.getsize(im)
        return self.device.tap_rand(x, y, w, h)

    def __exists(self, im: str, threshold: float = None) -> bool:
        """
        Check if a given image exists on screen.

        :param im: the name of the image
        :param threshold: threshold of matching
        """
        return self.tm.exists(im, threshold=threshold)

    def __wait(self, sec):
        """
        Wait some seconds and update the screen feed.

        :param sec: the seconds to wait
        """
        logger.debug('Sleep {} seconds.'.format(sec))
        sleep(sec)
        self.tm.update_screen()

    def __wait_until(self, im: str) -> bool:
        """
        Wait until the given image appears. Useful when try to use skills, etc.
        """
        logger.debug("Wait until image '{}' appears.".format(im))
        self.tm.update_screen()
        while not self.__exists(im):
            self.__wait(INTERVAL_MID)
        else:
            return True

    def __get_current_stage(self) -> int:
        """
        Get the current stage in battle.

        :return: current stage. Return -1 if error occurs.
        """
        
        max_prob, max_stage = 0.70, -1
        for stage in range(1, self.stage_count + 1):
            im = '{}_{}'.format(stage, self.stage_count)
            prob = self.tm.probability(im)
            if prob > max_prob:
                max_prob, max_stage = prob, stage

        if max_stage == -1:
            logger.error('Failed to get current stage.')
        else:
            logger.debug('Got current stage: {}'.format(max_stage))

        return max_stage
    
    def __select_class(self, friend_class: str):
        """
        Select friend's class

        :return: None
        """
        #class index in support list, for calculating the (x,y) of support class
        spt_cls_index = {
            "all":      0,
            "saber":    1,
            "archer":   2,
            "lancer":   3,
            "rider":    4,
            "caster":   5,
            "assassin": 6,
            "berserker":7,
            "extra":    8
        }
        x, y, w, h = self.__button('all')
        x += self.buttons['support_class_distance'] * ( spt_cls_index[friend_class] )
        self.device.tap(x,y)
        
    
    def __select_friend(self) -> bool:
        """
        Select friend and enter team select screen 

        :Return True if enter successs
        """
        self.__wait_until("friend_pick")
        self.__select_class(self.friend_class)
        
        friend = ''
        swp_times = 0
        while not friend:
            for fid in range(self.friend_count):
                im = 'f_{}'.format(fid)
                if self.__exists(im, threshold=self.friend_threshold):
                    friend = im
                    break
            if friend:
                break
            elif swp_times >5 :
                swp_times = 0
                self.__wait_until('refresh_friends')      
                self.__find_and_tap('refresh_friends')
                self.__wait(INTERVAL_SHORT)
                self.__find_and_tap('yes')
                self.__wait(INTERVAL_SHORT * 2) 
                self.__wait_until("friend_pick")
            else:
                swp_times += 1
                self.__swipe('friend')
                self.__wait(INTERVAL_SHORT)
        
        self.__find_and_tap(friend)

        self.__wait(INTERVAL_SHORT)
        return self.__wait_until('start_quest')
    
    def __from_terminal_select_quest(self):
        """
        Select quest

        :Return: True if success

        False if fail
        """
        self.__wait_until('menu')
        while not self.__find_and_tap('quest', threshold=self.quest_threshold):
            self.__swipe('quest')
            self.__wait(INTERVAL_SHORT)
        self.__wait(INTERVAL_SHORT * 2)
        
    def __enter_battle(self) -> bool:
        """
        Enter the battle.

        :return: whether successful.
        """
        logger.info("try to select quest")
        self.__from_terminal_select_quest()
        if self.__exists('stormbottle_use'):
            self.__find_and_tap('quest_start', threshold=self.quest_threshold)
            self.__wait(INTERVAL_SHORT * 2)

        # no enough AP
        if self.__exists('ap_paper_regen'):
            logger.info("recover_ap when paper quest")
            self.__find_and_tap('recover_ap')
            self.__wait(INTERVAL_SHORT)

        if self.__exists('ap_regen'):
            logger.info("eat_apple")
            if not self.__eat_Apple():
                return False
            
        if self.__exists('stormbottle_use'):
            self.__find_and_tap('quest_start', threshold=self.quest_threshold)
            self.__wait(INTERVAL_SHORT * 2)
        
        logger.info("try to select friend")
        self.__select_friend()
        
        logger.info("select team")
        self.__find_and_tap('start_quest')
        self.__wait(INTERVAL_LONG)
        self.__wait_until('attack')
        return True
    
    def __eat_Apple(self) -> bool:
        """
        Recover AP
            :Return False if no ap strategy or fail to recover
        """
        if not self.ap:
            return False
        else:
            ok = False
            for ap_item in self.ap:
                if self.__find_and_tap(ap_item):
                    self.__wait(INTERVAL_SHORT)
                    if self.__find_and_tap('decide'):
                        ok = True
                        break
            if ok:
                return True
            else:
                return False


    def __play_battle(self) -> int:
        """
        Play the battle.

        :return: count of rounds.
        """
        rounds = 0
        while True:
            stage = self.__get_current_stage()
            if stage == -1:
                logger.error("Failed to get current stage. Quit battle...")
                return -1

            rounds += 1
            logger.info('At stage {}/{}, round {}, calling handler function...'
                        .format(stage, self.stage_count, rounds))
            self.__wait_until('attack')

            self.stage_handlers[stage]()

            while True:
                self.__wait(INTERVAL_MID)
                if self.__exists('bond') or self.__exists('bond_up'):
                    logger.info("'与从者的羁绊' detected. Leaving battle...")
                    return rounds
                elif self.__exists('attack'):
                    logger.info("'Attack' detected. Continuing loop...")
                    break

    def __end_battle(self):
        # self.__find_and_tap('bond')
        # self.__wait(INTERVAL_SHORT)
        # self.__wait_until('gain_exp')
        # self.__find_and_tap('gain_exp')
        # self.__wait(INTERVAL_SHORT)
        self.__wait(INTERVAL_SHORT * 2)
        while not self.__exists('next_step'):
            self.device.tap(590, 230)
            self.__wait(INTERVAL_SHORT)

        self.__find_and_tap('next_step')
        self.__wait(INTERVAL_SHORT * 2)

        # quest first-complete reward
        if self.__exists('please_tap'):
            self.__find_and_tap('please_tap')
            self.__wait(INTERVAL_SHORT)

        # not send friend application
        if self.__exists('not_apply'):
            self.__find_and_tap('not_apply')
        
        # exit from quest
        if self.__exists('close'):
            self.__find_and_tap('close')

        self.__wait(INTERVAL_LONG)
        self.__wait_until('menu')

    def at_stage(self, stage: int):
        """
        A decorator that is used to register a handler function to a given stage of the battle.

        :param stage: the stage number
        """

        def decorator(f):
            self.__add_stage_handler(stage, f)
            return f

        return decorator

    def use_skill(self, servant: int, skill: int, obj=None):
        """
        Use a skill.

        :param servant: the servant id.
        :param skill: the skill id.
        :param obj: the object of skill, if required.
        """
        x, y, w, h = self.__button('skill')
        x += self.buttons['servant_distance'] * (servant - 1)
        x += self.buttons['skill_distance'] * (skill - 1)
        logger.debug('Used skill ({}, {})'.format(servant, skill))
        self.device.tap(x, y)
        self.__wait(INTERVAL_SHORT)

        if self.__exists('choose_object'):
            if obj is None:
                logger.error('Must choose a skill object.')
            else:
                x, y, w, h = self.__button('choose_object')
                x += self.buttons['choose_object_distance'] * (obj - 1)
                logger.debug('Chose skill object {}.'.format(obj))
                self.device.tap(x, y)
        
        #click for high speed skill animation
        self.device.tap(590, 230)

        self.__wait(INTERVAL_SHORT)
        self.__wait_until('attack')

    def use_master_skill(self, skill: int, obj=None, obj2=None):
        """
        Use a master skill.
        Param `obj` is needed if the skill requires a object.
        Param `obj2` is needed if the skill requires another object (Order Change).

        :param skill: the skill id.
        :param obj: the object of skill, if required.
        :param obj2: the second object of skill, if required.
        """

        x, y, w, h = self.__button('master_skill_menu')
        self.device.tap(x, y)
        self.__wait(INTERVAL_SHORT)

        x, y, w, h = self.__button('master_skill')
        x += self.buttons['master_skill_distance'] * (skill - 1)
        self.device.tap(x, y)
        logger.debug('Used master skill {}'.format(skill))
        self.__wait(INTERVAL_SHORT)

        if self.__exists('choose_object'):
            if obj is None:
                logger.error('Must choose a master skill object.')
            elif 1 <= obj <= 3:
                x, y, w, h = self.__button('choose_object')
                x += self.buttons['choose_object_distance'] * (obj - 1)
                self.device.tap(x, y)
                logger.debug('Chose master skill object {}.'.format(obj))
            else:
                logger.error('Invalid master skill object.')
        elif self.__exists('change_disabled'):
            if obj is None or obj2 is None:
                logger.error('Must choose two objects for Order Change.')
            elif 1 <= obj <= 3 and 4 <= obj2 <= 6:
                x, y, w, h = self.__button('change')
                x += self.buttons['change_distance'] * (obj - 1)
                self.device.tap_rand(x, y, w, h)

                x += self.buttons['change_distance'] * (obj2 - obj)
                self.device.tap_rand(x, y, w, h)
                logger.debug('Chose master skill object ({}, {}).'.format(obj, obj2))

                self.__wait(INTERVAL_SHORT)
                self.__find_and_tap('change')
                logger.debug('Order Change')
                #click for high speed animation
                self.device.tap(590, 230)
            else:
                logger.error('Invalid master skill object.')

        self.__wait(INTERVAL_SHORT)
        self.__wait_until('attack')

    def attack(self, cards: list):
        """
        Tap attack __button and choose three cards.

        1 ~ 5 stands for normal cards, 6 ~ 8 stands for noble phantasm cards.

        :param cards: the cards id, as a list

        """
        assert len(cards) == 3, 'Number of cards must be 3.'
        assert len(set(cards)) == 3, 'Cards must be distinct.'
        self.__wait_until('attack')

        self.__find_and_tap('attack')
        self.__wait(INTERVAL_SHORT * 2)
        for card in cards:
            if 1 <= card <= 5:
                x, y, w, h = self.__button('card')
                x += self.buttons['normal_card_distance'] * (card - 1)
                self.device.tap_rand(x, y, w, h)
            elif 6 <= card <= 8:
                x, y, w, h = self.__button('noble_card')
                x += self.buttons['noble_card_distance'] * (card - 6)
                self.device.tap_rand(x, y, w, h)
            else:
                logger.error('Card number must be in range [1, 8]')
            self.__wait(INTERVAL_SHORT)
        
        self.__wait(INTERVAL_LONG)

    def run(self, max_loops: int = 10):
        """
        Start the bot.

        :param max_loops: the max number of loops.
        """
        count = 0
        for n_loop in range(max_loops):
            logger.info('Entering battle...')
            if not self.__enter_battle():
                logger.info('AP runs out. Quiting...')
                break
            rounds = self.__play_battle()
            if rounds == -1:
                logger.error('{}-th Battle interrupt. {} rounds played.'.format(count, rounds))
                return -1
            else:
                self.__end_battle()
                count += 1
                logger.info('{}-th Battle complete. {} rounds played.'.format(count, rounds))

        logger.info('{} Battles played in total. Good bye!'.format(count))
        