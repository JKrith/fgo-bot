# fgo-bot

fgo自动脚本

## 原理
- 通过adb连接安卓设备/模拟器，实现模拟点击、滑动、截取屏幕，**支持后台运行**
- 使用opencv提供的模板匹配来快速找图、定位
- 读取`/fgobot/config/buttons.json`的数据来计算按键和指令卡的位置
- 按照用户定义的策略来进行自动战斗等操作

## 安装

### 安装adb

如果已经安装adb，请跳过此步骤。

从[http://adbshell.com/downloads](http://adbshell.com/downloads)下载adb kits，解压，并加入PATH。

在命令行中输入`adb`，出现帮助信息则说明安装成功。

### 安装本体

下载这个项目的release，解压后在根目录下运行
```
python3 setup.py install
```

## 使用前的准备
- 推荐使用模拟器进行游戏。**使用真机可能导致分辨率和连接等问题。**

- 构筑所用的队伍。由于当前版本不支持获取敌方信息，建议选择稳定的宝具速刷队。

- 在设置中关闭“灵基再临第四阶段展示”选项，可以减少助战识别的工作量

- 在助战界面选择好想要的职介，确保（在线的）好友可以大概率刷出期望的助战。

- 手动进行一场对战。（非必须，用于选中队伍以及调整相关设置）

- 在战斗菜单中关闭“技能使用确认”和“宝具匀速”，打开“缩短敌人消失时间。

- 在选择指令卡界面调整游戏速度为2倍速。

- 在设备/模拟器上对要打的副本和期望的助战截图，放在脚本的同级目录下，可以参考`/exp_level5.png`和`/molgan-1.png`。
  ![quest](https://github.com/JKrith/fgo-bot/blob/main/exp_level5.png?raw=true)
  
  ![friend](https://github.com/JKrith/fgo-bot/blob/main/molgan-1.png?raw=true)
  
  注意：尽量截取更多的信息，但不要超出可点击的范围。

- 将游戏置于进入任务前的界面，例如下图。

  ![how to run](https://github.com/JKrith/fgo-bot/blob/main/how_to_run.png?raw=true)

## 使用教程

### 编写你自己的脚本

在任意目录下创建一个python源文件，导入`fgobot`这个模块。

`fgobot.BattleBot`类提供了`@at_stage()`装饰器，只需要在你自己的`python`源文件中实例化一个`bot`，然后将函数注册到对应的战斗阶段，接着运行`bot.run()`，就可以实现自动战斗。

具体例子可以参考Release解压后根目录下的`/WG_level90p.py`。

### API参考

#### `BattleBot.use_skill(servant, skill, obj=None, reinforceOrNot = None)`

使用（从左往右）第`servant`个从者的第`skill`个技能，施放对象为第`obj`个从者（如果是指向性）。

关于`reinforceOrNot`的设置，视技能的情况来决定:

- 如果是普通的技能，不需要特地设置这个参数（脚本自动使用默认值）
- 如果是可强化的，比如库库尔坎消耗暴击星 / 水妖高的宝具单体化，并且你想要强化，设置`reinforceOrNot = True`
- 如果是可强化的但你不想强化，设`reinforce = False`

如果技能有对敌单体的效果，请改用下面的`BattleBot.use_skill_enemy`。

#### `BattleBot.use_master_skill(skill, obj=None, obj2=None)`

使用第`skill`个御主技能，作用对象为从者`obj`（如果是指向性）。

如果使用换人技能，还需要指定`obj2`作为被换上的从者。注意`obj2`需要在`4~6`之间。例如`obj=3,obj2=4`代表使用换人技能，交换第3（场上第3）和第4（场下第1）个。

如果技能有对敌单体的效果，请改用下面的`BattleBot.use_master_skill_enemy`。

#### `BattleBot.use_spell(obj)`

使用令咒，为第`obj`个从者充能。目前只支持令咒的充能用法。

#### `BattleBot.use_master_skill_enemy(skill, enemy=3)`

对从左到右第`enemy`个敌人，使用第`skill`个衣服技能。

#### `BattleBot.use_skill_enemy(servant, skill, enemy=3)`

对从左到右第`enemy`个敌人，使用第`skill`个从者技能。

#### `BattleBot.attack(cards, enemy=3)`

目标第`enemy`个敌人（从左到右），选取指令卡并攻击。

`cards`必须是三个元素的`list`，元素可以是6~9的整数，也可以是字符串:

- `6~8`表示从左往右的宝具卡
- `9`表示任意的平A卡，脚本将从未选卡中选出最靠左的一张
- 字符串表示希望优先选取的指令卡（找不到时按`9`的情况处理）

需要提前将指令卡截图为“xxxx.png”放在脚本的同级目录下。

例如将汇呆蓝卡截图为“artsAlcas.png”，然后在`attack()`中传入`[6, 'artsAlcas', 9]`表示第一张卡选1号位从者的宝具卡，第二张卡优先选汇呆蓝卡（如果找不到则选最左的未选卡），第三张卡直接选最左的未选卡。

截图如果不包含指令卡的背景，脚本将会选取该从者的所有卡，包括宝具。如果你想这样使用，请留意，脚本可能会误选宝具卡。请参考`/WG_level90pp.py`中第三个回合的写法，在传入字符串前先用整数`6~8`选宝具，否则脚本将重复单击宝具卡。

## 注意

脚本识别出错时，请尝试裁剪你的截图。留意截图中是否包含不必要的信息，比如指令卡截图中最好不要包含Buff、纹章图标，除非你真的需要它们。

## 更新日志

### 2024.10.17

1. 新增使用令咒充能、对敌单体技能的API
2. 现在脚本会自动用`attack([9,9,9])`填充`xjbd_handlers`，对补刀没有要求的话，不必再为每个回合手动指定补刀打法

### 2024.10.13

1. 适配任意的屏幕分辨率。现在`device`通过`adb shell wm size`获取屏幕分辨率，并计算缩放倍率。截取游戏屏幕时会调用`cv2.resize()`压缩到1280x720，输出单击和滑动时会将坐标缩放到游戏屏幕的分辨率。
2. 连接设备的时机提前到实例化`device`时，这是为了在`bot`和`device`初始化时获取屏幕分辨率。现在用户实例化`bot`时要提供本地端口。

### 2024.10.8

1. `use_skill()`新增参数`reinforce`，现在这个函数可以用于库库尔坎和水妖高3技能
2. 修改了`attack()`的逻辑，现在`attack`选平A卡有两种模式：传入参数`9`和传入字符串。传入参数`9`表示对平A卡没有要求，`attack`将会从未选卡中选出最靠左的一张。传入参数为字符串`xxxx`，`attack`将会尝试在脚本同级目录下寻找文件`xxxx.png`，然后尝试在游戏屏幕中寻找并单击它，如果尝试失败，`attack`将按照传入`9`的情况执行。
3. 增加了装饰器`@xjbd()`，其实现与原有的`@at_stage()`类似。对于关卡的每一面，脚本将在首个回合执行`@at_stage()`中的函数，如果首个回合过后没有进入关卡下一面，脚本将会执行`@xjbd()`中的函数。

### 2024.8.28	

1. 现在脚本会单击“连续出击”来跳过选择关卡和选择编队
2. 架构调整，将原`device.py` 和`tm.py`两个模块合并为新`device.py`，原模块`bot.py`中的部分函数定义移入新`device.py`，增加了一些函数。同时，对原有函数做了以下调整：
   - 原`__wait()`函数重命名为`wait_and_updateScreen()`，定义不变。新`wait()`函数的定义不同于原`__wait()`函数
   - `find()`和`probability()`合并为`match()`
   - 常量`FROM_SHELL`和`SDCARD_PULL`移到模块最外层

### 2024.8.18	在Github建立仓库

- 现在脚本使用技能后自动单击屏幕，加速动画播放
- 现在脚本可以选择助战职介，默认为“caster”
- 参考@yuezhilanyi，更新了` fgobot/images`文件夹下的图片，现在脚本可以用于当前版本的B服（简中服.版本号：2.86.1）