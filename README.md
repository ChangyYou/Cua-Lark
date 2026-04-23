# CUA-Lark Agent

让大模型像人一样操作飞书（Lark）桌面客户端。

CUA-Lark 是一个基于 **Qwen-VL** 等多模态大模型的桌面 UI 自动化智能体。它通过 **感知 (Observe) - 规划 (Plan) - 执行 (ReAct)** 的循环，将用户的自然语言指令转化为高精度的鼠标与键盘交互操作，实现飞书客户端的完全自动化驱动。

不仅如此，CUA-Lark 还具备**经验记忆**与**技能自我生长**能力，能够在不断的执行中沉淀知识，越用越聪明。

---

## ✨ 核心特性

- **🎯 高精度坐标定位**：完全摒弃传统的网格数字覆盖（Grid Overlay）方案，直接利用大模型的原生视觉能力输出相对坐标 (`x_ratio`, `y_ratio`)，显著提高小目标（如侧边栏图标、细小按钮）的点击成功率。
- **🧠 长期记忆 (Long-Term Memory)**：每次任务结束后，Agent 会自动复盘并提取通用的 UI 交互经验（例如“视频会议入口在左侧导航栏”），保存在本地 `memory.json` 中，指导未来的跨任务规划。
- **🌱 技能自动生长 (Skill Auto-Generation)**：当 Agent 成功通过“通用视觉探索”完成了一项结构化任务（如预约会议）后，它会自动将其提炼为符合 `AgentSkill` 协议的 Python 代码并持久化。下次遇到类似指令，直接无脑复用“肌肉记忆”。
- **🛡️ 高危操作拦截 (Human-in-the-loop)**：内置安全防线。当检测到用户的指令或模型预测的下一步动作涉及“删除、清空、退出、解散”等高危意图时，系统会自动挂起并请求人类用户的终端二次确认 (y/n)，拒绝执行时大模型能听懂拒绝并重新规划。
- **🔄 Plan-then-ReAct 架构**：先统揽全局生成多步计划，再在每一步执行时重新截图进行 ReAct 动态微调决策，兼顾大局观与对动态弹窗的应对能力。
- **💻 跨平台支持**：原生支持 Windows (`win32gui` / `win32process`) 与 macOS (`Quartz`) 桌面环境的窗口捕获与底层键鼠控制。

---

## 🚀 快速开始

### 1. 环境与依赖安装

建议使用 Python 3.10+。

```bash
# 克隆仓库
git clone https://github.com/your-repo/CUA-Lark.git
cd CUA-Lark

# 安装依赖 (Windows)
pip install -r requirements.txt

# 安装依赖 (macOS)
pip install -r requirements-macos.txt
```

### 2. 配置环境变量

复制环境模板文件并填入你的阿里云百炼 API Key：

```bash
cp .env.example .env
```

在 `.env` 中配置：
```env
# API 配置
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 模型配置
MODEL_IMAGE=qwen3-vl-flash      # 推荐使用 flash 兼顾速度与理解力
MODEL_TOOLS=qwen-vl-max         # ReAct 阶段需要更强的推理能力
MODEL_TEMPERATURE=0.2           # 保持低温度以确保输出 JSON 结构的稳定性
```

### 3. 运行 Agent

请确保飞书客户端已登录并处于打开状态。

```bash
# 通过命令行启动交互式 Agent
python src/app/agent.py
```

或者使用 CLI 模式：
```bash
python src/app/cli.py "帮我给张三发送明天下午开会的提醒"
```

---

## 🧠 智能体的自我进化

CUA-Lark 突破了传统 RPA 脚本需要人工维护的局限，实现了“用得越多，能力越强”。

### 1. 长期记忆提取
在复杂的应用中，某些入口藏得很深。当 Agent 经过多次试错终于找到入口并完成任务后，系统会触发 `extract_and_store_memory` 机制：
- **记录知识**：如 *“飞书日历的入口位于左侧导航栏的第 4 个图标。”*
- **经验复用**：下次执行任务时，这些记忆会作为强 Prompt 注入给大模型，避免重复试错。

### 2. Skill 自动生成
对于高频且结构化的任务（如发送消息、创建日程），如果每次都走 ReAct 视觉探索会非常慢且浪费 Token。
- **Fallback 到 Skill**：当 Agent 成功完成一项陌生的通用任务后，`skill_generator.py` 会在后台调用 LLM，分析执行历史。
- **生成代码**：如果认定为可复用模式，它会自动生成包含状态机逻辑的 Python 技能脚本，并将其保存在 `skills/` 目录下。
- **动态加载**：下次启动时，路由模型会直接命中这个新技能，按照固定链路快速执行。

---

## 🛡️ 安全与权限

### Windows
项目使用了 `win32gui` 等原生 API 来处理复杂的多窗口层级（如飞书主窗口与弹出的会议窗口），以解决焦点被抢占的问题。通常不需要特殊提权。

### macOS
为了实现屏幕捕获与键鼠模拟，你必须在 `系统设置 > 隐私与安全性` 中授予运行此 Python 脚本的终端程序（如 iTerm, VSCode 等）以下权限：
1. **辅助功能 (Accessibility)**：允许控制键盘和鼠标。
2. **屏幕录制 (Screen Recording)**：允许截取屏幕内容。

### Human-in-the-loop (高危拦截)
自动化操作最怕“视觉幻觉”导致的误删。系统内置了基于正则和意图分析的拦截器。
当触发高危动作时，终端会阻塞：
```text
⚠️ 警告：Agent 正在尝试执行 高危 操作。目标动作：click_position(x=0.850, y=0.120)
操作意图: 点击确认删除按钮
是否允许继续？(y/n) [默认 n]: 
```
如果输入 `n`，大模型会收到 `[失败] - 用户拒绝了该操作` 的反馈，并在下一轮尝试其他安全途径或终止任务。

---

## 📂 项目结构

```text
CUA-Lark/
├── data/
│   └── memory.json       # Agent 持久化的长期记忆库
├── skills/               # 技能目录 (内置与系统自动生成的 Skill)
│   └── send-message/     # 示例：发送消息技能
├── src/
│   ├── app/
│   │   ├── agent.py      # Agent 核心运行循环 (Plan-then-ReAct)
│   │   ├── skills/       # 动态技能加载注册机制
│   │   └── utils/        # LLM 交互、动作解析、记忆与技能生成工具
│   └── platforms/        # 跨平台屏幕捕获与底层键鼠驱动 (macOS/Windows)
├── Prompt/               # 系统核心 Prompt 模板
├── captures/             # 运行时的步骤截图存放处
└── requirements.txt      # 依赖清单
```

---

## 📜 License

MIT License.
