import pygame
from collections import deque
from src.core.timer import Timer
from src.core.input_config import JOYSTICK_LABELS, UI_MAPPING

class InputAction:
    """封装单个动作的状态"""
    def __init__(self):
        self.pressed = False        # 当前是否按住
        self.just_pressed = False   # 这一帧是否刚按下
        self.just_released = False  # 这一帧是否刚松开
        self.hold_frames = 0        # 按住了多少帧

    def update(self, is_down: bool):
        if is_down:
            if not self.pressed:
                self.just_pressed = True
            self.pressed = True
            self.hold_frames += 1
        else:
            if self.pressed:
                self.just_released = True
            self.pressed = False
            self.hold_frames = 0

    def reset_transients(self):
        """每帧末尾调用，清除瞬时状态"""
        self.just_pressed = False
        self.just_released = False

class Controller:
    def __init__(self):
        self.battle_actions = ['up', 'down', 'left', 'right', 'jump', 'attack', 'super move 1', 'super move 2', 'finisher']
        self.ui_actions = ['up', 'down', 'left', 'right', 'tab_left', 'tab_right', 'confirm', 'cancel', 'menu']
        
        # 统一动作字典
        all_action_names = set(self.battle_actions + self.ui_actions)
        self.actions = {name: InputAction() for name in all_action_names}
        
        # 命令缓冲区 (动作名, 时间戳)
        self.buffer = deque(maxlen=30)
        
        self.action_map = {}
        self.running_dir = None # 记录当前跑动方向: 'left', 'right' 或 None
        self.last_released_key = '' 

    def update(self, event: pygame.event.Event) -> None:
        pass

    def update_state(self, dt: float) -> None:
        pass

    def post_update(self):
        """每帧末尾清除瞬时状态"""
        for action in self.actions.values():
            action.reset_transients()

    def performed(self, action: str) -> bool:
        """兼容旧代码：返回动作是否被执行"""
        # 1. 跑动状态判定 (方向一致且处于跑动锁中)
        if action == 'run left': return self.actions['left'].pressed and self.running_dir == 'left'
        if action == 'run right': return self.actions['right'].pressed and self.running_dir == 'right'
        
        # 2. 处理瞬时触发动作
        if action in ['jump', 'attack', 'super move 1', 'super move 2', 'finisher']:
            return self.actions[action].just_pressed
            
        # 3. 处理持续按住动作 (方向键/普通走路)
        if action in self.actions:
            return self.actions[action].pressed
            
        return False

    def ui_performed(self, action: str) -> bool:
        if action in ['up', 'down', 'left', 'right']:
            return self.actions[action].pressed
        if action in self.actions:
            return self.actions[action].just_pressed
        return False

    def refresh_map(self):
        pass

    def release_all(self):
        for action in self.actions.values():
            action.update(False)
        self.running_dir = None

    def _add_to_buffer(self, action_name: str):
        """记录动作到缓冲区，并检测双击跑动"""
        now = pygame.time.get_ticks()
        self.buffer.append((action_name, now))
        
        if action_name in ['left', 'right']:
            # 向前回溯查找同方向的最近一次按下
            for i in range(len(self.buffer) - 2, -1, -1):
                act, ts = self.buffer[i]
                if act == action_name:
                    if now - ts < 300: 
                        self.running_dir = action_name
                    break

    def check_sequence(self, sequence: list, window_ms=500) -> bool:
        if not sequence: return False
        now = pygame.time.get_ticks()
        buf_idx = len(self.buffer) - 1
        for action_needed in reversed(sequence):
            found = False
            while buf_idx >= 0:
                act, ts = self.buffer[buf_idx]
                buf_idx -= 1
                if now - ts > window_ms: return False
                if act == action_needed:
                    found = True
                    break
            if not found: return False
        return True

class KeyBoard(Controller):
    def __init__(self):
        super().__init__()
        self.name_to_key = {
            'a': pygame.K_a, 'b': pygame.K_b, 'c': pygame.K_c, 'd': pygame.K_d, 'e': pygame.K_e,
            'f': pygame.K_f, 'g': pygame.K_g, 'h': pygame.K_h, 'i': pygame.K_i, 'j': pygame.K_j,
            'k': pygame.K_k, 'l': pygame.K_l, 'm': pygame.K_m, 'n': pygame.K_n, 'o': pygame.K_o,
            'p': pygame.K_p, 'q': pygame.K_q, 'r': pygame.K_r, 's': pygame.K_s, 't': pygame.K_t,
            'u': pygame.K_u, 'v': pygame.K_v, 'w': pygame.K_w, 'x': pygame.K_x, 'y': pygame.K_y,
            'z': pygame.K_z, '0': pygame.K_0, '1': pygame.K_1, '2': pygame.K_2, '3': pygame.K_3,
            '4': pygame.K_4, '5': pygame.K_5, '6': pygame.K_6, '7': pygame.K_7, '8': pygame.K_8, '9': pygame.K_9,
            '[': pygame.K_LEFTBRACKET, ']': pygame.K_RIGHTBRACKET, ';': pygame.K_SEMICOLON,
            '\'': pygame.K_QUOTE, ',': pygame.K_COMMA, '.': pygame.K_PERIOD, '/': pygame.K_SLASH,
            '\\': pygame.K_BACKSLASH, '-': pygame.K_MINUS, '=': pygame.K_EQUALS, '`': pygame.K_BACKQUOTE,
            'space': pygame.K_SPACE, 'return': pygame.K_RETURN, 'escape': pygame.K_ESCAPE, 'backspace': pygame.K_BACKSPACE,
            'tab': pygame.K_TAB, 'left shift': pygame.K_LSHIFT, 'right shift': pygame.K_RSHIFT,
            'left ctrl': pygame.K_LCTRL, 'right ctrl': pygame.K_RCTRL, 'left alt': pygame.K_LALT, 'right alt': pygame.K_RALT,
            'page up': pygame.K_PAGEUP, 'page down': pygame.K_PAGEDOWN, 'home': pygame.K_HOME, 'end': pygame.K_END,
            'insert': pygame.K_INSERT, 'delete': pygame.K_DELETE, 'up': pygame.K_UP, 'down': pygame.K_DOWN,
            'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'm': pygame.K_m
        }
        self.refresh_map()
        ui_map = UI_MAPPING['keyboard']
        self.ui_action_to_key = {action: self.name_to_key.get(label, pygame.K_UNKNOWN) for action, label in ui_map.items()}

    def refresh_map(self):
        from src.core.config import config
        saved_keys = config.get('controls', 'keyboard')
        self.action_map = {a: self.name_to_key.get(saved_keys.get(a, '').lower(), pygame.K_UNKNOWN) for a in self.battle_actions}
        self.release_all()

    def update(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            target_actions = []
            for action, key in self.action_map.items():
                if event.key == key: target_actions.append(action)
            for action, key in self.ui_action_to_key.items():
                if event.key == key: target_actions.append(action)
            
            for action in set(target_actions):
                if not self.actions[action].pressed:
                    self.actions[action].update(True) # 抢先更新状态，防止 update_state 重复触发
                    self._add_to_buffer(action)

    def update_state(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        action_states = {name: False for name in self.actions.keys()}
        for action, key in self.action_map.items():
            if key != pygame.K_UNKNOWN and keys[key]: action_states[action] = True
        for action, key in self.ui_action_to_key.items():
            if key != pygame.K_UNKNOWN and keys[key]: action_states[action] = True
        
        for action, is_down in action_states.items():
            prev_pressed = self.actions[action].pressed
            self.actions[action].update(is_down)
            
            if self.actions[action].just_pressed:
                if action in ['left', 'right', 'up', 'down']:
                    self._add_to_buffer(action)
            
            if not is_down and prev_pressed:
                if action == self.running_dir:
                    self.running_dir = None

class Joystick(Controller):
    def __init__(self, joystick: pygame.joystick.JoystickType):
        super().__init__()
        self.joystick = joystick
        self.button_count = joystick.get_numbuttons()
        self.axis_count = joystick.get_numaxes()
        self.name = joystick.get_name().lower()
        if any(kw in self.name for kw in ['ps', 'dualshock', 'dualsense', 'wireless controller']): self.type = 'ps'
        elif any(kw in self.name for kw in ['nintendo', 'switch', 'joy-con']): self.type = 'nintendo'
        else: self.type = 'xbox'
        self.button_labels = JOYSTICK_LABELS.get(self.type, JOYSTICK_LABELS['xbox'])
        self.label_to_id = {label: btn_id for btn_id, label in self.button_labels.items()}
        ui_map = UI_MAPPING.get(self.type, UI_MAPPING['xbox'])
        self.ui_action_to_id = {action: self.label_to_id.get(label) for action, label in ui_map.items()}
        self.min_limit = 0.22 
        self.refresh_map()

    def get_button_name(self, button_id: int) -> str:
        if button_id is None: return "---"
        res = self.button_labels.get(button_id)
        return res if res else f"BTN {button_id}"

    def refresh_map(self):
        from src.core.config import config
        saved_keys = config.get('controls', 'joystick')
        self.action_map = {a: saved_keys.get(a) for a in self.battle_actions}
        self.release_all()

    def update(self, event: pygame.event.Event) -> None:
        if event.type == pygame.JOYBUTTONDOWN:
            for action, btn_id in self.action_map.items():
                if event.button == btn_id:
                    if not self.actions[action].pressed:
                        self.actions[action].update(True)
                        self._add_to_buffer(action)
        elif event.type == pygame.JOYAXISMOTION:
            pass 

    def update_state(self, dt: float) -> None:
        action_states = {name: False for name in self.actions.keys()}
        
        # 1. 摇杆轴输入 (Analog Sticks)
        h_axis = self.joystick.get_axis(0) if self.axis_count > 0 else 0
        v_axis = self.joystick.get_axis(1) if self.axis_count > 1 else 0
        if h_axis < -self.min_limit: action_states['left'] = True
        if h_axis > self.min_limit: action_states['right'] = True
        if v_axis < -self.min_limit: action_states['up'] = True
        if v_axis > self.min_limit: action_states['down'] = True

        # 2. 十字键 Hat 输入 (D-Pad via Pygame Hats)
        if self.joystick.get_numhats() > 0:
            hat = self.joystick.get_hat(0)
            if hat[0] == -1: action_states['left'] = True
            if hat[0] == 1: action_states['right'] = True
            if hat[1] == 1: action_states['up'] = True
            if hat[1] == -1: action_states['down'] = True

        # 3. 备用方向按钮输入 (Backup Buttons for D-Pad, e.g. on Switch/PS/Xbox)
        if self.button_count > 14:
            if self.joystick.get_button(13): action_states['left'] = True
            if self.joystick.get_button(14): action_states['right'] = True
            if self.joystick.get_button(11): action_states['up'] = True
            if self.joystick.get_button(12): action_states['down'] = True

        for action, btn_id in self.action_map.items():
            if btn_id is not None and btn_id < self.button_count:
                if self.joystick.get_button(btn_id): action_states[action] = True
        for action, btn_id in self.ui_action_to_id.items():
            if btn_id is not None and btn_id < self.button_count:
                if self.joystick.get_button(btn_id): action_states[action] = True

        for action, is_down in action_states.items():
            prev_pressed = self.actions[action].pressed
            self.actions[action].update(is_down)
            if self.actions[action].just_pressed:
                if action in ['left', 'right', 'up', 'down']:
                    self._add_to_buffer(action)
            if not is_down and prev_pressed:
                if action == self.running_dir:
                    self.running_dir = None

class GameInput:
    def __init__(self):
        pygame.joystick.init()
        self.controllers: dict[int, dict[str, any]] = {
            -1: {
                'player_index': 'p0', 
                'player_name': 'unselected', 
                'controller': KeyBoard(), 
                'timer': Timer(200), 
                'confirmed': False
            }
        }

    def refresh_all_maps(self):
        for device_info in self.controllers.values():
            device_info['controller'].refresh_map()

    def update(self, event) -> None:
        self.check_hot_plugging(event)
        if hasattr(event, 'key'):
            self.controllers[-1]['controller'].update(event)
        iid = -2 
        if hasattr(event, 'instance_id'): iid = event.instance_id
        elif hasattr(event, 'joy'): 
            try: iid = pygame.joystick.Joystick(event.joy).get_instance_id()
            except: pass
        if iid in self.controllers:
            self.controllers[iid]['controller'].update(event)

    def update_timers(self, dt):
        for device_info in self.controllers.values():
            device_info['timer'].update()
            device_info['controller'].update_state(dt)

    def post_update(self):
        for device_info in self.controllers.values():
            device_info['controller'].post_update()

    def check_hot_plugging(self, event: pygame.event.Event) -> None:
        if event.type == pygame.JOYDEVICEADDED:
            joystick = pygame.joystick.Joystick(event.device_index)
            iid = joystick.get_instance_id()
            self.controllers[iid] = {
                'player_index': 'p0', 
                'player_name': 'unselected', 
                'confirmed': False, 
                'timer': Timer(200), 
                'controller': Joystick(joystick)
            }
        if event.type == pygame.JOYDEVICEREMOVED:
            if event.instance_id in self.controllers:
                del self.controllers[event.instance_id]

    def joined_count(self) -> int:
        return sum(1 for dic in self.controllers.values() if dic['player_index'] != 'p0')

    @property
    def joinable(self) -> bool:
        return self.joined_count() < 2

    def join(self, instance_id: int, name: str) -> None:
        self.controllers[instance_id]['player_index'] = f'p{self.joined_count() + 1}'
        self.controllers[instance_id]['player_name'] = name

    def leave(self, instance_id: int) -> None:
        deleting_index = self.controllers[instance_id]['player_index']
        self.controllers[instance_id]['player_index'] = 'p0'
        self.controllers[instance_id]['player_name'] = 'unselected'
        for dic in self.controllers.values():
            if dic['player_index'] > deleting_index:
                dic['player_index'] = f'p{int(dic["player_index"][1:]) - 1}'

    def ready_to_start(self) -> bool:
        count = 0
        for dic in self.controllers.values():
            if dic['player_index'] != 'p0':
                if dic['confirmed']: count += 1
                else: return False
        return count == 2

    def get_confirm_hint(self, lang='zh_CN') -> str: return self._get_action_hint('confirm')
    def get_menu_hint(self, lang='zh_CN') -> str: return self._get_action_hint('cancel')

    def _get_action_hint(self, ui_action) -> str:
        hints = []
        if -1 in self.controllers:
            mapping = {'confirm': '⏎', 'cancel': 'ESC', 'menu': 'M'}
            hints.append(mapping.get(ui_action, ui_action.upper()))
        joysticks = [d['controller'] for id, d in self.controllers.items() if id != -1]
        if joysticks:
            btn_names = [j.get_button_name(j.ui_action_to_id.get(ui_action)) for j in joysticks]
            hints.append("/".join(sorted(list(set(btn_names)))))
        return " / ".join(hints)

    def reset(self) -> None:
        for ctrl in self.controllers.values():
            ctrl['player_index'] = 'p0'
            ctrl['player_name'] = 'unselected'
            ctrl['confirmed'] = False
            ctrl['controller'].release_all()
