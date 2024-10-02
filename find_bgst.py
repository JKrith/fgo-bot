from fgobot import bot


finding = bot.BattleBot(
    quest= 'qp.png',
    friend= 'friend_bgst.png',
    friend_class= 'archer'
)
# 检查设备是否连接
if not finding.device.connected():
        
    # 如果没有连接，则尝试通过本地端口62001连接（具体参数请参考自己的设备/模拟器）
    finding.device.connect('127.0.0.1:16384')
finding.select_friend()