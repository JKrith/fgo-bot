"""
An example of custom battle bot.
:time: 2024/10/08
:author: @JKrith
"""


from fgobot import bot
import logging

# 指定日志的输出等级（DEBUG / INFO / WARNING / ERROR）
# 建议日常使用时设 INFO，需要debug时设 DEBUG
logging.basicConfig(level=logging.INFO)

# 重设 INTERVAL_MID的值，单位为 秒 
# 如果设备配置低，游戏加载时间长，脚本可能会跳bug。在下行代码中增加 INTERVAL_MID的值，可能解决此问题
bot.INTERVAL_MID = 4

# 实例化一个 bot.BattleBot
insBot = bot.BattleBot(

    # 要打的关卡截图为'WG_level90p.png'，放在这个文件的同一级目录下
    quest='WG_level90pp.png', # 此关为 旺吉娜活动90++

    # 助战的职介 all / saber / archer / lancer / rider / assassin / berserker / extra
    friend_class = bot.EXTRA,

    # 需要的助战截图为'TaiGong1.png'，放在这个文件的同一级目录下
    # 如果可以接受的助战有多个，可以传入一个list，例如：friend=['friend1.png', 'friend2.png]
    friend=['Oberon.png'],

    # AP策略为：当体力耗尽时，优先吃银苹果，再吃金苹果
    # 可选项为  rainbow_apple, gold_apple, silver_apple
    # 如果不指定ap参数，则当体力耗尽时停止运行
    ap=['gold_apple'],

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
m = insBot.use_master_skill
a = insBot.attack

# 建议用常量保存编队，下面是例子 
CG= 1      
ALCAS = 2    
CAS = 3 
OBERON =1
# 第一面首个回合的打法
@insBot.at_stage(1)
def stage_1():

    # s(1, 2)表示使用1号从者的技能2
    s(ALCAS, 3)
    s(CAS, 3, ALCAS)
    s(CAS, 2, ALCAS)
    s(CG, 1)
    s(CG, 2)
    s(CG, 3)
    # 优先选库库红卡，如果有，就能解决一面并省下宝具
    a([7, 'artsAlcas', 9])  



# 第二面首个回合的打法
@insBot.at_stage(2)
def stage_2():
    
    # 如果上一面用过宝具，会在第三动卡住
    s(ALCAS, 1)
    s(CAS, 1)
    a([7, 'artsAlcas', 9])

# 第三面首个回合的打法
@insBot.at_stage(3)
def stage_3():
    m(3, 1, 4)
    m(1)
    s(OBERON, 1)
    s(OBERON, 2, ALCAS)
    s(ALCAS, 2, ALCAS)
    s(OBERON, 3, ALCAS)
    # 先选库库的宝具，再选库库任意卡，以免脚本选‘anyKkrk’时选到宝具
    a([7, 'artsAlcas', 9])

# 如果首个回合后没能解决一面，将执行下面的打法，作为补刀
# 第一面的补刀打法
@insBot.xjbd(stage= 1)
def xjbd_2():
    a([9, 9, 9])

# 第二面的补刀打法
@insBot.xjbd(stage= 2)
def xjbd_2():
    a([9, 9, 9])

# 第三面的补刀打法
@insBot.xjbd(stage= 3)
def xjbd_2():
    a([9 ,9, 9])


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
