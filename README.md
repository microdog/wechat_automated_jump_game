# 自动玩微信跳一跳小游戏

利用MonkeyRunner和OpenCV在安卓设备上自动玩微信跳一跳小游戏。

## 依赖

* OpenCV
  * 安装方法：https://docs.opencv.org/3.4.0/da/df6/tutorial_py_table_of_contents_setup.html
  * Mac下Homebrew可以直接 `brew install opencv` ，然后按提示进行配置即可。
* numpy
  * 使用 `pip` 安装：`pip install numpy`
* flask
  * 使用 `pip` 安装：`pip install flask`
* monkeyrunner
  * 位于 Android SDK 中：`tools/bin/monkeyrunner`
* adb
  * 位于 Android SDK 中：`platform-tools/adb`

## 原理说明

本项目通过图像处理的方式从屏幕截图中判断棋子当前位置和目标棋盘位置。

1. 使用 Template Matching 的方式在截图中识别棋子当前位置。
1. 对截图进行边缘检测，然后在合适的区域内自上而下寻找第一个形状的顶部中心点和最右点，再计算出目标跳跃位置。
1. 计算棋子当前位置到目标跳跃位置的距离。
1. 将距离映射为按压时间。
1. 控制设备进行模拟点击操作。

## 项目结构说明

项目主要分为两部分：计算跳跃时间的服务端（`server.py`）和执行设备控制操作的客户端（目前仅有安卓MonkeyRunner脚本`monkeyrunner.py`）。

执行设备控制操作的客户端首先对设备进行截图，然后将截图通过POST方式发送到服务端的HTTP接口上，计算跳跃时间的服务端对截图进行处理并返回对应的按压时间，客户端在设备上模拟点击操作。

## 操作步骤

1. 启动计算跳跃时间的服务端：`python server.py`，服务端默认监听 `127.0.0.1:5000`。可选启动参数见 `python server.py -h`。
1. 安卓手机开启USB调试，通过USB线连接到电脑。
1. 使用ADB列出连接的安卓设备：`adb devices`，并记录设备ID如 `WTKDU1670700000`。
1. 启动MonkeyRunner：`monkeyrunner monkeyrunner.py WTKDU1670700000 http://127.0.0.1:5000`。注意将 `WTKDU1670700000` 替换为上一步记录的设备ID，如果启动服务端时修改了监听端口，则第二个参数也需要对应修改。
1. MonkeyRunner提示 `Press enter to start` 后，在微信中打开跳一跳并开始游戏，然后在MonkeyRunner中按下回车键。

## 已知问题

* 圆形和长方形的棋盘位置判断可能会有偏差，但不致命。
* 音乐盒的音符可能会干扰棋盘位置判断，致命。（已尝试修复，未确认）

## TODO

* 增加iOS脚本？
* 也许可以把服务端部署在服务器上。
* 优化性能。
* 优化圆形和长方形棋盘的处理。

## QA

### 安卓手机需要ROOT吗？

不需要ROOT。但需要电脑安装 [Android SDK](https://developer.android.com/studio/index.html#downloads)。只需要命令行工具即可，不需要`Android Studio`。

### 提示 `Broken Pipe` 该如何处理？

`Ctrl + C`退出一次MonkeyRunner再重新启动即可。

### MonkeyRunner提示 `Press enter to start` 后卡住

下载[2.5.4rc1版本的Jython](http://search.maven.org/remotecontent?filepath=org/python/jython-standalone/2.5.4-rc1/jython-standalone-2.5.4-rc1.jar)并 ***替换*** Android SDK 中 `tools/lib/jython-standalone-2.5.3.jar` 文件。
