# Windows：从安装到 VS Code 无线调试

适用范围：Windows 10/11、STM32F103、爱博 HS/FS 无线 DAPLink、CubeMX 生成的 CMake 工程。本文仓库只有文档和配置示例，不包含可单独编译的 STM32 工程。

## 1. 需要安装什么

| 软件 | 用途 | 是否必需 |
| --- | --- | --- |
| [VS Code](https://code.visualstudio.com/) | 编辑与调试界面 | 本教程必需 |
| [STM32CubeMX](https://www.st.com/en/development-tools/stm32cubemx.html) + 对应 STM32CubeF1 固件包 | 生成/维护 STM32 工程 | 已有工程且不重新生成时可不操作 |
| [STM32CubeIDE for VS Code 扩展](https://marketplace.visualstudio.com/items?itemName=stmicroelectronics.stm32-vscode-extension)及其构建工具 | 管理工具链和 CMake 构建 | 可用独立工具链替代 |
| Arm GNU Toolchain：`arm-none-eabi-gcc`、`arm-none-eabi-gdb` | 编译和调试 Cortex-M 固件 | 必需，可复用 ST 工具包中的版本 |
| CMake + Ninja | 配置并构建本例工程 | 必需，可复用 ST 工具包中的版本 |
| [Cortex-Debug](https://marketplace.visualstudio.com/items?itemName=marus25.cortex-debug) | 连接 GDB 与 OpenOCD | 本教程必需 |
| [xPack OpenOCD](https://github.com/xpack-dev-tools/openocd-xpack/releases) Windows 版本 | 驱动 CMSIS-DAP 探针并提供调试服务 | 本教程必需 |
| Python 3 | 后续 SWD 采样 | 仅运行 Python 示例时需要 |

安装编译工具有两条路径，选一条即可：

- 已在使用 ST 扩展：通过其工具管理安装 GNU 工具链、CMake、Ninja，复用它们的路径或扩展提供的构建环境。
- 使用独立工具：安装 [Arm GNU Toolchain](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads)、[CMake](https://cmake.org/download/) 和 [Ninja](https://github.com/ninja-build/ninja/releases)，将各自可执行文件目录加入当前终端的 PATH。

OpenOCD 解压时保留完整目录，包括配套 `scripts`。Windows 10+ 无需驱动是本设备说明书的描述；不代表所有 CMSIS-DAP 设备都一样。如枚举异常，先检查 USB 线、模式和厂家说明，勿直接替换整个复合 USB 设备的驱动。

本机现有组合为 GCC/GDB `14.3.1+st.2`、Ninja `1.13.2+st.1`、xPack OpenOCD `0.12.0+dev-02228`。这些是工程记录，不要求必须安装同样版本；OpenOCD 需要支持本例配置中的 `cmsis-dap quirk` 和后续 `read_memory` 命令。

Keil、IAR、HC-05、串口助手和 VOFA+ 均不是这条 SWD 调试链路的安装前提。Python 读取示例仅使用标准库，不需要 Bleak、Unicorn 或 pyelftools。

## 2. 配好硬件与 CubeMX

按[硬件教程](03-wireless-probe.md)配对主从、供电和接线，确认主机蓝灯、从机绿灯。

在 CubeMX 中选择实际芯片，SYS → Debug 选择 Serial Wire。本例使用 CMake 工程生成方式；已有工程可沿用当前 `CMakePresets.json`，不要为了调试重新覆盖应用代码。

## 3. 先确认构建成功

在 STM32 工程根目录打开终端。独立工具链的环境可检查：

```powershell
arm-none-eabi-gcc --version
arm-none-eabi-gdb --version
cmake --version
ninja --version
```

原工程使用 `Debug` 预设，对应命令：

```powershell
cmake --preset Debug
cmake --build --preset Debug
```

ST 扩展环境也可能使用 `cube-cmake` 或其构建按钮。若普通终端找不到命令，应使用扩展的工具环境或填入安装目录，不必重复安装。其他工程的预设名称和 ELF 路径以各自配置为准。

本项目生成 `build/Debug/SHUIBENG.elf`。应使用带调试信息的 Debug 固件；ELF 与烧录版本必须一致。

## 4. 复制配置

把本仓库 `examples/vscode/` 中的四个文件复制/合并到 **STM32 工程根目录的 `.vscode/`**，不要覆盖原有的其他配置。

- `daplink.cfg`：CMSIS-DAP、SWD、STM32F1 和当前探针兼容性设置。
- `launch.json`：Cortex-Debug 调试启动项；GDB 和 OpenOCD 路径通过首次启动时的输入框填写。
- `tasks.json`：调试前构建；`cmake` 不在 PATH 时改成实际可执行文件路径，ST 环境可按本机情况使用 `cube-cmake`。
- `extensions.json`：推荐安装 Cortex-Debug。

示例默认 ELF 为 `build/Debug/SHUIBENG.elf`，其他项目必须修改。填写工具路径时用 `/`，不要在输入框额外加引号。

`daplink.cfg` 沿用本工程配置：

```tcl
source [find interface/cmsis-dap.cfg]
cmsis-dap quirk enable
transport select swd
source [find target/stm32f1x.cfg]
adapter speed 100
reset_config none
```

`quirk enable` 是兼容当前探针固件、禁用命令流水的设置；100 的单位为 kHz，用于保守起步，并不等于无线空中速率。`reset_config none` 对应本例未使用硬件复位线的连接方式；其他接线不能照搬复位配置。

## 5. 启动调试

1. VS Code 打开真正的 STM32 工程根目录。
2. 打开“运行和调试”，选择 `Wireless DAPLink - STM32F103`。
3. 按 F5，填写 `arm-none-eabi-gdb.exe` 和 `openocd.exe` 的完整路径。
4. 预构建成功后，Cortex-Debug 启动 GDB 和 OpenOCD，下载程序并运行到 `main`。
5. 可查看变量、设置断点、单步和继续执行。

该项为 `launch`：会下载固件并改变目标运行状态。若只想读取正在运行的程序，使用[独立采样教程](05-read-memory-tutorial.md)，不要启动这个下载项。

电脑看到的是 USB CMSIS-DAP 接口。探针内部转发无线通信，VS Code 不需要另外输入无线 IP、蓝牙名称或串口号。

## 6. 常见问题

| 现象 | 优先检查 |
| --- | --- |
| 找不到 CMSIS-DAP | 主机是否连接电脑、USB 线是否可传数据、模式是否正确、是否有其他调试程序占用 |
| 找到探针但不能连接 STM32 | 从机配对、目标供电、共地、SWDIO/SWCLK、PA13/PA14 是否被程序占用 |
| 找不到 `interface/cmsis-dap.cfg` | OpenOCD 的 scripts 是否完整；必要时在启动配置增加 `searchDir` 指向实际 scripts 目录 |
| 不认识 `cmsis-dap quirk` | OpenOCD 构建是否过旧或不支持；换用支持该命令的版本 |
| 构建命令不存在 | 工具链/CMake/Ninja 的 PATH，或 ST 扩展的工具环境 |
| 找不到 ELF / 源码行不匹配 | 是否先完成 Debug 构建、路径是否正确、ELF 是否对应当前固件 |
| 无线不稳定 | 缩短距离、检查供电与天线、确认两端配置；可切换 usb 有线模式对比 |
| GDB 端口占用 / 探针被占用 | 关闭前一个 VS Code、Keil、OpenOCD 会话；一套探针只由一个后端占用 |

## 参考

- [ST：调试与第三方调试扩展](https://dev.st.com/stm32cube-docs/stm32cubeide-vscode/latest/en/docs/markup/development/debug.html)
- [Cortex-Debug 项目与支持的后端](https://github.com/Marus/cortex-debug)
- [OpenOCD：调试适配器配置与 CMSIS-DAP](https://openocd.org/doc/html/Debug-Adapter-Configuration.html)
- [厂家说明书](../reference/wireless-daplink-manual.pdf)

本次发布核对了原工程配置、说明书和官方资料，并检查示例格式；未对新增通用示例重新连接硬件测试。
