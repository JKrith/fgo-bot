"""
An example of custom battle bot.
:author: @will7101
"""


from fgobot import bot
import logging

# 指定日志的输出等级（DEBUG / INFO / WARNING / ERROR）
logging.basicConfig(level=logging.INFO)

# 实例化一个bot
bot = bot.BattleBot(

    # 要打的关卡截图为'qp.png'，放在这个文件的同一级目录下
    quest='exp_level5.png',

    #助战的职介 all / saber / archer / lancer / rider / assassin / berserker / extra
    friend_class = bot.BERSERKER,
    
    # 需要的助战截图为'friend_qp.png'，放在这个文件的同一级目录下
    # 如果可以接受的助战有多个，可以传入一个list，例如：friend=['friend1.png', 'friend2.png]
    friend=['molgan-1.png','molgan-3.png'],

    # AP策略为：当体力耗尽时，优先吃银苹果，再吃金苹果
    # 可选项为  rainbow_apple, gold_apple, silver_apple, red_copper_apple, bronze_apple
    # 如果不指定ap参数，则当体力耗尽时停止运行
    ap=['silver_apple'],

    # 要打的关卡有3面   
    stage_count=3,

    # 关卡图像识别的阈值为0.97
    # 如果设的过低会导致进错本，太高会导致无法进本，请根据实际情况调整
    quest_threshold=0.95,

    # 助战图像识别的阈值为0.95
    # 如果设的过低会导致选择错误的助战，太高会导致选不到助战，请根据实际情况调整
    friend_threshold=0.95
)


# 为了方便，使用了简写
s = bot.use_skill
m = bot.use_master_skill
a = bot.attack_old
c = bot.use_spell
se=bot.use_skill_Enemy
me=bot.use_master_skill_Enemy

################################
# 编队 
Arc = 2
Rin = 1
King = 3

# 第一面的打法
@bot.at_stage(1)
def stage_1():
    
    # s(1, 2)表示使用1号从者的技能2
    # c(1)
    se(Arc, 2, 3)
    se(Arc, 1, 3)
    se(Arc, 3, 3)
    se(King, 2, 1)
    se(King, 3, 3)
    se(King, 1, 2)
    # (a[6, 1, 2])表示出卡顺序为：6号卡（1号从者宝具卡），1号卡，2号卡
    a([3, 1, 2])

# 第二面的打法
@bot.at_stage(2)
def stage_2():
    
    # m(2, 1)表示使用御主技能2，对象为1号从者
    me(3, 2)
    me(1, 1)
    me(2, 3)
    a([3, 1, 2])


# 第三面的打法
@bot.at_stage(3)
def stage_3():
    a([1, 3, 2])


# 程序的入口点（不加这行也可以）
# 使用时，可以直接在命令行运行'python my_bot.py'
if __name__ == '__main__':
    # 检查设备是否连接
    if not bot.device.connected():
        
        # 如果没有连接，则尝试通过本地端口62001连接（具体参数请参考自己的设备/模拟器）
        bot.device.connect('127.0.0.1:16384')

    # 启动bot，最多打5次
    bot.run(max_loops=15)