# STM32：DAPLink 调试与 SWD 数据采集

本仓库把 STM32 工程中容易混淆的两件事分开说明：

## 为什么整理这套方案

本项目原先使用 STM32CubeMX + VS Code 开发，但原有调试配置没有打通手上的无线 DAPLink。因此补充了 **Cortex-Debug + OpenOCD + CMSIS-DAP** 配置，使无线探针可以用于下载、断点调试和运行中内存采样。

这不表示 CubeMX + VS Code 无法无线调试：CubeMX 负责外设配置和代码生成，VS Code 需要相应调试扩展及后端。ST 的调试文档也允许使用 Cortex-Debug 等第三方扩展，见[官方说明](https://dev.st.com/stm32cube-docs/stm32cubeide-vscode/latest/en/docs/markup/development/debug.html)。

## 从这里开始

1. [无线仿真器的品牌、配对和接线](docs/03-wireless-probe.md)
2. [Windows 安装与 VS Code 无线调试教程](docs/04-setup-tutorial.md)
3. [不走串口的 SWD 读取示例](docs/05-read-memory-tutorial.md)

本例设备为**商丘爱博电子科技有限公司的 HS/FS 高速无线 DAPLink**；说明书产品图片的机身标识为 **Horco DAP_WL**，封面另有 **ABorobots** 标识。详细型号和 HS/FS 版本以实物标签为准。

仓库附有[厂家说明书](reference/wireless-daplink-manual.pdf)及可复制的 [VS Code 配置示例](examples/vscode)。

## 两种用途

| 主题 | 解决的问题 | 主要工具 |
| --- | --- | --- |
| [DAPLink 下载与程序调试](docs/01-daplink-debug.md) | 如何烧录、打断点、单步、查看变量和检查固件 | DAPLink、SWD、OpenOCD、GDB、Cortex-Debug |
| [SWD 直接采集运行数据](docs/02-swd-data-capture.md) | 如何不通过串口，直接采样位置、速度、PWM 和运行状态 | DAPLink、SWD、OpenOCD、电脑采样脚本 |

两者共用调试硬件，但用途不同。程序调试关注代码执行；运行数据采集关注变量随时间的变化。运行数据采集可以独立于 VS Code 和 GDB，通过 OpenOCD 的接口完成。

本文依据 STM32F103 水泵与转轴控制工程的配置、代码和既有测试记录整理。示例不绑定具体 RAM 地址，不包含完整控制固件或可直接运行的通用采样器。

## 项目中的两条数据路径

```text
SWD 直接读取：
电脑采样脚本 → OpenOCD → USB → DAPLink → SWD → STM32 RAM / 外设寄存器

蓝牙遥测：
STM32 USART1 → HC-05 BLE → 电脑 Python 桥接 → TCP → VOFA+
```

前一条路径不需要单片机通过串口主动发送数据。后一条路径需要固件打包发送遥测帧。

## 记录范围

工程中的早期阶跃测试脚本采用混合方式：通过 SWD 读写目标值和读取 PI 参数，通过蓝牙链路接收波形。

工程记录中的后续 5 圈运动测试采用 DAPLink 直接读回采样；记录包含位置、速度指令、实际测速值、PWM、编码器计数和硬件 CCR 等字段。不能把混合脚本直接当作纯 SWD 采样器。
