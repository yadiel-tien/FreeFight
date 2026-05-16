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
   git clone https://github.com/yourusername/FreeFight.git
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

### Architecture Overview
- **Scene Management:** State-driven system for handling game transitions.
- **Input System:** Abstracted controller logic for keyboards and joysticks.
- **Player Entities:** Sprite-based players with physics and animation state machines.
- **Support Utilities:** Centralized resource loading for consistent asset pathing.

### Development
- **Adding Characters:** Drop new graphics into `assets/graphics/sprites/<name>/` and update logic in `src/entities/player.py`.
- **Custom Scenes:** Inherit from `Scene` in `src/scenes/scene.py` and register in `src/main.py`.

### Tools
- `tools/joystick_test.py`: Utility to test gamepad connections and mappings.

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
   git clone https://github.com/yourusername/FreeFight.git
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

### 架构概览
- **场景管理：** 驱动游戏状态转换的系统。
- **输入系统：** 抽象的键盘和手柄控制逻辑。
- **角色实体：** 具有物理效果和动画状态机的精灵类。
- **支撑工具：** 用于统一资源路径加载的工具类。

### 开发指南
- **添加角色：** 将新的图形资源放入 `assets/graphics/sprites/<name>/` 并更新 `src/entities/player.py` 中的逻辑。
- **自定义场景：** 继承 `src/scenes/scene.py` 中的 `Scene` 类并在 `src/main.py` 中注册。

### 辅助工具
- `tools/joystick_test.py`: 用于测试手柄连接和按键映射的实用程序。

---

## License
[Your chosen license, e.g., MIT]
