# FreeFight

[English](#english) | [简体中文](#简体中文)

---

<a name="english"></a>
## English

FreeFight is a 2D fighting game built with Python and the Pygame library. It features a modular scene-based architecture, supporting multiple players with both keyboard and gamepad controllers.

### Features
- **Modular Scene System:** Easily switch between Main Menu, Character Selection, and Combat Arena.
- **Unified Input Handling:** Supports keyboard and various gamepads with hot-plugging.
- **Dynamic Player Mechanics:** Complex state-based logic for movement, attacks, and special moves.
- **Rich Animations:** Smooth frame-based animations extracted from GIFs.
- **Multiplayer:** Local multiplayer support for up to 4 players.
- **Visual Hitbox & Stats Editor:** A highly responsive developer/designer tool to visually draw, edit, and auto-save collision boxes (Hurtbox, Hitbox, Pushbox), customize character physical stats, and tweak combat move parameters in real time.

### Key Technologies
- **Python 3**
- **Pygame:** Core game engine.
- **Pillow (PIL):** Asset processing and GIF frame extraction.

### Getting Started

#### Prerequisites
- Python 3.x
- Pygame
- Pillow

#### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yadiel-tien/FreeFight.git
   cd FreeFight
   ```
2. Set up a virtual environment (recommended):
   - **Windows:**
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install pygame Pillow
   ```

#### Running the Game
To start the game as a module (recommended), run the following command from the root directory:
```bash
python -m src.main
```

#### Running the Editor
To start the visual hitbox and stats editor, run the game with the `--editor` or `-e` flag:
```bash
python -m src.main --editor
# or
python -m src.main -e
```

### Visual Hitbox & Stats Editor

FreeFight includes a highly responsive, designer-friendly visual tool to tweak character physics, combat frame hitboxes, and action parameters in real time.

#### Hotkeys & Canvas Controls
- **1 / 2 / 3:** Switch active box drawing mode (1: Hurtbox 🟢, 2: Hitbox 🔴, 3: Pushbox 🔵)
- **Mouse Left Drag:** Draw the box directly on the active character frame (autosaves on release)
- **A / D (or Left / Right Arrow):** Navigate between animation frames
- **W / S (or Up / Down Arrow):** Cycle through different action states (e.g. idle, attack, jump)
- **C / DELETE:** Clear the selected box type on the current frame
- **R:** Sync/Copy the current box configuration to all frames of this action
- **F:** Flip character orientation (mirroring)
- **B:** Toggle UI Theme Mode (Cyber Dark Grid / Daylight Light Grid)
- **Ctrl + S (or Cmd + S):** Manually save configurations (in addition to auto-save)
- **ESC:** Cancel active drawing or open the exit confirmation modal (Enter/Y to exit, ESC/N to cancel)

#### Inspector Panel Tabs
- **Move Stats:** Micro-adjust combat properties (Damage, Knockback, MP Cost, Startup time, Recovery frames) for specific combat action moves.
- **Base Stats:** Customize global character physics (Max Health, Speed, Gravity, Jump Strength).
- **Quick Help:** Interactive on-screen list of all shortcut keys.

### Architecture Overview
- **Scene Management:** State-driven system for handling game transitions.
- **Input System:** Abstracted controller logic for keyboards and joysticks.
- **Player Entities:** Sprite-based players with physics and animation state machines.
- **Support Utilities:** Centralized resource loading for consistent asset pathing.

### Development
- **Adding Characters:** Drop new graphics into `assets/graphics/sprites/<name>/` and update logic in `src/entities/player.py`.
- **Custom Scenes:** Inherit from `Scene` in `src/scenes/scene.py` and register in `src/main.py`.

~

---

<a name="简体中文"></a>
## 简体中文

FreeFight 是一款使用 Python 和 Pygame 库开发的 2D 格斗游戏。它具有模块化的场景架构，支持使用键盘和手柄进行多玩家对战。

### 核心特性
- **模块化场景系统：** 在主菜单、角色选择和战斗场景之间轻松切换。
- **统一的输入处理：** 支持键盘和多种型号的手柄，并支持热插拔。
- **动态角色机制：** 复杂的基于状态的移动、攻击和特殊技能逻辑。
- **丰富的动画：** 从 GIF 中提取的平滑帧动画。
- **多玩家对战：** 支持最多 4 人的本地对战。
- **可视化碰撞与属性编辑器：** 支持可视化绘制与自动保存碰撞盒（受击盒、攻击盒、推挤盒），并在右侧 Inspector 面板实时微调角色物理属性和招式数值参数。

### 关键技术
- **Python 3**
- **Pygame:** 核心游戏引擎。
- **Pillow (PIL):** 资源处理和 GIF 帧提取。

### 快速开始

#### 环境要求
- Python 3.x
- Pygame
- Pillow

#### 安装步骤
1. 克隆仓库：
   ```bash
   git clone https://github.com/yadiel-tien/FreeFight.git
   cd FreeFight
   ```
2. 创建并激活虚拟环境（推荐）：
   - **Windows:**
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. 安装依赖：
   ```bash
   pip install pygame Pillow
   ```

#### 运行游戏
推荐以模块方式启动游戏，在根目录下运行以下命令：
```bash
python -m src.main
```

#### 运行编辑器
若要启动可视化碰撞与数值属性编辑器，只需在启动命令后添加 `--editor` 或 `-e` 参数：
```bash
python -m src.main --editor
# 或
python -m src.main -e
```

### 可视化碰撞与属性编辑器

FreeFight 包含一个功能丰富且极具极客风的可视化编辑器，允许开发者和设计师实时调整角色物理参数、格斗帧碰撞范围以及招式细节。

#### 快捷键与画布操作
- **数字键 1 / 2 / 3：** 切换当前编辑的碰撞盒类型（1: 受击盒 Hurtbox 🟢, 2: 攻击盒 Hitbox 🔴, 3: 推挤盒 Pushbox 🔵）
- **鼠标左键拖拽：** 直接在中央角色帧画布上框选绘制碰撞范围（鼠标松开时会自动保存）
- **A / D (或 方向键 左 / 右)：** 切换当前动作的上一帧/下一帧
- **W / S (or 方向键 上 / 下)：** 切换上一动作/下一动作状态（如 idle, attack, jump 等）
- **C / DELETE：** 清除当前帧中选中的碰撞盒类型
- **R 键：** 快速复制当前碰撞盒配置到该动作的所有帧，并伴随自动保存及轻量级弹窗提示
- **F 键：** 镜像翻转角色朝向
- **B 键：** 切换编辑器整体界面主题（Cyber 深黑网格 / 舒适白昼灰网格）
- **Ctrl + S (或 Cmd + S)：** 手动保存修改（所有操作均支持自动保存）
- **ESC 键：** 取消当前框选绘制，或调出半透明退出确认弹窗（Enter/Y 确定退出，ESC/N 取消）

#### 右侧属性检查器 (Inspector) 选项卡
- **招式属性 (Move Stats)：** 实时微调特定战斗招式的核心参数（如伤害、击退距离、耗能、前摇时间、收招硬直时间）。
- **角色属性 (Base Stats)：** 动态配置角色全局物理特性（如最大生命值、移动速度、重力加速度、跳跃高度）。
- **快捷指令 (Help Tab)：** 内置按键快捷指南，方便随时查询。

### 架构概览
- **场景管理：** 驱动游戏状态转换的系统。
- **输入系统：** 抽象的键盘和手柄控制逻辑。
- **角色实体：** 具有物理效果和动画状态机的精灵类。
- **支撑工具：** 用于统一资源路径加载的工具类。

### 开发指南
- **添加角色：** 将新的图形资源放入 `assets/graphics/sprites/<name>/` 并更新 `src/entities/player.py` 中的逻辑。
- **自定义场景：** 继承 `src/scenes/scene.py` 中的 `Scene` 类并在 `src/main.py` 中注册。



---

## License
[Your chosen license, e.g., MIT]
