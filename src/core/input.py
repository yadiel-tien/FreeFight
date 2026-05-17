import pygame

from src.core.timer import Timer


class Controller:
    def __init__(self):
        # 可自定义的战斗动作
        self.battle_actions = ['up', 'down', 'left', 'right', 'jump', 'attack', 'super move 1', 'super move 2', 'finisher']
        # 固定的界面控制动作
        self.ui_actions = ['up', 'down', 'left', 'right', 'tab_left', 'tab_right', 'confirm', 'cancel', 'menu']
        
        self.last_released_key = ''
        self.last_released_time = 0
        self.running = False
        
        self.execute: dict[str, bool] = {a: False for a in self.battle_actions}
        self.ui_execute: dict[str, bool] = {a: False for a in self.ui_actions}
        
        self.action_map: dict[str, int] = {}
        self.key_released: dict[int, bool] = {}

    def release_all(self) -> None:
        for key in self.action_map.values():
            self.key_released[key] = True

    def handle_keyup(self, event: pygame.event.Event, is_keyboard: bool) -> None:
        current_time = pygame.time.get_ticks()
        event_type = pygame.KEYUP if is_keyboard else pygame.JOYBUTTONUP
        event_key = event.key if is_keyboard else event.button
        
        if event_key not in [self.action_map.get('up'), self.action_map.get('down')]:
            self.running = False

        if event and event.type == event_type:
            # 1. 记录战斗映射按键的释放
            for action, key in self.action_map.items():
                if event_key == key:
                    self.key_released[key] = True
                    self.last_released_key = action
                    if action in ['left', 'right']:
                        self.last_released_time = current_time
                    break
            # 2. 记录所有物理按键的释放状态 (用于界面控制的 one-shot 逻辑)
            self.key_released[event_key] = True

    def check_run_status(self) -> None:
        current_time = pygame.time.get_ticks()
        for action in ['left', 'right']:
            if (
                    self.execute.get(action, False)
                    and self.last_released_key == action
                    and current_time - self.last_released_time < 150
            ):
                self.running = True
        if self.execute.get('left', False) and self.execute.get('right', False):
            self.running = False

    def performed(self, action: str) -> bool:
        """战斗动作检测 (受配置影响)"""
        if action in ['jump', 'attack', 'super move 1', 'super move 2', 'finisher']:
            key = self.action_map.get(action, pygame.K_UNKNOWN)
            if self.execute.get(action, False) and self.key_released.get(key, True):
                self.key_released[key] = False # 消耗该次按键
                return True
        if action in ['up', 'down']:
            return self.execute.get(action, False)
        if action in ['left', 'right']:
            return self.execute.get(action, False) and not self.running
        if action in ['run left', 'run right']:
            return self.execute.get(action[4:], False) and self.running
        return False

    def ui_performed(self, action: str) -> bool:
        """界面动作检测 (硬编码，不受配置影响)"""
        return False

    def refresh_map(self):
        pass


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
            'space': pygame.K_SPACE, 'return': pygame.K_RETURN, 
            'escape': pygame.K_ESCAPE, 'backspace': pygame.K_BACKSPACE, 'tab': pygame.K_TAB,
            'left shift': pygame.K_LSHIFT, 'right shift': pygame.K_RSHIFT,
            'left ctrl': pygame.K_LCTRL, 'right ctrl': pygame.K_RCTRL,
            'left alt': pygame.K_LALT, 'right alt': pygame.K_RALT,
            'page up': pygame.K_PAGEUP, 'page down': pygame.K_PAGEDOWN,
            'home': pygame.K_HOME, 'end': pygame.K_END, 'insert': pygame.K_INSERT, 'delete': pygame.K_DELETE,
            'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT, 'right': pygame.K_RIGHT
        }
        self.refresh_map()

    def refresh_map(self):
        from src.core.config import config
        saved_keys = config.get('controls', 'keyboard')
        self.action_map = {}
        for action in self.battle_actions:
            key_name = saved_keys.get(action)
            if key_name:
                self.action_map[action] = self.name_to_key.get(key_name.lower(), pygame.K_UNKNOWN)
        self.release_all()

    def update(self, event: pygame.event.Event) -> None:
        self.handle_keyup(event, is_keyboard=True)
        keys = pygame.key.get_pressed()
        
        # 战斗动作状态
        for action, key in self.action_map.items():
            self.execute[action] = keys[key] if key != pygame.K_UNKNOWN else False

        # UI 动作状态
        self.ui_execute['up'] = keys[pygame.K_UP]
        self.ui_execute['down'] = keys[pygame.K_DOWN]
        self.ui_execute['left'] = keys[pygame.K_LEFT]
        self.ui_execute['right'] = keys[pygame.K_RIGHT]
        self.ui_execute['tab_left'] = keys[pygame.K_q]
        self.ui_execute['tab_right'] = keys[pygame.K_e]
        self.ui_execute['confirm'] = keys[pygame.K_RETURN]
        self.ui_execute['cancel'] = keys[pygame.K_ESCAPE]
        self.ui_execute['menu'] = keys[pygame.K_ESCAPE]

        self.check_run_status()

    def ui_performed(self, action: str) -> bool:
        one_shot_map = {
            'tab_left': pygame.K_q, 'tab_right': pygame.K_e,
            'confirm': pygame.K_RETURN, 'cancel': pygame.K_ESCAPE, 'menu': pygame.K_ESCAPE
        }
        key = one_shot_map.get(action)
        if key and self.ui_execute.get(action, False) and self.key_released.get(key, True):
            self.key_released[key] = False
            return True
        if action in ['up', 'down', 'left', 'right']:
            return self.ui_execute.get(action, False)
        return False


class Joystick(Controller):
    def __init__(self, joystick: pygame.joystick.JoystickType):
        super().__init__()
        self.joystick = joystick
        self.button_count = joystick.get_numbuttons()
        self.axis_count = joystick.get_numaxes()
        
        # 识别手柄类型
        self.name = joystick.get_name().lower()
        if any(kw in self.name for kw in ['ps', 'dualshock', 'dualsense', 'wireless controller']):
            self.type = 'ps'
        elif any(kw in self.name for kw in ['nintendo', 'switch', 'joy-con']):
            self.type = 'nintendo'
        else:
            self.type = 'xbox'

        self.refresh_map()
        self.ls_left_released = True
        self.ls_right_released = True
        self.min_limit = 0.22

    def get_button_name(self, button_id: int) -> str:
        if button_id is None: return "---"
        mapping = {
            'xbox': {0: 'A', 1: 'B', 2: 'X', 3: 'Y', 4: 'LB', 5: 'RB', 6: 'Back', 7: 'Start', 8: 'LS', 9: 'LB', 10: 'RB', 11: 'Up', 12: 'Down', 13: 'Left', 14: 'Right'},
            'ps': {0: 'X', 1: '○', 2: '□', 3: '△', 4: 'L1', 5: 'R1', 6: 'Share', 7: 'Options', 8: 'L3', 9: 'L1', 10: 'R1', 11: 'Up', 12: 'Down', 13: 'Left', 14: 'Right'},
            'nintendo': {0: 'A', 1: 'B', 2: 'X', 3: 'Y', 4: 'L', 5: 'R', 6: '-', 7: '+', 8: 'LS', 9: 'L', 10: 'R', 11: 'Up', 12: 'Down', 13: 'Left', 14: 'Right'}
        }
        # 强制覆盖 ID 9/10 为肩键
        if button_id == 9: return "L" if self.type == 'nintendo' else "L1" if self.type == 'ps' else "LB"
        if button_id == 10: return "R" if self.type == 'nintendo' else "R1" if self.type == 'ps' else "RB"
        
        res = mapping.get(self.type, mapping['xbox']).get(button_id)
        return res if res else f"BTN {button_id}"

    def refresh_map(self):
        from src.core.config import config
        saved_keys = config.get('controls', 'joystick')
        self.action_map = {a: saved_keys.get(a) for a in self.battle_actions}
        self.release_all()

    def update(self, event: pygame.event.Event) -> None:
        if event.type == pygame.JOYAXISMOTION:
            current_time = pygame.time.get_ticks()
            if event.axis == 0: # Horizontal
                if -self.min_limit <= event.value <= self.min_limit:
                    if not self.ls_right_released: self.last_released_time, self.last_released_key, self.running = current_time, 'right', False
                    elif not self.ls_left_released: self.last_released_time, self.last_released_key, self.running = current_time, 'left', False
                    self.ls_right_released = self.ls_left_released = True
                elif event.value < -self.min_limit: self.ls_left_released, self.ls_right_released = False, True
                else: self.ls_left_released, self.ls_right_released = True, False
        else:
            self.handle_keyup(event, is_keyboard=False)

        # 战斗动作状态 (配置映射)
        h_axis = self.joystick.get_axis(0) if self.axis_count > 0 else 0
        v_axis = self.joystick.get_axis(1) if self.axis_count > 1 else 0
        self.execute['left'] = h_axis < -self.min_limit or (self.joystick.get_button(13) if self.button_count > 13 else False)
        self.execute['right'] = h_axis > self.min_limit or (self.joystick.get_button(14) if self.button_count > 14 else False)
        self.execute['up'] = v_axis < -self.min_limit or (self.joystick.get_button(11) if self.button_count > 11 else False)
        self.execute['down'] = v_axis > self.min_limit or (self.joystick.get_button(12) if self.button_count > 12 else False)
        
        for action in ['jump', 'attack', 'super move 1', 'super move 2', 'finisher']:
            btn_id = self.action_map.get(action)
            self.execute[action] = self.joystick.get_button(btn_id) if btn_id is not None and btn_id < self.button_count else False

        # UI 动作状态 (硬编码物理按键)
        self.ui_execute['up'] = self.execute['up']
        self.ui_execute['down'] = self.execute['down']
        self.ui_execute['left'] = self.execute['left']
        self.ui_execute['right'] = self.execute['right']
        self.ui_execute['tab_left'] = self.joystick.get_button(9) if self.button_count > 9 else False
        self.ui_execute['tab_right'] = self.joystick.get_button(10) if self.button_count > 10 else False
        self.ui_execute['confirm'] = self.joystick.get_button(0) if self.button_count > 0 else False # A
        self.ui_execute['cancel'] = self.joystick.get_button(1) if self.button_count > 1 else False  # B
        self.ui_execute['menu'] = (self.joystick.get_button(7) if self.button_count > 7 else False) or \
                                 (self.joystick.get_button(6) if self.button_count > 6 else False)

        self.check_run_status()

    def ui_performed(self, action: str) -> bool:
        # 定义 UI 动作对应的所有物理按钮 ID
        ui_btn_map = {
            'tab_left': [9], 'tab_right': [10],
            'confirm': [0], 'cancel': [1],
            'menu': [7, 6], # Start 或 Back
            'up': [11], 'down': [12], 'left': [13], 'right': [14]
        }
        
        btns = ui_btn_map.get(action, [])
        if not btns: return False
        
        # 对于 one-shot 动作 (非方向键)
        if action not in ['up', 'down', 'left', 'right']:
            for b in btns:
                if b < self.button_count and self.joystick.get_button(b) and self.key_released.get(b, True):
                    self.key_released[b] = False
                    return True
            return False
        else:
            # 方向键直接返回执行状态
            return self.ui_execute.get(action, False)


class GameInput:
    def __init__(self):
        pygame.joystick.init()
        self.controllers: dict[int, dict[str, any]] = {-1: {
            'player_index': 'p0',
            'player_name': 'unselected',
            'controller': KeyBoard(),
            'timer': Timer(200),
            'confirmed': False
        }}

    def refresh_all_maps(self):
        for device_info in self.controllers.values():
            device_info['controller'].refresh_map()

    def update(self, event) -> None:
        self.check_hot_plugging(event)
        for controller in self.controllers.values(): controller['timer'].update()
        if hasattr(event, 'key'): self.controllers[-1]['controller'].update(event)
        if hasattr(event, 'instance_id') and event.instance_id in self.controllers:
            self.controllers[event.instance_id]['controller'].update(event)

    def check_hot_plugging(self, event: pygame.event.Event) -> None:
        if event.type == pygame.JOYDEVICEADDED:
            joystick = pygame.joystick.Joystick(event.device_index)
            iid = joystick.get_instance_id()
            self.controllers[iid] = {
                'player_index': 'p0', 'player_name': 'unselected', 'confirmed': False,
                'timer': Timer(200), 'controller': Joystick(joystick)
            }
        if event.type == pygame.JOYDEVICEREMOVED:
            if event.instance_id in self.controllers: del self.controllers[event.instance_id]

    def joined_count(self) -> int: return sum(1 for dic in self.controllers.values() if dic['player_index'] != 'p0')
    def joinable(self) -> bool: return self.joined_count() < 4

    def join(self, instance_id: int, name: str) -> None:
        self.controllers[instance_id]['player_index'] = f'p{self.joined_count() + 1}'
        self.controllers[instance_id]['player_name'] = name

    def leave(self, instance_id: int) -> None:
        deleting_index = self.controllers[instance_id]['player_index']
        self.controllers[instance_id]['player_index'], self.controllers[instance_id]['player_name'] = 'p0', 'unselected'
        for dic in self.controllers.values():
            if dic['player_index'] > deleting_index:
                dic['player_index'] = f'p{int(dic["player_index"][1:]) - 1}'

    def ready_to_start(self) -> bool:
        count = 0
        for dic in self.controllers.values():
            if dic['player_index'] != 'p0':
                if dic['confirmed']: count += 1
                else: return False
        return count > 0

    def get_confirm_hint(self, lang='zh_CN') -> str: return self._get_action_hint('confirm')
    def get_menu_hint(self, lang='zh_CN') -> str: return self._get_action_hint('cancel')

    def _get_action_hint(self, ui_action) -> str:
        hints = []
        if -1 in self.controllers:
            mapping = {'confirm': '⏎', 'cancel': 'ESC'}
            hints.append(mapping.get(ui_action, ui_action.upper()))
        joysticks = [d['controller'] for id, d in self.controllers.items() if id != -1]
        if joysticks:
            joy_map = {'confirm': 0, 'cancel': 1}
            btn_names = [j.get_button_name(joy_map.get(ui_action)) for j in joysticks]
            hints.append("/".join(sorted(list(set(btn_names)))))
        return " / ".join(hints)

    def reset(self) -> None:
        for ctrl in self.controllers.values():
            ctrl['player_index'], ctrl['player_name'], ctrl['confirmed'] = 'p0', 'unselected', False
