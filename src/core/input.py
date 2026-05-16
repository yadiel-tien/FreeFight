import pygame

from core.timer import Timer


class Controller:
    def __init__(self):
        self.actions = ['up', 'down', 'left', 'right', 'jump', 'attack', 'super move 1', 'super move 2', 'finisher',
                        'confirm', 'cancel', 'menu']
        self.last_released_key = ''
        self.last_released_time = 0
        self.running = False
        self.execute: dict[str:bool] = {}
        self.action_map: dict[str:int] = {}
        self.key_released: dict[int:bool] = {}

        for action in self.actions:
            self.execute[action] = False

    def release_all(self) -> None:
        for key in self.action_map.values():
            self.key_released[key] = True

    def handle_keyup(self, event: pygame.event.Event, is_keyboard: bool) -> None:
        current_time = pygame.time.get_ticks()  # 获取时间戳
        event_type = pygame.KEYUP if is_keyboard else pygame.JOYBUTTONUP
        event_key = event.key if is_keyboard else event.button
        # 除上下键外，其他按键变化就结束跑步
        if event_key not in [self.action_map['up'], self.action_map['down']]:
            self.running = False

        # 记录释放按键、左右键更新时间
        if event and event.type == event_type:
            for action, key in self.action_map.items():
                if event_key == key:
                    self.key_released[key] = True
                    self.last_released_key = action
                    if action in ['left', 'right']:
                        self.last_released_time = current_time
                    break

    def check_run_status(self) -> None:
        # 满足跑步条件进入跑步状态,快速双击
        current_time = pygame.time.get_ticks()
        for action in ['left', 'right']:
            if (
                    self.execute[action]
                    and self.last_released_key == action
                    and current_time - self.last_released_time < 150
            ):
                self.running = True
        if self.execute['left'] and self.execute['right']:  # 避免反向跑步
            self.running = False

    def performed(self, action: str) -> bool:
        if action in self.actions[4:]:
            key = self.action_map[action]
            if self.execute[action] and self.key_released[key]:
                self.key_released[key] = False  # 不允许连按
                return True
        if action in ['up', 'down']:
            return self.execute[action]
        if action in ['left', 'right']:
            return self.execute[action] and not self.running
        if action in ['run left', 'run right']:
            return self.execute[action[4:]] and self.running
        return False


class KeyBoard(Controller):
    def __init__(self):
        super().__init__()
        from core.config import config
        
        # 定义内部映射名到 pygame 常量的映射
        self.name_to_key = {
            'a': pygame.K_a, 'b': pygame.K_b, 'c': pygame.K_c, 'd': pygame.K_d, 'e': pygame.K_e,
            'f': pygame.K_f, 'g': pygame.K_g, 'h': pygame.K_h, 'i': pygame.K_i, 'j': pygame.K_j,
            'k': pygame.K_k, 'l': pygame.K_l, 'm': pygame.K_m, 'n': pygame.K_n, 'o': pygame.K_o,
            'p': pygame.K_p, 'q': pygame.K_q, 'r': pygame.K_r, 's': pygame.K_s, 't': pygame.K_t,
            'u': pygame.K_u, 'v': pygame.K_v, 'w': pygame.K_w, 'x': pygame.K_x, 'y': pygame.K_y,
            'z': pygame.K_z, 'space': pygame.K_SPACE, 'return': pygame.K_RETURN, 
            'escape': pygame.K_ESCAPE, 'backspace': pygame.K_BACKSPACE, 'tab': pygame.K_TAB,
            'left shift': pygame.K_LSHIFT, 'right shift': pygame.K_RSHIFT
        }

        saved_keys = config.get('controls', 'keyboard')
        self.action_map = {}
        for action, key_name in saved_keys.items():
            self.action_map[action] = self.name_to_key.get(key_name.lower(), pygame.K_UNKNOWN)
            
        self.release_all()

    def update(self, event: pygame.event.Event) -> None:
        # 处理按键释放
        self.handle_keyup(event, is_keyboard=True)

        # 更新按键按下状态
        keys = pygame.key.get_pressed()
        for action, key in self.action_map.items():
            self.execute[action] = keys[key]

        # 检查跑步状态
        self.check_run_status()


class Joystick(Controller):
    def __init__(self, joystick: pygame.joystick.JoystickType):
        super().__init__()
        from core.config import config
        
        self.key_map = {'A': 0, 'B': 1, 'X': 2, 'Y': 3, '-': 4, 'Home': 5, '+': 6, 'left stick down': 7,
                        'right stick down': 8, 'left bumper': 9, 'right bumper': 10, 'cross up': 11,
                        'cross down': 12, 'cross left': 13, 'cross right': 14, 'capture': 15,
                        'left stick horizontal': 0, 'left stick vertical': 1, 'right stick horizontal': 2,
                        'right stick vertical': 3, 'left trigger': 4, 'right trigger': 5}
        
        # 从配置中加载手柄映射
        self.action_map = config.get('controls', 'joystick')
        
        self.release_all()
        self.joystick = joystick
        self.button_count = joystick.get_numbuttons()
        self.axis_count = joystick.get_numaxes()
        self.ls_left_released = True
        self.ls_right_released = True

        self.min_limit = 0.22

    def handle_axis(self, event: pygame.event.Event) -> None:
        # 记录摇杆左右动作和释放
        if event.axis == self.key_map['left stick horizontal']:
            current_time = pygame.time.get_ticks()

            if -self.min_limit <= event.value <= self.min_limit:
                if not self.ls_right_released:
                    self.last_released_time = current_time
                    self.last_released_key = 'right'
                    self.running = False
                elif not self.ls_left_released:
                    self.last_released_time = current_time
                    self.last_released_key = 'left'
                    self.running = False

                self.ls_right_released = True
                self.ls_left_released = True
            elif event.value < -self.min_limit:
                self.ls_left_released = False
                self.ls_right_released = True
            else:
                self.ls_left_released = True
                self.ls_right_released = False

    def pressed(self, button: str) -> bool:
        button_id = self.action_map[button]
        return self.joystick.get_button(button_id) if button_id < self.button_count else False

    def axis_value(self, axis: str) -> float:
        axis_id = self.key_map[axis]
        return self.joystick.get_axis(axis_id) if axis_id < self.axis_count else 0

    def stick_to(self, direction: str) -> bool:
        horizontal = self.axis_value('left stick horizontal')
        vertical = self.axis_value('left stick vertical')
        if direction == 'left':
            return horizontal < -self.min_limit
        elif direction == 'right':
            return horizontal > self.min_limit
        elif direction == 'up':
            return vertical < -self.min_limit
        elif direction == 'down':
            return vertical > self.min_limit
        else:
            return False

    def update(self, event: pygame.event.Event) -> None:
        # 处理按键释放
        if event.type == pygame.JOYAXISMOTION:
            self.handle_axis(event)
        else:
            self.handle_keyup(event, is_keyboard=False)
            # 更新按键按下状态
            for action in self.actions[4:]:
                self.execute[action] = self.pressed(action)

        # 上下左右,支持摇杆和十字键
        for action in ['left', 'right', 'up', 'down']:
            self.execute[action] = self.stick_to(action) or self.pressed(action)

        # 检查跑步状态
        self.check_run_status()


class GameInput:
    def __init__(self):
        pygame.joystick.init()
        self.controllers: dict[int:dict[str: any]] = {-1: {
            'player_index': 'p0',
            'player_name': 'unselected',
            'controller': KeyBoard(),
            'timer': Timer(200),
            'confirmed': False
        }}

    def update_timer(self) -> None:
        for controller in self.controllers.values():
            controller['timer'].update()

    def update(self, event) -> None:
        self.check_hot_plugging(event)
        self.update_timer()
        if hasattr(event, 'key'):  # 键盘事件更新
            self.controllers[-1]['controller'].update(event)
        if hasattr(event, 'instance_id') and event.instance_id in self.controllers:  # 手柄事件更新
            self.controllers[event.instance_id]['controller'].update(event)

    def check_hot_plugging(self, event: pygame.event.Event) -> None:
        # Handle hot plugging
        if event.type == pygame.JOYDEVICEADDED:
            # event 有属性type，guid，device_index,同型号guid会重复
            # device_index为设备索引，按插入顺序为0，1，2，3。。。
            # instance_id为对象编号，每创建一个joystick就增加1，断掉再连也会增加1
            joystick = pygame.joystick.Joystick(event.device_index)
            instance_id = joystick.get_instance_id()
            # 新设备添加
            self.controllers[instance_id] = {
                'player_index': 'p0',
                'player_name': 'unselected',
                'confirmed': False,
                'timer': Timer(200),
                'controller': Joystick(joystick)
            }

        if event.type == pygame.JOYDEVICEREMOVED:
            # event 有属性type、instance_id,此instance_id=创建时的joystick.get_instance_id()
            del self.controllers[event.instance_id]

    def joined_count(self) -> int:
        return sum(1 for dic in self.controllers.values() if dic['player_index'] != 'p0')

    def joinable(self) -> None:
        return self.joined_count() < 4

    def join(self, instance_id: int, name: str) -> None:
        player_index = f'p{self.joined_count() + 1}'
        self.controllers[instance_id]['player_index'] = player_index
        self.controllers[instance_id]['player_name'] = name

    def leave(self, instance_id: int) -> None:
        # 删除player_index,name
        deleting_index = self.controllers[instance_id]['player_index']

        # 重置被删除玩家的索引和名称
        self.controllers[instance_id]['player_index'] = 'p0'
        self.controllers[instance_id]['player_name'] = 'unselected'

        # 其他手柄位次前移
        for dic in self.controllers.values():
            if dic['player_index'] > deleting_index:
                current_index = int(dic['player_index'][1:])
                dic['player_index'] = f'p{current_index - 1}'

    def ready_to_start(self) -> bool:
        count = 0  # 所有玩家都已准备好，且人数不少于2人
        for dic in self.controllers.values():
            if dic['player_index'] != 'p0':
                if dic['confirmed']:
                    count += 1
                else:
                    return False

        return count > 0

    def reset(self) -> None:
        for ctrl in self.controllers.values():
            ctrl['player_index'] = 'p0'
            ctrl['player_name'] = 'unselected'
            ctrl['confirmed'] = False
