# 上班鼓励器

一款 Windows 桌面悬浮小工具：实时计算你今天已经赚了多少钱、距离下班还有多久，
用不断跳动的数字给搬砖的你一点甜头。

## 功能一览

- **实时赚钱计时器**：按设定时薪实时计算今日已赚金额，精确到小数点后 4 位，数字持续跳动（每 100ms 刷新）。
- **下班倒计时**：显示距离下班的「X小时X分X秒」，支持夜班跨天；非工作日自动显示休息提示。
- **工作进度**：进度条展示今日已工作时长 / 目标工时及完成百分比。
- **收入统计**：时薪（或月薪折算）、每秒收入、今日收入、本月累计；可打开历史记录查看每天工时与收入、本月与全部合计。
- **打卡管理**：上班打卡 / 暂停休息 / 继续工作 / 下班打卡，同一天可多次打卡，时间自动累加。
- **个性化设置**：收入类型（时薪 / 月薪，月薪按「月均工作日 × 每日工时」自动折算）、每日目标工时、上下班时间、工作日（周一~周日）、浅色/深色主题、窗口置顶。
- **趣味鼓励**：随机展示「再过 2小时53分，一件T恤就赚回来了」这类消息，每 15 秒自动更换。
- **托盘常驻**：关闭/最小化即收到系统托盘，双击托盘图标恢复；托盘菜单可直接打卡或退出。

## 运行

### 方式一：源码运行

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe run.py
```

### 方式二：打包成 exe（无需 Python 即可运行）

```bat
build_exe.bat
```

或手动：

```bat
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe build_exe.py
```

产物为 `dist\上班鼓励器.exe`，单文件、免安装，双击即可运行。

## 数据与准确性

- 所有数据保存在本地：`%APPDATA%\WorkEncourager\`（`settings.json` 设置、`state.json` 状态与历史），原子写入，重启后无缝恢复。
- 计时只累计「上班中且程序在运行」的真实时间：
  - 暂停休息、下班打卡后立即停止累计；
  - 电脑休眠 / 睡眠期间的时间通过 wall-clock 与 monotonic 双时钟差检测并丢弃；
  - 单次心跳增量上限 30 秒兜底，杜绝关机、改系统时间导致的错误累计；
  - 累计值每 5 秒落盘一次，程序异常退出最多丢失 5 秒。
- 跨天自动归档：昨日数据写入历史记录，新的一天从零开始。
- 历史记录按各天结算时的时薪保存；修改时薪立即影响今日显示。

## 项目结构

```
run.py                  # 启动入口
build_exe.py            # PyInstaller 打包脚本
build_exe.bat           # 一键打包（自动建 venv）
requirements.txt
work_encourager/
    main.py             # QApplication 装配
    window.py           # 主悬浮窗（无边框、拖动、置顶、托盘）
    dialogs.py          # 设置 / 历史记录对话框
    tracker.py          # 计时与收入引擎（双时钟校准、跨天归档）
    storage.py          # JSON 持久化（原子写入）
    messages.py         # 趣味鼓励语
    theme.py            # 浅色 / 深色主题样式
    icon.py             # 程序图标动态绘制
    config.py           # 常量与路径
assets/icon.ico         # 应用图标
tests/
    test_tracker.py     # 引擎单元测试（python tests/test_tracker.py）
    smoke_gui.py        # GUI 冒烟测试（offscreen 双主题）
tools/gen_icon.py       # 重新生成 icon.ico
```

## 常见问题

- **关掉窗口会丢数据吗？** 不会。关闭只是最小化到托盘，计时照常；退出请在托盘菜单选「退出」。
- **电脑休眠会多算钱吗？** 不会，休眠期间的时间会被自动丢弃。
- **为什么金额不动了？** 检查是否处于「休息中」或「未上班」状态，点「继续工作 / 上班打卡」即可。
- **换电脑迁移数据？** 拷贝 `%APPDATA%\WorkEncourager\` 整个目录即可。
