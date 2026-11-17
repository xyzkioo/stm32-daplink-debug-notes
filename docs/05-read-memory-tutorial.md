# 无串口回传：直接读取 RAM 的最小教程

本例在程序运行中通过 SWD 读取一个 32 位 RAM 变量，不写内存、不下载固件、不主动暂停或复位 CPU。它用于说明链路；尚未用本次新增示例重新做硬件验证。

## 1. 准备变量地址

先完成[安装与调试配置](04-setup-tutorial.md)，并确认目标上已经烧录对应固件。

使用与固件完全匹配的 ELF，通过 GDB 查询静态变量。例如本工程 `pump_app.c` 中的 `status`：

```powershell
arm-none-eabi-gdb build/Debug/SHUIBENG.elf -batch -ex "p/x &'pump_app.c'::status"
```

如需结构体内字段地址，可在 GDB 中使用相应字段的地址表达式，例如 `p/x &'pump_app.c'::status.position_counts`。文件限定用于区分不同源码里的同名静态变量；具体命令以 ELF 中可见的符号为准。

全局变量可以直接查询变量名。记下实际地址与类型；不要使用其他固件的地址。若变量被优化掉，需要改用有稳定存储位置的状态变量或对应调试构建。

## 2. 单独启动 OpenOCD

先退出 VS Code 的调试会话，再在 STM32 工程根目录启动下面这个服务。不要让两个 OpenOCD 同时占用同一探针。

```powershell
& 'D:/Tools/OpenOCD/bin/openocd.exe' -f .vscode/daplink.cfg -c 'bindto 127.0.0.1' -c 'gdb_port 3333' -c 'tcl_port 50001' -c 'telnet_port disabled' -c init
```

工具安装目录不同就修改路径。这里没有 `reset`、`halt` 或 `program` 命令；目标必须已运行。观察日志确认目标识别成功，且 Tcl RPC 监听 `50001`。

## 3. 用 Python 读取

仓库提供 [read_memory.py](../examples/read_memory.py)，只用 Python 标准库，无需 `pip install`。下方 `$ramAddress` 必须换成第 1 步确认的真实 RAM 地址，不可原样使用占位符。

```powershell
$ramAddress = '替换成当前固件的RAM地址'
python examples/read_memory.py --address $ramAddress --type i32 --samples 100 --interval 0.05 --output capture.csv
```

此命令在本教程仓库根目录执行，OpenOCD 保持在另一个终端运行。变量是浮点数时使用 `--type f32`；无符号 32 位整数使用 `--type u32`。不要用来轮询未确认语义的外设寄存器。

脚本检查目标处于 `running` 状态后读取；默认 100 次采样。`--interval 0.05` 是电脑希望维持的采样间隔，实际链路较慢时会延长。CSV 保留主机相对时间，不把它当作 MCU 精确采样时间。

## 4. 数据如何到电脑

```text
Python socket → 本机 OpenOCD Tcl RPC → USB 主机 → 无线链路 → 从机 SWD → STM32 RAM
```

OpenOCD `read_memory` 返回 32 位原始数值，脚本按选择的类型解析并写 CSV。因此即使没有接 STM32 的 UART TX/RX，也能读取 RAM 中的状态。

需要更多通道时，应根据当前 ELF 布局扩展读取范围。多个字段不是天然同时快照；需要同步数据时，可先由固件组织带序号的快照，再通过 SWD 读取。

参考：[OpenOCD Tcl RPC 协议](https://openocd.org/doc/html/Tcl-Scripting-API.html)。
