import pygame
from src.core.timer import Timer
from src.core.input_config import JOYSTICK_LABELS, UI_MAPPING

class Controller:
    def __init__(self):
        self.battle_actions = ['up', 'down', 'left', 'right', 'jump', 'attack', 'super move 1', 'super move 2', 'finisher']
        self.ui_actions = ['up', 'down', 'left', 'right', 'tab_left', 'tab_right', 'confirm', 'cancel', 'menu']
        self.last_released_key = ''
        self.last_released_time = 0
        self.running = False
        self.execute: dict[str, bool] = {a: False for a in self.battle_actions}
        self.ui_execute: dict[str, bool] = {a: False for a in self.ui_actions}
        self.action_map: dict[str, int] = {}
        self.key_released: dict[int, bool] = {}

    def release_all(self) -> None:
        for key in list(self.key_released.keys()): self.key_released[key] = True

    def handle_keyup(self, event: pygame.event.Event, is_keyboard: bool) -> None:
        current_time = pygame.time.get_ticks()
        event_type = pygame.KEYUP if is_keyboard else pygame.JOYBUTTONUP
        event_key = event.key if is_keyboard else event.button
        if event and event.type == event_type:
            for action, key in self.action_map.items():
                if event_key == key:
                    self.last_released_key = action
                    if action in ['left', 'right']: self.last_released_time = current_time
                    break

    def check_run_status(self) -> None:
        current_time = pygame.time.get_ticks()
        for action in ['left', 'right']:
            if self.execute.get(action, False) and self.last_released_key == action and current_time - self.last_released_time < 150:
                self.running = True
        if self.execute.get('left', False) and self.execute.get('right', False): self.running = False

    def performed(self, action: str) -> bool:
        if action in ['jump', 'attack', 'super move 1', 'super move 2', 'finisher']:
            key = self.action_map.get(action, pygame.K_UNKNOWN)
            if self.execute.get(action, False) and self.key_released.get(key, True):
                self.key_released[key] = False
                return True
        if action in ['up', 'down']: return self.execute.get(action, False)
        if action in ['left', 'right']: return self.execute.get(action, False) and not self.running
        if action in ['run left', 'run right']: return self.execute.get(action[4:], False) and self.running
        return False

    def update(self, event: pygame.event.Event) -> None: pass
    def update_state(self, dt: float) -> None: pass
    def ui_performed(self, action: str) -> bool: return False
    def refresh_map(self): pass

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
        if event.type == pygame.KEYUP:
            self.handle_keyup(event, is_keyboard=True)

    def update_state(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        for action, key in self.action_map.items(): 
            self.execute[action] = keys[key] if key != pygame.K_UNKNOWN else False
        for action, key in self.ui_action_to_key.items():
            self.ui_execute[action] = keys[key]
            if not keys[key]: self.key_released[key] = True
        self.check_run_status()

    def ui_performed(self, action: str) -> bool:
        if action in ['up', 'down', 'left', 'right']: return self.ui_execute.get(action, False)
        key = self.ui_action_to_key.get(action)
        if key and self.ui_execute.get(action, False) and self.key_released.get(key, True):
            self.key_released[key] = False
            return True
        return False

class Joystick(Controller):
    def __init__(self, joystick: pygame.joystick.JoystickType):
        super().__init__()
        self.joystick = joystick
        self.button_count, self.axis_count = joystick.get_numbuttons(), joystick.get_numaxes()
        self.name = joystick.get_name().lower()
        if any(kw in self.name for kw in ['ps', 'dualshock', 'dualsense', 'wireless controller']): self.type = 'ps'
        elif any(kw in self.name for kw in ['nintendo', 'switch', 'joy-con']): self.type = 'nintendo'
        else: self.type = 'xbox'
        self.button_labels = JOYSTICK_LABELS.get(self.type, JOYSTICK_LABELS['xbox'])
        self.label_to_id = {label: btn_id for btn_id, label in self.button_labels.items()}
        ui_map = UI_MAPPING.get(self.type, UI_MAPPING['xbox'])
        self.ui_action_to_id = {action: self.label_to_id.get(label) for action, label in ui_map.items()}
        self.refresh_map()
        self.ls_left_released = self.ls_right_released = True
        self.min_limit = 0.22

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
        if event.type == pygame.JOYAXISMOTION:
            current_time = pygame.time.get_ticks()
            if event.axis == 0:
                if -self.min_limit <= event.value <= self.min_limit:
                    if not self.ls_right_released: self.last_released_time, self.last_released_key, self.running = current_time, 'right', False
                    elif not self.ls_left_released: self.last_released_time, self.last_released_key, self.running = current_time, 'left', False
                    self.ls_right_released = self.ls_left_released = True
                elif event.value < -self.min_limit: self.ls_left_released, self.ls_right_released = False, True
                else: self.ls_left_released, self.ls_right_released = True, False
        elif event.type == pygame.JOYBUTTONUP:
            self.handle_keyup(event, is_keyboard=False)

    def update_state(self, dt: float) -> None:
        h_axis, v_axis = (self.joystick.get_axis(0) if self.axis_count > 0 else 0), (self.joystick.get_axis(1) if self.axis_count > 1 else 0)
        self.execute.update({
            'left': h_axis < -self.min_limit or (self.joystick.get_button(13) if self.button_count > 13 else False),
            'right': h_axis > self.min_limit or (self.joystick.get_button(14) if self.button_count > 14 else False),
            'up': v_axis < -self.min_limit or (self.joystick.get_button(11) if self.button_count > 11 else False),
            'down': v_axis > self.min_limit or (self.joystick.get_button(12) if self.button_count > 12 else False)
        })
        for action in ['jump', 'attack', 'super move 1', 'super move 2', 'finisher']:
            btn_id = self.action_map.get(action)
            self.execute[action] = self.joystick.get_button(btn_id) if btn_id is not None and btn_id < self.button_count else False
        for action, btn_id in self.ui_action_to_id.items():
            is_pressed = self.joystick.get_button(btn_id) if btn_id is not None and btn_id < self.button_count else False
            self.ui_execute[action] = is_pressed
            if not is_pressed and btn_id is not None: self.key_released[btn_id] = True
        self.check_run_status()

    def ui_performed(self, action: str) -> bool:
        if action in ['up', 'down', 'left', 'right']: return self.ui_execute.get(action, False)
        btn_id = self.ui_action_to_id.get(action)
        if btn_id is not None:
            if self.ui_execute.get(action, False) and self.key_released.get(btn_id, True):
                self.key_released[btn_id] = False
                return True
        return False

class GameInput:
    def __init__(self):
        pygame.joystick.init()
        self.controllers: dict[int, dict[str, any]] = {-1: {'player_index': 'p0', 'player_name': 'unselected', 'controller': KeyBoard(), 'timer': Timer(200), 'confirmed': False}}
    def refresh_all_maps(self):
        for device_info in self.controllers.values(): device_info['controller'].refresh_map()
    def update(self, event) -> None:
        self.check_hot_plugging(event)
        if hasattr(event, 'key'): self.controllers[-1]['controller'].update(event)
        if hasattr(event, 'instance_id') and event.instance_id in self.controllers: self.controllers[event.instance_id]['controller'].update(event)
    def update_timers(self, dt):
        for device_info in self.controllers.values():
            device_info['timer'].update()
            device_info['controller'].update_state(dt)
    def check_hot_plugging(self, event: pygame.event.Event) -> None:
        if event.type == pygame.JOYDEVICEADDED:
            joystick = pygame.joystick.Joystick(event.device_index)
            iid = joystick.get_instance_id()
            self.controllers[iid] = {'player_index': 'p0', 'player_name': 'unselected', 'confirmed': False, 'timer': Timer(200), 'controller': Joystick(joystick)}
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
            if dic['player_index'] > deleting_index: dic['player_index'] = f'p{int(dic["player_index"][1:]) - 1}'
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
            mapping = {'confirm': '⏎', 'cancel': 'ESC', 'menu': 'M'}
            hints.append(mapping.get(ui_action, ui_action.upper()))
        joysticks = [d['controller'] for id, d in self.controllers.items() if id != -1]
        if joysticks:
            btn_names = [j.get_button_name(j.ui_action_to_id.get(ui_action)) for j in joysticks]
            hints.append("/".join(sorted(list(set(btn_names)))))
        return " / ".join(hints)
    def reset(self) -> None:
        for ctrl in self.controllers.values():
            ctrl['player_index'], ctrl['player_name'], ctrl['confirmed'] = 'p0', 'unselected', False
            ctrl['controller'].release_all()
