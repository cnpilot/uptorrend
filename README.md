# Unregistered-Torrents

很多人利用IRSSI刷各种站点时，如果设置0延迟，经常会遇到unregistered torrents,尤其是
刷各种0-day站点，如果等客户端自动刷新，那可是30分钟的间隔…… 而设置延迟一般也得
40S多，这时候效率就低很多了。
那么有没办法解决这个trackers更新时间呢？ 相信很多人如果在电脑前， R某种子出现
“Unregistered Torrents”手动使用update trackers能解决， 但不可能一直在电脑前盯着，所以
下面介绍一种脚本自动帮你完成。
条件：
Root权限
需要软件：
Deluge的插件Execute-1.3-py2.7 + update-tracker.py + 小脚本

上面是需要用的脚本， 使用以上脚本需要上述提到的2个软件，一个是Deluge的插件
Execute-1.3-py2.7,另外个是update-tracker.py
把update-tracker.py移动到deluge的commands目录下， 一般位置是：
/usr/lib/python2.7/dist-packages/deluge-1.3.14-py2.7.egg/deluge/ui/console/commands
然后在deluge里安装插件 Execute, 之后按如图设置：
Command那里输入： sh 你脚本的位置， 我是放到根目录，所以是 sh ~/update.sh
原理就是每次一添加某种子，会自动扫描tracker_status，如果出现"unregistered torrents"就
会利用脚本刷新。
