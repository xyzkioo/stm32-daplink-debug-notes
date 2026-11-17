# DAPLink 下载与程序调试

## 用了什么

- **DAPLink / CMSIS-DAP 调试探针**：把电脑侧的调试请求转换为目标芯片的 SWD 访问。
- **SWD 接口**：使用 SWDIO、SWCLK 和 GND 连接 STM32；还需按探针要求连接电压参考，复位线按连接与配置需要使用。
- **OpenOCD**：驱动探针、识别 STM32，提供烧录、内存访问和调试服务。
- **ARM GDB**：结合 ELF 调试信息进行源码调试、变量查询、断点和单步。
- **VS Code Cortex-Debug**：提供图形调试界面，连接 GDB 和 OpenOCD。
- **ARM GCC、CMake、Ninja**：把源码构建成固件和带调试信息的 ELF 文件。

## 工作链路

```text
VS Code / Cortex-Debug
        ↓
      ARM GDB ← ELF 中的符号和调试信息
        ↓
      OpenOCD
        ↓ USB / CMSIS-DAP
      DAPLink
        ↓ SWD
      STM32F103
```

ELF 告诉调试工具“变量叫什么、类型是什么、位于哪里”；SWD 提供实际访问芯片的通道。没有源码符号也能按地址访问内存，但不能方便地把地址对应回源码变量。

## 做了什么

1. 将固件写入 STM32 Flash，并进行校验。
2. 支持在源码处打断点、暂停、单步、继续执行和查看变量。
3. 读取 RAM 中的控制状态，以及定时器等外设寄存器。
4. 读取 Flash 并与预期镜像比较，排查运行的固件是否为预期版本。

本工程已有的 VS Code 配置使用 OpenOCD 服务，加载 `build/Debug/SHUIBENG.elf`，并设置运行到 `main`。探针配置选择 CMSIS-DAP、SWD 和 STM32F1 目标；工程中的适配器速度设置为 100 kHz，这是当前探针兼容性配置，不是所有探针的固定要求。

## 与运行数据采集的关系

断点和单步用于检查代码逻辑，会改变程序的运行时序。电机控制正在运行时，暂停 CPU 可能中断控制计算，而外设仍可能继续工作。

持续观察速度、位置等变化时，可使用下一篇说明中的运行中内存读取方式。它复用 DAPLink 和 OpenOCD，但不要求持续暂停 CPU，也不要求单片机增加串口发送代码。
