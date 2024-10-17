"""
Game auto-playing bot.
"""

import logging

from functools import partial
from typing import Dict, Any, Callable
from . import device
import json
from pathlib import Path
from typing import Tuple, List, Union, Literal
from random import randint

logger = logging.getLogger('bot')

# time for waitting between operations
INTERVAL_LONG = 20          # used in wait: loading battle, playing attack animation
INTERVAL_MID   = 4          # used in wait: loading friend list 
INTERVAL_SHORT = 1          # used in wait: pop up windows, any other case

# argument for calculating the position of friendlist class button
ALL     = 0
SABER   = 1
ARCHER  = 2
LANCER  = 3
RIDER   = 4
CASTER  = 5
ASSASSIN = 6
BERSERKER = 7
EXTRA   = 8

class BattleBot:
    """
    A class of the bot that automatically play battles.
    """

    def __init__(self,
                 quest: str = 'quest.png',
                 friend_class: int = CASTER,
                 friend: Union[str, List[str]] = 'friend.png',
                 stage_count = 3,
                 ap: List[str] = None,
                 quest_threshold: float = 0.97,
                 friend_threshold: float = 0.97,
                 port: str = '127.0.0.1:16384',
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
        :param port: the connect port of device
        """
        logger.info('Fgobot loading...')

        # A dict of the handler functions that are called repeatedly at each stage.
        # Use `at_stage` to register functions.
        self.stage_handlers = {}
        self.xjbd_handlers = {}

        # A dict of configurations.
        self.config = {}

        self.stage_count = stage_count
        logger.info('Stage count set to {}.'.format(self.stage_count))

        self.friend_class = friend_class

        #Collect paths of user' s images and Tag these paths
        user_imgs = dict()
        # image of quest
        user_imgs['quest'] = Path(quest).absolute()

        # images of friends
        # if friend has only 1 element, exchange into type list 
        if isinstance(friend, str):
            friend = [friend]
            
        self.friend_count = len(friend)     # Count of expected friend servants
        logger.info('Friend count is {}.'.format(self.friend_count))
        for fid in range(self.friend_count):
            user_imgs['f_{}'.format(fid)] = Path(friend[fid]).absolute()

        # Device
        self.device = device.Device(load_imgs= user_imgs, port= port, 
                                    capture_method= device.FROM_SHELL)

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

    def __swipe(self, track):
        """
        Swipe in given track.

        :param track:
        :return:
        """
        x1, y1, x2, y2 = map(lambda x: x, self.buttons['swipe'][track])
        self.device.swipe((x1, y1), (x2, y2))
    
    def tap_button(self, base_position_key:str, increment:list = None) ->bool :
        """
        read argument from buttons.json, use argument to calculate the position of button
         and tap button.
        
        """
        x, y = self.buttons[base_position_key].values()
        if increment is not None:
            for distance_key, distance_number in increment:
                assert isinstance(distance_key, str),  'arg: increment invalid'
                assert isinstance(distance_number, int),  'arg: increment invalid'
                x += self.buttons[distance_key] * distance_number
        return self.device.tap(x, y)

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
    
    def __select_class(self, friend_class: int):
        """
        Select friend's class

        :return: None
        """

        x, y = self.buttons['all'].values()
        x += self.buttons['support_class_distance'] * (friend_class)
        logger.info(f'select class {friend_class}')
        self.device.tap(x, y)
        self.device.wait_and_updateScreen(INTERVAL_SHORT /2 )

    def select_friend(self, friendList_status:int ) -> bool:
        """
        Select friend and enter team select screen 

        :Return True if enter successs
        """
        if friendList_status== 0:
            self.__refresh_friendlist()

        swp_times = 0
        while True:
            for fid in range(self.friend_count):
                im = 'f_{}'.format(fid)
                logging.disable(logging.WARNING)
                
                if self.device.find_and_tap(im, threshold=self.friend_threshold):
                    logging.disable(logging.NOTSET)
                    self.device.wait(INTERVAL_SHORT)
                    return True
            # when all friends are not found
            else:
                # swipe to find
                if swp_times <5 :
                    swp_times += 1
                    self.__swipe('friend')
                    self.device.wait_and_updateScreen(INTERVAL_SHORT)
                # refresh
                else:
                    swp_times = 0
                    self.__refresh_friendlist()

    def __refresh_friendlist(self):
        while True:
            x, y = self.buttons['refresh_friends'].values()
            self.device.tap(x, y)
            self.device.wait(INTERVAL_SHORT)

            x, y = self.buttons['refresh_friends_yes'].values()
            self.device.tap(x, y)
            # if friend appear, quit loop, else tap refresh again 
            if self.device.wait_until('view_friend_party', countLimit= 10):
                break
    
    def __from_terminal_select_quest(self):
        """
        Select quest. Update screen when return

        :Return: True if success,

        else False
        """
        self.device.update_screen()
        while not self.device.find_and_tap('quest', threshold=self.quest_threshold):
            self.__swipe('quest')
            self.device.wait_and_updateScreen(INTERVAL_SHORT)
        self.device.wait_and_updateScreen(INTERVAL_MID)

    def __enter_battle(self, battle_count: int) -> bool:
        """
        Enter the battle.

        :param battle_count: read the value of `run.count`, 
        deciding whether skip quest selection and team selection 

        :return: True if successful, else False.
        """
        if battle_count == 0:
            logger.info("try to select quest")
            self.__from_terminal_select_quest()

        # 4 cases and corresponding treatments
        case_list = {
            # case 1: when enough AP enter quest except Ordeal Call
            'friend_pick'   :self.__friendList_loading, 

            # case 2: when enough AP enter Ordeal Call quest
            'quest_start'   :self.__friendList_loading, 

            # case 3: no enough AP in quests except Ordeal Call
            'ap_regen'      :self.__recover_ap_normal,
                
            # case 4: no enough AP in Ordeal Call quests
            'recover_ap'    :self.__recover_ap_OrdealCall
            }
        for case, treatment in case_list.items():
            if self.device.find_and_tap(case):
                friendList_status = treatment()
                break

        else:
            # need to check macro: INTERVAL used in 'wait()' or 'wait_and_updateScreen()' 
            # also check the images used to enter quest, path:./fgobot/images/ 
            logger.error("please adjust INTERVAL_MID in /fgobot/bot.py, \
                         or check .png file in /fgobot/images")
            return False
        # when ap runs out
        if friendList_status== -1:
            return False
        
        logger.info("try to select friend")
        
        if battle_count == 0:
            self.__select_class(self.friend_class)
        
        self.select_friend(friendList_status)

        # decide the party, only when first entry 
        if battle_count == 0:
            logger.info("select team")
            self.device.wait_until_tap('start_quest')

        logger.info('wait...')
        self.device.wait(INTERVAL_LONG)
        self.device.wait_until('attack')
        logger.info('Enter success')
        return True
            
    def __friendList_loading(self) :
        """
        waiting for loading friendlist. When loading finished, 
        return friend list status to control
        the behavior of select_friend()
        """
        while True:
            self.device.update_screen()
            # friend appear
            if self.device.exists('view_friend_party') :
                return 1
            
            # no friend
            elif self.device.exists('noSupport'):
                return 0
            
            # loading has not finished
            else:
                self.device.wait(INTERVAL_SHORT *2)

    def __recover_ap_normal(self):
        """
        In normal quest, recover ap
        """
        if self.__eat_Apple():
            return self.__friendList_loading()
        else:
            # -1 stand for fail to enter friend list
            return -1

    def __recover_ap_OrdealCall(self):
        """
        In Ordeal Call quest, recover ap
        There is one more pop-up window in Ordeal Call quest
        """
        if self.__eat_Apple():
            self.device.wait_and_updateScreen(INTERVAL_SHORT *2)
            self.device.find_and_tap('quest_start')
            return self.__friendList_loading()
        else:
            # -1 stand for fail to enter friend list
            return -1
    
    def __eat_Apple(self) -> bool:
        """
        Recover AP

        :Return: False if no ap strategy or fail to recover
        """
        logger.info("try to eat Apple")
        if not self.ap:
            logger.error('AP策略不能为空')
            return False
        else:
            self.device.wait_and_updateScreen(INTERVAL_SHORT)
            for ap_item in self.ap:
                if  self.device.find_and_tap(ap_item):
                    self.device.wait_and_updateScreen(INTERVAL_SHORT)
                    self.device.find_and_tap('decide')
                    logger.info("Apple used")
                    return True
            else:
                logger.error('找不到AP道具 或者 道具已用尽')
                return False

    def __play_battle(self) -> int:
        """
        Play the battle.

        :return: count of rounds.
        """
        rounds = 0
        lastStage = 0
        while True:
            stage = self.__get_current_stage()
            if stage == -1:
                logger.error("Failed to get current stage. Quit battle...")
                return -1

            rounds += 1
            
            # when fail to enter the next stage, go XJBD
            if lastStage == stage:
                logger.info('At stage {}/{}, round {}, go xjbd...'
                            .format(stage, self.stage_count, rounds))
                self.xjbd_handlers[stage]()
            else:
                logger.info('At stage {}/{}, round {}, calling handler function...'
                            .format(stage, self.stage_count, rounds))
                self.stage_handlers[stage]()

            while True:
                if self.device.updateScreen_and_exists('bond'):
                    logger.info("'与从者的牵绊' detected. Leaving battle...")
                    return rounds
                elif self.device.exists('attack'):
                    logger.info("'Attack' detected. Continuing loop...")
                    # update the last stage
                    lastStage = stage
                    break
                else:
                    self.device.wait(INTERVAL_SHORT *2)

    def __end_battle(self, battle_count: int, max_loops: int):
        """
        Click to end the billing page. Update screen when return
        
        :param battle_count:
        :param max_loops: read the value of `run.count` and `run.max_loops`, 
        deciding to continue or quit battle
        """
        
        while not self.device.updateScreen_and_exists('next_step'):
            self.device.tap(590, 230)
            self.device.wait(INTERVAL_SHORT)

        x, y = self.buttons['next_step'].values()
        self.device.tap(x, y)
        self.device.wait_and_updateScreen(INTERVAL_SHORT * 2)

        # not send friend application
        if self.device.find_and_tap('not_apply'):
            self.device.wait_and_updateScreen(INTERVAL_SHORT)

        # continue battle
        if battle_count < max_loops:
            if self.device.find_and_tap('continue_battle'):
                self.device.wait_and_updateScreen(INTERVAL_SHORT *2)
                return True
            else:
                logger.error('storm-tank runs out')
                return False
        # quit battle
        else:
            self.device.find_and_tap('close')
            logger.info('wait...')
            self.device.wait(INTERVAL_LONG)
            self.device.wait_until('menu')
            return True

    def __wait_manual_operation(self, im: str, sec: int = INTERVAL_SHORT *2):
        """
        waitting for manual operation, when lack proper skill object

        :param im: name of image, recommend using the name of pop-up window 
        :param sec: interval time for waitting
        """
        logger.info('请手动完成此技能的操作, 脚本将在操作完成后继续')

        # disable logging output at level 'info' and lower
        logging.disable(level=logging.INFO)

        # wait until the pop-up window has been closed
        while self.device.updateScreen_and_exists(im):
            self.device.wait(sec)
        
        # enable all logging output
        logging.disable(logging.NOTSET)
        logger.info("Resume battle")

    def at_stage(self, stage: int):
        """
        A decorator that is used to register a handler function to a given stage of the battle.

        :param stage: the stage number
        """
        #logger.debug('Function {} registered to stage {}'.format(f.__name__, stage))
        def decorator(f):
            self.__add_stage_handler(stage, f)
            return f
        return decorator
    
    def xjbd(self, stage: int):
        """
        A decorator that is used to register a xjbd function to a given stage of the battle.

        :param stage: the stage number
        """
        def decorator(f):
            logger.debug('Function {} registered to stage {}'.format(f.__name__, stage))
            assert not self.xjbd_handlers.get(stage), 'Cannot register multiple function to a single stage.'
            self.xjbd_handlers[stage] = f
        return decorator

    def use_skill(self, servant: int, skill: int, obj=None, \
                  reinforceOrNot: bool = None):
        """
        Use a skill.

        :param servant: the servant id.
        :param skill: the skill id.
        :param obj: the object of skill, if required.
        :param reinfoceOrNot: whether reinforce skill or not.
        """
        x, y = self.buttons['skill'].values()
        x += self.buttons['servant_distance'] * (servant - 1)
        x += self.buttons['skill_distance'] * (skill - 1)
        logger.info('Used skill ({}, {})'.format(servant, skill))
        self.device.tap(x, y)
        self.device.wait(INTERVAL_SHORT)
        
        # skill reinforce, for example, KuKulcan
        if reinforceOrNot is not None:
            if reinforceOrNot:
                x, y = self.buttons['skill_reinforce']['yes']
                self.device.tap_and_wait(x, y, INTERVAL_SHORT/2)
            else:
                x, y = self.buttons['skill_reinforce']['no']
                self.device.tap_and_wait(x, y, INTERVAL_SHORT /2)

        # when need to select object
        if self.device.updateScreen_and_exists('choose_object'):
            if obj is None:
                logger.warning('请为 servant-{} 的技能{} 指定对象.'.format(servant, skill))
                self.__wait_manual_operation(im= 'choose_object')

            else:
                x, y = self.buttons['choose_object'].values()
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

        x, y, w, h = self.buttons['master_skill_menu'].values()
        self.device.tap_and_wait(x, y, INTERVAL_SHORT)

        x, y, w, h = self.buttons['master_skill'].values()
        x += self.buttons['master_skill_distance'] * (skill - 1)
        self.device.tap_and_wait(x, y, INTERVAL_SHORT)
        logger.info('Used master skill {}'.format(skill))

        # when need to select 1 object
        if self.device.updateScreen_and_exists('choose_object'):
            if obj is None:
                logger.warning('请为 master技能{} 指定一个对象.'.format(skill))
                self.__wait_manual_operation(im= 'choose_object')
            elif 1 <= obj <= 3:
                x, y = self.buttons['choose_object'].values()
                x += self.buttons['choose_object_distance'] * (obj - 1)
                self.device.tap(x, y)
                logger.info('Chose master skill object {}.'.format(obj))
            else:
                logger.warning('master技能{} 的对象不恰当.'.format(skill))
                self.__wait_manual_operation(im= 'choose_object')

        # when need to select 2 objects
        elif self.device.exists('change_disabled'):
            if obj is None or obj2 is None:
                logger.warning('请为 master换人技能 指定两个对象.')
                self.__wait_manual_operation(im= 'change_disabled')

            elif 1 <= obj <= 3 and 4 <= obj2 <= 6:
                x, y, w, h = self.buttons['change'].values()
                x += self.buttons['change_distance'] * (obj - 1)
                self.device.tap(x, y)

                x += self.buttons['change_distance'] * (obj2 - obj)
                self.device.tap_and_wait(x, y, INTERVAL_SHORT)
                logger.info('Chose order change object ({}, {}).'.format(obj, obj2))

                self.device.find_and_tap('change')
                logger.info('Order Change')
            else:
                logger.warning(f'master换人技能的对象{obj}, {obj2}不恰当.')
                self.__wait_manual_operation(im= 'change_disabled')

        # when no need to select or selection is finished
        self.device.tap(590, 230)
        self.device.wait(INTERVAL_SHORT)
        self.device.wait_until('attack')
    
    def __choose_enemy(self, enemy: int=3):
        """
        choose enemy, as object of skill or attack. From left to right are 1, 2, 3
        """
        x, y = self.buttons['enemy'].values()
        x += self.buttons['enemy_distance'] * (enemy - 1)
        self.device.tap(x, y)

    def use_skill_enemy(self, servant:int, skill:int, enemy:int=3):
        """
        Use a servant skill to an Enemy. 

        :param skill: the skill id.
        :param enemy: the object of skill. From left to right are 1, 2, 3
        """
        logger.info(f'Servant-{servant} skill-{skill} Target: {enemy}')
        self.__choose_enemy(enemy)
        self.use_skill(servant, skill, None, None)

    def use_master_skill_enemy(self, skill:int, enemy:int=3):
        """
        Use a master skill to an Enemy. 

        :param skill: the skill id.
        :param enemy: the object of skill. From left to right are 1, 2, 3
        """
        logger.info(f'Master skill-{skill} Target: {enemy}')
        self.__choose_enemy(enemy)
        self.use_master_skill(skill, None, None)

    def use_spell(self, obj: Literal[1, 2, 3]):
        """
        Use spell to charge for `obj`-th servant
        
        :param obj: the number of servant, should be one of [1,2,3]
        """
        # continuously tap
        for im in ['spell', 'spell_np', 'spell_decide']:
            x, y = self.buttons[im].values()
            self.device.tap(x, y)
            self.device.wait(INTERVAL_SHORT /2)

        if 1 <= obj <= 3:
            x, y = self.buttons['choose_object'].values()
            x += self.buttons['choose_object_distance'] * (obj - 1)
            logger.info(f'Spell used, obj is servant[{obj}]')
            self.device.tap(x, y)
        else:
            logger.warning(f'使用令咒的对象{obj}不恰当 应该是1、2或3.')
            self.__wait_manual_operation('choose_object')

        # tap for high speed animation
        self.device.tap()
        self.device.wait_until('attack', INTERVAL_SHORT*2)
        return

    def attack_old(self, cards: list):
        """
        Tap attack __button and choose three cards.

        1 ~ 5 stands for normal cards, 6 ~ 8 stands for noble phantasm cards.

        :param cards: the cards id, as a list

        """
        assert len(cards) == 3, 'Number of cards must be 3.'
        assert len(set(cards)) == 3, 'Cards must be distinct.'

        x, y, w, h = self.buttons['attack'].values()
        self.device.tap(x, y)
        self.device.wait(INTERVAL_SHORT * 2)

        
        for card in cards:
            if 1 <= card <= 5:
                x, y, w, h = self.buttons['card'].values()
                x += self.buttons['normal_card_distance'] * (card - 1)
                self.device.tap_rand(x, y, w, h)
            elif 6 <= card <= 8:
                x, y, w, h = self.buttons['noble_card'].values()
                x += self.buttons['noble_card_distance'] * (card - 6)
                self.device.tap_rand(x, y, w, h)
            else:
                logger.warning('Card number must be in range [1, 8]')
            self.device.wait(INTERVAL_SHORT)
        
        logger.info('wait...')
        self.device.wait(INTERVAL_LONG)

    def attack(self, cards: list, enemy: int=3 ):
        """
        Tap 'attack' button and choose three cards.
        
        :param cards: list, its lenth should be 3, and its element should be one of
        :param enemy: the object of skill. From left to right are 1, 2, 3
        number `9` for XJBD / number `6 ~ 8` for noble card / your preferred card
        """
        assert len(cards) == 3, 'Number of cards must be 3.'
        
        self.__choose_enemy(enemy)

        x, y, _, _ = self.buttons['attack'].values()
        self.device.tap(x, y)
        self.device.wait_until('battleBack')

        self.__unselected_NormalCards = {
                0 : True,
                1 : True,
                2 : True,
                3 : True,
                4 : True,
            }
        cardsOption = {
                6 : self.__attack_hougu,
                7 : self.__attack_hougu,
                8 : self.__attack_hougu,
                9 : self.__attack_random,
            }

        # pop each element from cards and tap it
        for userChoice in cards:
            # add user's preferred card to cards option
            if isinstance(userChoice, str) and userChoice not in cardsOption:
                cardsOption[userChoice] = self.__attack_preferred
                self.device.load_image(Path(userChoice +'.png'), userChoice)
            
            # execute the choice
            cardsOption[userChoice](userChoice)
            
            # interval between clicks 
            self.device.wait_and_updateScreen(INTERVAL_SHORT /2)

        # waiting for battle animation
        logger.info('wait...')
        self.device.wait(INTERVAL_LONG)
    
    def __attack_hougu(self, userChoice: int):

        x, y, w, h = self.buttons['noble_card'].values()
        x += self.buttons['noble_card_distance'] * (userChoice - 6)
        logger.info('choose hougu[{}]'.format(userChoice -5))
        self.device.tap_rand(x, y, w, h)

    def __attack_random(self, noUseParam = 0):
        # choose the left most of unselected cards 
        for i in range(5):
            if self.__unselected_NormalCards[i] == True:
                selected_card = i
                break
        x, y, w, h = self.buttons['card'].values()
        x += self.buttons['normal_card_distance'] * (selected_card)
        
        logger.info('choose card[{}]'.format(selected_card +1))
        self.device.tap_rand(x, y, w, h)
        self.__unselected_NormalCards[selected_card] = False
        
    def __attack_preferred(self, userChoice: str):
        success, (x, y) = self.device.find_and_tap(userChoice, 0.85, withPosition= True)

        # if not found, do as 'random'
        if not success:
            logger.info('NO preferredCard {} found, select at random'.format(userChoice))
            self.__attack_random()
            return
        
        # if found, calculate the location of chosen card, pop it from unselected cards
        logger.info('choose card {}'.format(userChoice))
        x -= 50
        location = -1   # location range [0,4]
        while x >0:
            location += 1
            x -= self.buttons['normal_card_distance']
        else:
            self.__unselected_NormalCards[location] = False

    def __check_xjbd_handlers(self) -> bool:
        try:
            # Check if the handler count is less than the expected stage count
            if len(self.xjbd_handlers) != self.stage_count:
                raise Exception('xjbd less than stage count, try to auto fill')
        except Exception as e:
            # Handle the case when handlers are fewer than expected
            logger.warning(e)  
            for n in range(1, self.stage_count + 1):
                # Fill missing handlers with __attack_xjbd method
                if not self.xjbd_handlers.get(n):
                    logger.debug(f'attack([9,9,9]) registered to xjbd {n}')
                    self.xjbd_handlers[n] = partial(self.attack, [9, 9, 9])

        logger.info('handlers filled')
        return True
    
    def run(self, max_loops: int = 3):
        """
        Start the bot.

        :param max_loops: the max number of loops.
        """
        self.__check_xjbd_handlers()
        #count for the number of battles which were completed successfully
        count = 0
        for n_loop in range(max_loops):
            
            logger.info('Entering battle...')
            if not self.__enter_battle(count):
                logger.info('Quiting...')
                break

            rounds = self.__play_battle()
            if rounds == -1:
                logger.error('{}-th Battle interrupt. {} rounds played.'.format(count, rounds))
                return -1
            else:
                count += 1
                if not self.__end_battle(count, max_loops):
                    break
                logger.info('{}-th Battle complete. {} rounds played.'.format(count, rounds))
                
        logger.info('{} Battles played in total. Good bye!'.format(count))
