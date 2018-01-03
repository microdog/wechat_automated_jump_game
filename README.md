# 自动玩微信跳一跳小游戏

利用MonkeyRunner（WebDriverAgent）和OpenCV在Android（iOS）设备上自动玩微信跳一跳小游戏。

效果：http://t.cn/RH939gQ

## 依赖

### 运行服务端

* Python
  * 版本 >= 2.7 或 >= 3.4
* OpenCV
  * 安装方法：https://docs.opencv.org/3.4.0/da/df6/tutorial_py_table_of_contents_setup.html
  * Mac下Homebrew可以直接 `brew install opencv` ，然后按提示进行配置即可
* 其它依赖
  * 使用 `pip` 安装：`pip install -U -r requirements_server.txt`

### 控制Android设备

* monkeyrunner
  * 位于 Android SDK 中：`tools/bin/monkeyrunner`
* adb
  * 位于 Android SDK 中：`platform-tools/adb`

### 控制iOS设备

* requests
  * 仅当使用WebDriverAgent在iOS上运行时需要安装
  * 使用 `pip` 安装：`pip install -U -r requirements_wda.txt`
* WebDriverAgent
  * https://github.com/facebook/WebDriverAgent

## 原理说明

本项目通过图像处理的方式从屏幕截图中判断棋子当前位置和目标棋盘位置。

1. 使用 Template Matching 的方式在截图中识别棋子当前位置。
1. 对截图进行边缘检测，然后在合适的区域内自上而下寻找第一个形状的顶部中心点和最右点，再计算出目标跳跃位置。
1. 计算棋子当前位置到目标跳跃位置的距离。
1. 将距离映射为按压时间。
1. 控制设备进行模拟点击操作。

## 项目结构说明

项目主要分为两部分：计算跳跃时间的服务端（`server.py`）和执行设备控制操作的客户端，分为控制Android设备的MonkeyRunner脚本（`monkeyrunner.py`）和控制iOS设备的WDA脚本（`wda.py`）。

执行设备控制操作的客户端首先对设备进行截图，然后将截图通过POST方式发送到服务端的HTTP接口上，计算跳跃时间的服务端对截图进行处理并返回对应的按压时间，客户端在设备上模拟点击操作。

## 操作步骤

### Android

1. 启动计算跳跃时间的服务端：`python server.py`，服务端默认监听 `127.0.0.1:5000`。可选启动参数见 `python server.py -h`。
1. Android手机开启USB调试，通过USB线连接到电脑。
1. 使用ADB列出连接的Android设备：`adb devices`，并记录设备ID如 `WTKDU1670700000`。
1. 启动MonkeyRunner：`monkeyrunner monkeyrunner.py WTKDU1670700000 http://127.0.0.1:5000`。注意将 `WTKDU1670700000` 替换为上一步记录的设备ID，如果启动服务端时修改了监听端口，则第二个参数也需要对应修改。
1. MonkeyRunner提示 `Press enter to start` 后，在微信中打开跳一跳并开始游戏，然后在MonkeyRunner中按下回车键。

### iOS

1. 启动计算跳跃时间的服务端：`python server.py`，服务端默认监听 `127.0.0.1:5000`。可选启动参数见 `python server.py -h`。
1. 在手机上启动 `WebDriverAgentRunner`，并记录设备URL如 `http://10.0.0.100:8100` 。
1. 启动脚本：`python wda.py http://10.0.0.100:8100 http://127.0.0.1:5000`。注意将 `http://10.0.0.100:8100` 替换为上一步记录的设备ID，如果启动服务端时修改了监听端口，则第二个参数也需要对应修改。
1. 提示 `Press enter to start` 后，在微信中打开跳一跳并开始游戏，然后在脚本中按下回车键。

## 幺蛾子

本项目做了以下幺蛾子操作。

### 人工增加随机跳跃误差

`monkeyrunner.py` 和 `wda.py` 均接受 `--jitter JITTER` 参数，若设置该值，则会将控制设备按压的时间乘以 `[1 - JITTER, 1 + JITTER]` 区间内的随机值。可以先尝试 `0.01` 然后再根据效果调整。

### 随机跳跃间隔

两次跳跃间的等待时间为固定 `1.75s` 加 `0.5s` 内的随机值。

## 已知问题

* iOS下WDA截图有损，杂噪点可能会影响位置判断，但应该不致命。有解决方法，见QA。
* iOS下可能需要微调长按时间的修正系数（wda.py文件中的 `CORRECTION_RATIO` 变量）。
* 距离到时间的映射大概也许可能是有问题的（calculate_time函数）。必要的话可以自己微调里面的系数，或者干脆重写这个函数。
* 圆形和长方形的棋盘位置判断可能会有偏差，但不致命。
* 音乐盒的音符可能会干扰棋盘位置判断，致命。（已尝试修复，未确认）

## TODO

* ~~增加iOS脚本？~~
* ~~也许可以把服务端部署在服务器上。~~
* ~~优化性能。~~
* 进一步优化性能。
* 优化圆形和长方形棋盘的处理。

## FAQ

### Android手机需要ROOT吗？

不需要ROOT。但需要电脑安装 [Android SDK](https://developer.android.com/studio/index.html#downloads)。只需要命令行工具即可，不需要`Android Studio`。

### 提示 `Broken Pipe` 该如何处理？

`Ctrl + C`退出一次MonkeyRunner再重新启动即可。

### MonkeyRunner提示 `Press enter to start` 后卡住

下载[2.5.4rc1版本的Jython](http://search.maven.org/remotecontent?filepath=org/python/jython-standalone/2.5.4-rc1/jython-standalone-2.5.4-rc1.jar)并 ***替换*** Android SDK 中 `tools/lib/jython-standalone-2.5.3.jar` 文件。

### 会不会被封号？

这个……封号应该是不会的，并没有对微信做任何的hack。不过删榜倒是有可能的。另外刷分太多会没朋友喔。

### 可以多个设备同时操作吗？

可以，开一个服务端和多个MonkeyRunner即可。

### iOS上运行时定位不准或服务端有大量 `Ignored shape` 提示

是WDA默认截图为有损格式所致。可以自行修改代码 [WebDriverAgentLib/Categories/XCUIDevice+FBHelpers.m](https://github.com/mykola-mokhnach/WebDriverAgent/blob/6a9b497/WebDriverAgentLib/Categories/XCUIDevice+FBHelpers.m#L64) 中 `- (NSData *)fb_screenshotWithError:(NSError*__autoreleasing*)error` 函数里 `quality` 变量值为 `0` 。但可能会导致不稳定，原因见该变量注释。
