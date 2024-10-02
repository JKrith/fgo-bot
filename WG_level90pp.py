"""
An example of custom battle bot.
:author: @JKrith
"""


from fgobot import bot
import logging

# 指定日志的输出等级（DEBUG / INFO / WARNING / ERROR）
# 建议日常使用时设 INFO，需要debug时设 DEBUG
logging.basicConfig(level=logging.INFO)

# 实例化一个 bot.BattleBot
insBot = bot.BattleBot(

    # 要打的关卡截图为'WG_level90p.png'，放在这个文件的同一级目录下
    quest='WG_level90pp.png',

    # 助战的职介 all / saber / archer / lancer / rider / assassin / berserker / extra
    friend_class = 'assassin',

    # 需要的助战截图为'TaiGong1.png'，放在这个文件的同一级目录下
    # 如果可以接受的助战有多个，可以传入一个list，例如：friend=['friend1.png', 'friend2.png]
    # 因为助战玩家可能开启了随机展示，最好截图助战从者的所有再临阶段
    friend=['TaiGong3.png','TaiGong1.png'],

    # AP策略为：当体力耗尽时，优先吃银苹果，再吃金苹果
    # 可选项为  rainbow_apple, gold_apple, silver_apple
    # 如果不指定ap参数，则当体力耗尽时停止运行
    ap=['silver_apple', 'gold_apple'],

    # 要打的关卡有3面
    stage_count = 3,

    # 关卡图像识别的阈值为0.90
    # 如果设的过低会导致进错本，太高会导致无法进本，请根据实际情况调整
    quest_threshold = 0.90,

    # 助战图像识别的阈值为0.95
    # 如果设的过低会导致选择错误的助战，太高会导致选不到助战，请根据实际情况调整
    friend_threshold = 0.95
)


# 为了方便，使用了简写
s = insBot.use_skill
ss=insBot.use_skill_special
m = insBot.use_master_skill
a = insBot.attack

# 建议用常量保存编队，下面是例子 
Kyskp = 1    #1号位  哈贝喵 退场   
Kkrk = 2   #2号位  汇呆
f_Kyskp = 3 #3号位  

# 第一面首个回合的打法
@insBot.at_stage(1)
def stage_1():

    # s(1, 2)表示使用1号从者的技能2
    s(1, 2)
    # 定义了常量 Habe = 1 后，可以键入 Habe 代替数字1 
    s(Habe, 3, Alcas)
    s(Taigong, 2)
    s(Taigong, 1)
    s(Taigong, 3)
    # 选卡： 1号位哈贝喵的宝具、若有则优先选取汇呆蓝卡、任意卡
    a([6, 'artsAlcas', 9])


# 第二面首个回合的打法
@insBot.at_stage(2)
def stage_2():
    
    # s(1, 3, Taigong) 表示使用 1号位RBA的 1技能，目标 3号位太公
    #s(1, 3, Taigong)
    #s(Rba, 1, Taigong)
    s(Rba, 2)
    s(Alcas, 3)
    s(Alcas, 2, Alcas)
    s(Alcas, 1)
    a([7, 'artsAlcas', 9])


# 第三面首个回合的打法
@insBot.at_stage(3)
def stage_3():

    # m(2, 3)表示使用御主技能2，对象为 3号位太公
    #m(2, Taigong)
    a([8, 'artsAlcas', 9])

@insBot.xjbd(stage= 2)
def xjbd_2():
    a([9, 9, 9])
    
@insBot.xjbd(stage= 2)
def xjbd_2():
    a([9, 9, 9])
# 程序的入口点（不加这行也可以）
# 使用时，可以直接在命令行运行'python WG_level90p.py'
if __name__ == '__main__':
    # 检查设备是否连接
    if not insBot.device.connected():
        
        # 如果没有连接，则尝试通过本地端口16384连接（具体参数请参考自己的设备/模拟器）
        # 如果不知道如何查看端口号，请参考 https://mumu.163.com/help/20230214/35047_1073151.html
        insBot.device.connect('127.0.0.1:16384')

    # 启动bot，打3次，最多打5次
    insBot.run(max_loops=3)
