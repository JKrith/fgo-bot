# fgo-bot

fgo自动脚本

## 原理
- 通过adb连接安卓设备/模拟器，实现模拟点击、滑动、截取屏幕，**支持后台运行**
- 使用opencv提供的模板匹配来快速找图、定位
- 按照用户定义的策略来进行自动战斗等操作

## 安装

### 安装adb

如果已经安装adb，请跳过此步骤。

从[http://adbshell.com/downloads](http://adbshell.com/downloads)下载adb kits，解压，并加入PATH。

在命令行中输入`adb`，出现帮助信息则说明安装成功。

### 安装本体

下载这个项目，在根目录下运行
```
python3 setup.py install
```

## 使用前的准备
- 推荐使用模拟器进行游戏，并调整分辨率为`1280x720`。**使用真机可能导致分辨率和连接等问题。**

- 构筑所用的队伍。由于当前版本不支持获取敌方信息，建议选择稳定的宝具速刷队。

- 在设置中关闭“灵基再临第四阶段展示”选项，可以减少助战识别的工作量

- 在助战界面选择好想要的职介，确保（在线的）好友可以大概率刷出期望的助战。

- 手动进行一场对战。（非必须，用于选中队伍以及调整相关设置）

- 在战斗菜单中关闭“技能使用确认”和“宝具匀速”，打开“缩短敌人消失时间。

- 在选择指令卡界面调整游戏速度为2倍速。

- 在设备/模拟器上对要打的副本和期望的助战截图，放在脚本的同级目录下，可以参考`/qp.png`和`/friend_qp.png`。
  ![quest](https://github.com/will7101/fgo-bot/blob/master/qp.png?raw=true)
  
  ![friend](https://github.com/will7101/fgo-bot/blob/master/friend_qp.png?raw=true)
  
  注意：尽量截取更多的信息，但不要超出可点击的范围。

- 将游戏置于进入任务前的界面，例如下图。

  ![how to run](https://github.com/JKrith/fgo-bot/blob/master/how_to_run.png)

## 使用教程

### 编写你自己的脚本

在任意目录下创建一个python源文件，导入`fgobot`这个模块。

`fgobot.BattleBot`类提供了`@at_stage()`装饰器，只需要在你自己的`python`源文件中实例化一个`bot`，然后将函数注册到对应的战斗阶段，接着运行`bot.run()`，就可以实现自动战斗。

具体例子可以参考项目根目录下的`/my_bot.py`。

### API参考

#### `BattleBot.use_skill(servant, skill, obj=None)`

使用（从左往右）第`servant`个从者的第`skill`个技能，施放对象为第`obj`个从者（如果是指向性）

#### `BattleBot.use_master_skill(skill, obj=None, obj2=None)`

使用第`skill`个御主技能，作用对象为从者`obj`（如果是指向性）。

如果使用换人技能，还需要指定`obj2`作为被换上的从者。注意`obj2`需要在`4~6`之间。例如`obj=3,obj2=4`代表使用换人技能，交换第3（场上第3）和第4（场下第1）个。

#### `BattleBot.attack(cards)`

选取指令卡并攻击。

`cards`需要为有三个整数作为元素的`list`，按照顺序表示出的卡。其中`1~5`表示从左往右的常规卡，`6~8`表示从左往右的宝具卡。

例如`[6, 1, 2]`表示先使用从者1的宝具卡，再使用指令卡1和指令卡2。

## 更新日志

### 2024.8.28	

1. 现在脚本会单击“连续出击”来跳过选择关卡和选择编队
2. 架构调整，将原`device.py` 和`tm.py`两个模块合并为新`device.py`，原模块`bot.py`中的部分函数定义移入新`device.py`，增加了一些函数。同时，对原有函数做了以下调整：
   - 原`__wait()`函数重命名为`wait_and_capture()`，定义不变。新`wait()`函数的定义不同于原`__wait()`函数
   - `find()`和`probability()`合并为`match()`
   - 常量`FROM_SHELL`和`SDCARD_PULL`移到模块最外层

### 2024.8.18	在Github建立仓库

- 现在脚本使用技能后自动单击屏幕，加速动画播放
- 现在脚本可以选择助战职介，默认为“caster”
- 参考@yuezhilanyi，更新了` fgobot/images`文件夹下的图片，现在脚本可以用于当前版本的B服（简中服.版本号：2.86.1）