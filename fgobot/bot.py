"""
Game auto-playing bot.
"""

import logging

from functools import partial
from typing import Dict, Any, Callable
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
INTERVAL_LONG = 20


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

        self.friend_class = friend_class

        if isinstance(friend, str):
            friend = [friend]

        # Count of expected friend servants
        self.friend_count = len(friend)
        logger.info('Friend count is {}.'.format(self.friend_count))

        #Collect paths of user' s images and Name these paths
        user_imgs = dict()
        user_imgs['quest'] = Path(quest).absolute()
        for fid in range(self.friend_count):
            user_imgs['f_{}'.format(fid)] = Path(friend[fid]).absolute()

        # Device
        self.device = Device(load_imgs= user_imgs, capture_method= 'FROM_SHELL')

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

    def __get_current_stage(self) -> int:
        """
        Get the current stage in battle.

        :return: current stage. Return -1 if error occurs.
        """
        
        max_prob, max_stage = 0.70, -1
        for stage in range(1, self.stage_count + 1):
            im = '{}_{}'.format(stage, self.stage_count)
            prob = self.device.probability(im)
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
        self.device.wait_and_capture(0.5)

    def __select_friend(self) -> bool:
        """
        Select friend and enter team select screen 

        :Return True if enter successs
        """
        self.device.wait_until("view_friend_party", INTERVAL_SHORT *2)
        self.__select_class(self.friend_class)
        
        friend = ''
        swp_times = 0
        while not friend:
            for fid in range(self.friend_count):
                im = 'f_{}'.format(fid)
                if self.device.find_tap(im, threshold=self.friend_threshold):
                    friend = im
                    break
            if friend:
                break
            elif swp_times >5 :
                swp_times = 0
                self.device.wait_until_tap('refresh_friends')
                self.device.wait(INTERVAL_SHORT)
                self.device.capture_find_tap('yes')
                self.device.wait_until('view_friend_party')
            else:
                swp_times += 1
                self.__swipe('friend')
                self.device.wait_and_capture(INTERVAL_SHORT)
    
    def __from_terminal_select_quest(self):
        """
        Select quest

        :Return: True if success,

        else False
        """
        while not self.device.capture_find_tap('quest', threshold=self.quest_threshold):
            self.__swipe('quest')
            self.device.wait(INTERVAL_SHORT)
        self.device.wait(INTERVAL_SHORT * 2)

    def __enter_battle(self) -> bool:
        """
        Enter the battle.

        :return: True if successful, else False.
        """
        logger.info("try to select quest")
        self.__from_terminal_select_quest()

        # Capture for 1 time, then Judge 4 cases
        self.device.capture_screen()
        # case 1: when enough AP enter quest except Ordeal Call
        if self.device.exists('friend_pick'):
            self.device.wait(INTERVAL_SHORT)
        # case 2: when enough AP enter Ordeal Call quest
        elif self.device.find_tap('quest_start'):        
            self.device.wait(INTERVAL_SHORT)

        # case 3: no enough AP in quests except Ordeal Call
        elif self.device.exists('ap_close'):
            logger.info("eat Apple")
            if self.__eat_Apple():
                self.device.wait(INTERVAL_SHORT)
            else:
                logger.info('AP runs out')
                return False

        # case 4: no enough AP in Ordeal Call quests
        elif self.device.find_tap('recover_ap'):
            self.device.wait(INTERVAL_SHORT)
            logger.info("eat Apple")
            if self.__eat_Apple():
                self.device.wait(INTERVAL_SHORT)
                self.device.capture_find_tap('quest_start')
                self.device.wait(INTERVAL_SHORT)
            else:
                logger.info('AP runs out')
                return False
        # fail to enter, Maybe need to check 'the arg: sec' of 'function: wait' 
        # also check the images used to enter quest, path:./fgobot/images/ 
        else:
            logger.error("请检查函数'wait'的参数'sec' 和 用于识别的照片")
            return False
        
        logger.info("try to select friend")
        self.__select_friend()
        self.device.wait(INTERVAL_SHORT)
        
        logger.info("select team")
        self.device.wait_until_tap('start_quest')
        self.device.wait(INTERVAL_LONG)
        self.device.wait_until('attack')
        return True
    
    def __eat_Apple(self) -> bool:
        """
        Recover AP

        :Return: False if no ap strategy or fail to recover
        """
        if not self.ap:
            logger.error('请检查 AP 策略')
            return False
        else:
            ok = False
            for ap_item in self.ap:
                x = self.buttons['apple'][ap_item]['x']
                y = self.buttons['apple'][ap_item]['y']
                if self.device.tap(x, y):
                    self.device.wait(INTERVAL_SHORT)
                    if self.device.capture_find_tap('decide'):
                        logger.info("Apple used")
                        ok = True
                        break
            if ok:
                return True
            else:
                logger.error('请检查buttons.json中的参数 和 路径./fgobot/下用于识别的图片')
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

            self.stage_handlers[stage]()

            while True:
                if self.device.capture_and_exists('bond'):
                    logger.info("'与从者的牵绊' detected. Leaving battle...")
                    return rounds
                elif self.device.exists('attack'):
                    logger.info("'Attack' detected. Continuing loop...")
                    break

    def __end_battle(self):

        
        while not self.device.capture_and_exists('next_step'):
            self.device.tap(590, 230)
            self.device.wait(INTERVAL_SHORT)

        x, y = self.buttons['next_step'].values()
        self.device.tap(x, y)
        self.device.wait(INTERVAL_SHORT * 2)

        # not send friend application
        if self.device.capture_find_tap('not_apply'):
            self.device.wait(INTERVAL_SHORT)
            
        # quit quest
        self.device.capture_find_tap('close')

        self.device.wait(INTERVAL_LONG)
        self.device.wait_until('menu')

    def __wait_maual_operation(self, im: str, sec: int = INTERVAL_SHORT *2):
        """
        waitting for manual operation, when lack proper skill object

        :param im: name of image, recommend using the name of pop-up window 
        :param sec: interval time for waitting
        """
        logger.info('请手动完成此技能的操作, 脚本将在操作完成后继续')
        # disable logging output at level 'info' and lower
        logging.disable(level=logging.INFO)
        # wait until the pop-up window has been close
        while self.device.capture_and_exists(im):
            self.device.wait(sec)
        # enable all logging output
        logging.disable(logging.NOTSET)
        logger.info("Resume battle")

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
        logger.info('Used skill ({}, {})'.format(servant, skill))
        self.device.tap(x, y)
        self.device.wait(INTERVAL_SHORT)

        # when need to select object
        if self.device.capture_and_exists('choose_object'):
            if obj is None:
                logger.warning('请为 servant-{} 的技能{} 指定对象.'.format(servant, skill))
                self.__wait_maual_operation(im= 'choose_object')

            else:
                x, y, w, h = self.__button('choose_object')
                x += self.buttons['choose_object_distance'] * (obj - 1)
                logger.info('Chose skill object {}.'.format(obj))
                self.device.tap(x, y)

        #when no need to select or selection is finished 
        #click for high speed skill animation
        self.device.tap(590, 230)
        self.device.wait(INTERVAL_SHORT)
        self.device.wait_until('attack')

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
        self.device.wait(INTERVAL_SHORT)

        x, y, w, h = self.__button('master_skill')
        x += self.buttons['master_skill_distance'] * (skill - 1)
        self.device.tap(x, y)
        logger.info('Used master skill {}'.format(skill))
        self.device.wait(INTERVAL_SHORT)

        # when need to select 1 object
        if self.device.capture_and_exists('choose_object'):
            if obj is None:
                logger.warning('请为 master技能{} 指定一个对象.'.format(skill))
                self.__wait_maual_operation(im= 'choose_object')
            elif 1 <= obj <= 3:
                x, y, w, h = self.__button('choose_object')
                x += self.buttons['choose_object_distance'] * (obj - 1)
                self.device.tap(x, y)
                logger.info('Chose master skill object {}.'.format(obj))
            else:
                logger.warning('master技能{} 的对象不恰当.'.format(skill))
                self.__wait_maual_operation(im= 'choose_object')

        # when need to select 2 objects
        elif self.device.exists('change_disabled'):
            if obj is None or obj2 is None:
                logger.warning('请为 master换人技能 指定两个对象.')
                self.__wait_maual_operation(im= 'change_disabled')

            elif 1 <= obj <= 3 and 4 <= obj2 <= 6:
                x, y, w, h = self.__button('change')
                x += self.buttons['change_distance'] * (obj - 1)
                self.device.tap(x, y)

                x += self.buttons['change_distance'] * (obj2 - obj)
                self.device.tap(x, y)
                logger.info('Chose order change object ({}, {}).'.format(obj, obj2))
                self.device.wait(INTERVAL_SHORT)
                self.device.find_tap('change')
                logger.info('Order Change')
            else:
                logger.warning('master换人技能 的对象不恰当.')
                self.__wait_maual_operation(im= 'change_disabled')

        # when no need to select or selection is finished
        self.device.tap(590, 230)
        self.device.wait(INTERVAL_SHORT)
        self.device.wait_until('attack')

    def attack(self, cards: list):
        """
        Tap attack __button and choose three cards.

        1 ~ 5 stands for normal cards, 6 ~ 8 stands for noble phantasm cards.

        :param cards: the cards id, as a list

        """
        assert len(cards) == 3, 'Number of cards must be 3.'
        assert len(set(cards)) == 3, 'Cards must be distinct.'

        x, y, w, h = self.__button('attack')
        self.device.tap(x, y)
        self.device.wait(INTERVAL_SHORT * 2)
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
                logger.warning('Card number must be in range [1, 8]')
            self.device.wait(INTERVAL_SHORT)
        
        self.device.wait(INTERVAL_LONG)

    def run(self, max_loops: int = 10):
        """
        Start the bot.

        :param max_loops: the max number of loops.
        """
        count = 0
        for n_loop in range(max_loops):
            logger.info('Entering battle...')
            if not self.__enter_battle():
                logger.info('Quiting...')
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
        