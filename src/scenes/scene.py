import os.path

import pygame
from enum import Enum

from ui.components.dialogue import Dialogue
from core.input import GameInput
from core.support import import_folder_dict, resource_path, import_pic, import_gif
from settings import *
from ui.text import Menu
from core.timer import Timer
from ui.ui import Particles
from ui.components.widgets import Slider, Selector, KeyBinder, Button, Toggle
from core.config import config
from core.logger import logger
import settings


class SceneStatus(Enum):
    UNDEFINED = 0
    HOME = 1
    CHOOSE_ROLE = 2
    CHOOSE_BACKGROUND = 3
    FIGHTING = 4
    SETTINGS = 5
    EXIT = 6


class Scene:
    def __init__(self, game_input: GameInput):
        self.screen = pygame.display.get_surface()
        self.game_input = game_input

    def run(self, dt) -> SceneStatus:
        pass

    def de_init(self):
        pass


class Home(Scene):
    def __init__(self, game_input: GameInput):
        super().__init__(game_input)
        # 背景图
        image = pygame.image.load(resource_path('assets/graphics/background/background_blurred.png'))
        self.image = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        # 文字半透明背景
        self.title_surf = pygame.Surface((550, 450), pygame.SRCALPHA)
        title = pygame.image.load(resource_path('assets/graphics/background/title.png'))
        self.title = pygame.transform.scale(title, (550, 450)).convert_alpha()
        self.title_surf.blit(self.title, (0, 0))
        # 菜单背景
        self.menu_rect = pygame.Rect(100, 0, 200, SCREEN_HEIGHT)
        self.menu_surf = pygame.Surface(self.menu_rect.size, pygame.SRCALPHA)
        self.menu_surf.fill((0, 0, 0, 214))
        # 菜单
        options = ['对战', '操作', '角色', '选项', '退出']
        self.menu = Menu(options, game_input, (120, 200))
        # 粒子
        self.sparkles = Particles(0.05)

        self.dialogue = Dialogue(game_input)

    def run(self, dt) -> SceneStatus:
        if self.dialogue.showing:
            if self.dialogue.run():
                return SceneStatus.EXIT
        else:
            self.screen.blit(self.image, (0, 0))
            self.screen.blit(self.menu_surf, self.menu_rect)
            self.sparkles.update(dt)
            self.menu.display()
            self.screen.blit(self.title_surf, (500, 250))

            index = self.menu.handle_input()
            if index == 4:
                self.dialogue.show('确定要退出吗？')
            elif index == 0:
                return SceneStatus.CHOOSE_ROLE
            elif index == 3:
                return SceneStatus.SETTINGS
        return SceneStatus.HOME


class Settings(Scene):
    def __init__(self, game_input: GameInput):
        super().__init__(game_input)
        
        background = import_pic('assets/graphics/background/background_blurred.png')
        self.image = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        self.panel_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 250, 600, 500)
        self.panel_surf = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
        self.panel_surf.fill((0, 0, 0, 230))
        
        # 加载中文字体
        self.font = pygame.font.Font(resource_path('assets/font/SimHei.ttf'), 36)
        
        self.init_widgets()
        self.selection_index = 0
        self.widgets[0].selected = True
        
        # 增加输入冷却时间，防止一按跳好几个（从150ms调到250ms）
        self.timer = Timer(250) 
        self.dialogue = Dialogue(game_input)

    def init_widgets(self):
        x, y = self.panel_rect.x + 50, self.panel_rect.y + 100
        self.widgets = [
            Slider('主音量', (x, y), config.get('volume', 'master')),
            Slider('音乐', (x, y + 45), config.get('volume', 'music')),
            Slider('音效', (x, y + 90), config.get('volume', 'sfx')),
            Toggle('全屏', (x, y + 135), config.get('graphics', 'fullscreen')),
            Selector('分辨率', (x, y + 180), ['1280x720', '1920x1080', '800x600'], 0),
            KeyBinder('键盘攻击', (x, y + 225), config.get('controls', 'keyboard', 'attack')),
            KeyBinder('手柄攻击', (x, y + 270), config.get('controls', 'joystick', 'attack'), is_joystick=True),
            Button('恢复默认设置', (x, y + 330), (500, 45))
        ]

    def run(self, dt) -> SceneStatus:
        if self.dialogue.showing:
            if self.dialogue.run():
                config.reset_to_defaults()
                self.init_widgets() # 重新加载组件状态
            return SceneStatus.SETTINGS

        self.screen.blit(self.image, (0, 0))
        pygame.draw.rect(self.screen, 'orange', self.panel_rect.inflate(10, 10), 2)
        self.screen.blit(self.panel_surf, self.panel_rect)
        
        # 绘制标题
        title = self.font.render('系统设置 SETTINGS', True, 'orange')
        self.screen.blit(title, (self.panel_rect.x + 50, self.panel_rect.y + 30))

        for widget in self.widgets:
            widget.draw(self.screen)

        return self.handle_input()

    def handle_input(self):
        # 使用第一个可用的控制器
        ctrl = None
        for dic in self.game_input.controllers.values():
            ctrl = dic['controller']
            break
        
        if not ctrl: return SceneStatus.SETTINGS

        self.timer.update()
        
        # 处理按键绑定等待 (键盘 + 手柄)
        current_widget = self.widgets[self.selection_index]
        if isinstance(current_widget, KeyBinder) and current_widget.waiting_for_input:
            # 监听键盘
            for event in pygame.event.get(pygame.KEYDOWN):
                if not current_widget.is_joystick:
                    key_name = pygame.key.name(event.key)
                    current_widget.key = key_name
                    current_widget.waiting_for_input = False
                    config.set(key_name, 'controls', 'keyboard', 'attack')
                    self.timer.activate()
                return SceneStatus.SETTINGS
            
            # 监听手柄按钮
            for event in pygame.event.get(pygame.JOYBUTTONDOWN):
                if current_widget.is_joystick:
                    btn_id = event.button
                    current_widget.key = btn_id
                    current_widget.waiting_for_input = False
                    config.set(btn_id, 'controls', 'joystick', 'attack')
                    self.timer.activate()
                return SceneStatus.SETTINGS
            
            return SceneStatus.SETTINGS

        if self.timer.active: return SceneStatus.SETTINGS

        # 上下选择
        if ctrl.performed('up'):
            current_widget.selected = False
            self.selection_index = (self.selection_index - 1) % len(self.widgets)
            self.widgets[self.selection_index].selected = True
            self.timer.activate()
        elif ctrl.performed('down'):
            current_widget.selected = False
            self.selection_index = (self.selection_index + 1) % len(self.widgets)
            self.widgets[self.selection_index].selected = True
            self.timer.activate()

        # 左右调节
        if ctrl.performed('left') or ctrl.performed('right'):
            direction = 'left' if ctrl.performed('left') else 'right'
            if not isinstance(current_widget, Button):
                val = current_widget.update_value(direction)
                self._apply_setting(current_widget.label, val)
                self.timer.activate()

        # 确定与返回
        if ctrl.performed('confirm'):
            if isinstance(current_widget, Button):
                self.dialogue.show('确定要恢复默认设置吗？')
                self.timer.activate()
            elif hasattr(current_widget, 'waiting_for_input'):
                current_widget.waiting_for_input = True
                self.timer.activate()
            elif not isinstance(current_widget, Slider):
                val = current_widget.update_value('right')
                self._apply_setting(current_widget.label, val)
                self.timer.activate()
        
        if ctrl.performed('cancel'):
            config.save()
            return SceneStatus.HOME

        return SceneStatus.SETTINGS

    def _apply_setting(self, label, value):
        if label == '主音量': config.set(value, 'volume', 'master')
        elif label == '音乐': config.set(value, 'volume', 'music')
        elif label == '音效': config.set(value, 'volume', 'sfx')
        elif label == '全屏': 
            config.set(value, 'graphics', 'fullscreen')
            # 使用 SCALED 配合 FULLSCREEN 是 Pygame 2 在 Mac 上的最佳实践
            flags = pygame.SCALED
            if value:
                flags |= pygame.FULLSCREEN
            
            # 重新设置模式
            pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), flags)
            self.screen = pygame.display.get_surface()
            self.screen.blit(self.image, (0, 0))
            pygame.display.flip()
        elif label == '分辨率':
            config.set(value, 'graphics', 'resolution')
            # 实现即时分辨率切换
            try:
                w, h = map(int, value.split('x'))
                
                # 更新全局变量
                settings.SCREEN_WIDTH = w
                settings.SCREEN_HEIGHT = h
                
                flags = pygame.SCALED
                if config.get('graphics', 'fullscreen'):
                    flags |= pygame.FULLSCREEN
                
                # 切换显示模式
                pygame.display.set_mode((w, h), flags)
                self.screen = pygame.display.get_surface()
                
                # 重新计算 UI 布局
                self.panel_rect = pygame.Rect(w // 2 - 300, h // 2 - 250, 600, 500)
                background = import_pic('assets/graphics/background/background_blurred.png')
                self.image = pygame.transform.scale(background, (w, h))
                
                # 重新初始化组件以更新它们的位置坐标
                self.init_widgets()
                # 保持之前的选中索引
                self.widgets[self.selection_index].selected = True
                
                # 强制刷新画面
                self.screen.blit(self.image, (0, 0))
                pygame.display.flip()
                
                logger.info(f"Resolution changed to {w}x{h}")
            except Exception as e:
                logger.error(f"Error changing resolution: {e}")


class RolePicker(Scene):
    def __init__(self, game_input: GameInput):
        super().__init__(game_input)
        # 背景图
        background = import_pic('assets/graphics/background/background_blurred.png')
        self.image = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        # 文字半透明背景
        self.bar_rect = pygame.Rect(0, SCREEN_HEIGHT - 240, SCREEN_WIDTH, 180)
        self.bar = pygame.Surface(self.bar_rect.size, pygame.SRCALPHA)
        self.bar.fill((0, 0, 0, 214))  # 半透明
        self.role_menu = RoleMenu(self.game_input)  # 可选角色
        self.role_details = RoleDetailModule(self.game_input)  # 角色详情
        self.image.blit(self.bar, self.bar_rect)
        self.particles = Particles(0.05)
        self.timer = Timer(100, lambda: setattr(self, 'start', True))
        self.start = False

    def handle_input(self):
        for instance_id, device_info in self.game_input.controllers.items():
            ctrl = device_info['controller']
            current_player = device_info['player_name']
            timer = device_info['timer']

            if device_info['player_index'] != 'p0':  # 已加入游戏
                # 左右选择人物
                if not timer.active and not device_info['confirmed']:  # 选定后不能移动
                    if ctrl.performed('left'):
                        device_info['player_name'] = self.role_menu.previous(current_player)
                        timer.activate()
                    elif ctrl.performed('right'):
                        device_info['player_name'] = self.role_menu.next(current_player)
                        timer.activate()

                # 确认选择
                if ctrl.performed('confirm'):
                    device_info['confirmed'] = True

                    # 检查是否具备开始条件,超过2个玩家，全部准备好
                    if self.game_input.ready_to_start():
                        self.timer.activate()  # 启动计时器

                # 满足条件后稍等片刻进入游戏
                if self.start:
                    return SceneStatus.FIGHTING

                # 取消操作
                if ctrl.performed('cancel') and not self.timer.active:
                    if device_info['confirmed']:  # 取消确认
                        device_info['confirmed'] = False
                    else:  # 退出游戏控制
                        self.game_input.leave(instance_id)
                        self.role_details.create_details()  # 刷新显示

            # 加入游戏
            elif self.game_input.joinable:
                if ctrl.performed('confirm'):
                    self.game_input.join(instance_id, self.role_menu.available())
                    self.role_details.create_details()  # 刷新显示
                # 返回上一级
                if ctrl.performed('cancel') and self.game_input.joined_count() == 0:
                    return SceneStatus.HOME
        return SceneStatus.CHOOSE_ROLE

    def run(self, dt) -> SceneStatus:
        self.timer.update()
        self.screen.blit(self.image, (0, 0))
        self.particles.update(dt)
        self.role_menu.update()
        self.role_details.update(dt)
        return self.handle_input()


class RoleDetailModule:
    def __init__(self, game_input: GameInput):
        self.group = pygame.sprite.Group()
        self.game_input = game_input
        self.place_holder = None
        self.screen = pygame.display.get_surface()
        self.create_details()

    def create_details(self):
        self.group.empty()
        num = self.game_input.joined_count()
        y, w, h = 40, 280, 420  # 默认尺寸
        if num > 2:  # 数量太多，缩小尺寸
            y, w, h = 100, 200, 300  # 缩小后尺寸
        if num < 4:
            gap = (SCREEN_WIDTH - w * (num + 1)) // (num + 2)
        else:
            gap = (SCREEN_WIDTH - w * 4) // 5
        x = gap
        for i in range(1, 5):
            for dic in self.game_input.controllers.values():
                if dic['player_index'] == f'p{i}':
                    RoleDetailItem(dic, (x, y, w, h), self.group)
                    x += gap + w
                    break

        # 加入提示
        self.place_holder = RoleDetailItem(None, (x, y, w, h), self.group) if num < 4 else None

    def update(self, dt):
        self.group.update(dt)
        self.group.draw(self.screen)


class RoleDetailItem(pygame.sprite.Sprite):
    def __init__(self, device_info, rect: tuple, groups: pygame.sprite.Group):
        super().__init__(groups)
        self.device_info = device_info
        self.name = ''
        self.half_length = None
        self.full_length_pics = None
        self.full_length_index = 0
        self.full_length_pic = None
        self.indicators = import_folder_dict('assets/graphics/icons/indicator')
        check_icon = import_pic('assets/graphics/icons/check.png')
        self.check_icon = pygame.transform.scale(check_icon, (60, 60))
        self.earth_icon = import_pic('assets/graphics/icons/earth.png')
        self.update_player_pics()
        self.rect = pygame.Rect(rect)

        self.alpha_background = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.image = pygame.surface.Surface(self.rect.size, pygame.SRCALPHA)

        # 占位相关提示
        self.text_surf = Menu.get_tip_surf('A 加入游戏')
        rect = self.text_surf.get_rect(midbottom=self.rect.midbottom).move(0, -50)
        self.text_offset = rect.x - self.rect.x, rect.y - self.rect.y

    def draw_indicator(self):
        if self.device_info:
            size = self.rect.w * 0.25
            indicator = pygame.transform.scale(self.indicators[self.device_info['player_index']], (size, size))
            self.image.blit(indicator, (0, self.rect.h - size))

    def draw_check_mark(self):
        if self.device_info and self.device_info['confirmed']:
            self.image.blit(self.check_icon, (self.rect.w - 60, self.rect.h - 60))

    def draw_tip(self):
        self.image.blit(self.text_surf, self.text_offset)

    def update_player_pics(self):
        self.name = self.device_info['player_name'] if self.device_info else 'unselected'
        if self.name == 'unselected':
            self.half_length = self.earth_icon
            self.full_length_pics = None
        else:
            self.half_length = import_pic(f'assets/graphics/sprites/{self.name}/half_length.png')
            self.full_length_pics = import_gif(f'assets/graphics/sprites/{self.name}/idle.gif')

    def draw_background(self):
        if self.device_info and self.device_info['confirmed']:
            self.alpha_background.fill('orange')
            self.alpha_background.set_alpha(214)
        else:
            self.alpha_background.fill('black')
            self.alpha_background.set_alpha(114)
        half = pygame.transform.scale(self.half_length, self.rect.size)
        self.alpha_background.blit(half, (0, 0))
        self.image.blit(self.alpha_background, (0, 0))

    # 更新动画
    def update_full_length_pic(self, dt):
        self.full_length_index += dt * 4
        if self.full_length_index >= len(self.full_length_pics):
            self.full_length_index = 0
        if not self.full_length_pics:
            self.full_length_pic = None
        else:
            original = self.full_length_pics[int(self.full_length_index)]
            self.full_length_pic = pygame.transform.flip(original, True, False)

    def draw_foreground(self):
        # 全身像转为标准尺寸
        # 缩放 rect 并保持 midbottom 对齐
        full_rect = self.rect.scale_by(0.7)
        full_rect.midbottom = self.rect.midbottom
        # 按缩放后的 rect 大小调整图像
        full = pygame.transform.scale(self.full_length_pic, full_rect.size)
        # 计算偏移量，并将图像绘制到 self.image 上
        full_offset = full_rect.x - self.rect.x, full_rect.y - self.rect.y
        # 半身像转为标准尺寸

        self.image.blit(full, full_offset)

    def update(self, dt):
        self.update_player_pics()
        self.image.fill((0, 0, 0, 0))
        self.alpha_background.fill('black')
        self.draw_background()
        if self.name != 'unselected':
            self.update_full_length_pic(dt)
            self.draw_foreground()
            self.draw_indicator()
            self.draw_check_mark()
        else:
            self.draw_tip()


class RoleMenu:
    def __init__(self, game_input: GameInput):
        self.group = pygame.sprite.Group()
        self.game_input = game_input
        self.names: list[str] = [d for d in os.listdir(resource_path('assets/graphics/sprites')) if
                                 not d.startswith('.')]
        self.create_options()
        self.screen = pygame.display.get_surface()

    def create_options(self) -> None:
        w = len(self.names) * 110
        x, y = (SCREEN_WIDTH - w) // 2, 500
        for name in self.names:
            RoleOption(name, (x, y), self.game_input, self.group)
            x += 110

    def update(self) -> None:
        self.group.update()
        self.group.draw(self.screen)

    # 获取一个尚无人选择的角色
    def available(self) -> str:
        for name in self.names:
            if all(ctrl['player_name'] != name for ctrl in self.game_input.controllers.values()):
                return name

    def next(self, name: str) -> str:
        index = self.names.index(name)
        if index < len(self.names) - 1:
            index += 1
        return self.names[index]

    def previous(self, name: str) -> str:
        index = self.names.index(name)
        if index > 0:
            index -= 1
        return self.names[index]


class RoleOption(pygame.sprite.Sprite):
    def __init__(self, name: str, pos: tuple, game_input: GameInput, groups: pygame.sprite.Group):
        super().__init__(groups)
        self.name = name
        self.original = import_pic(f'assets/graphics/sprites/{name}/headshot.png')
        self.indicators = import_folder_dict('assets/graphics/icons/indicator')
        self.game_input = game_input
        self.normal_rect = pygame.Rect((0, 0, 100, 250))
        self.scaled_rect = self.normal_rect.scale_by(1.05)  # 保持中心缩放
        self.scaled_rect.topleft = self.normal_rect.topleft  # 对齐左上角
        self.normal_global_rect = self.normal_rect.move(pos)
        self.scaled_global_rect = self.normal_global_rect.scale_by(1.05)

        self.role_pic = pygame.transform.scale(self.original, self.normal_rect.size)
        self.scaled_role_pic = pygame.transform.scale(self.original, self.scaled_rect.size)
        self.colors = {'p1': 'green', 'p2': 'cyan', 'p3': 'purple', 'p4': 'magenta'}
        self.positions = [(0, 0), (65, 0), (0, 220), (65, 220)]
        self.image = pygame.surface.Surface(self.normal_rect.size)
        self.rect = None

    def update(self) -> None:
        # 绘制选中状态
        i = 0
        for dic in self.game_input.controllers.values():
            player_index = dic['player_index']
            if dic['player_name'] == self.name:
                if i == 0:
                    self.draw_scaled()
                pygame.draw.rect(self.image, self.colors[player_index], self.scaled_rect, 6)  # 边框
                i += 1
        self.draw_indicator()
        # 未选中状态
        if i == 0:
            self.draw_unselected()

    def draw_indicator(self) -> None:
        # 绘制标签
        i = 0
        dics: list[dict[str:any]] = sorted(self.game_input.controllers.values(), key=lambda d: d['player_index'])
        for dic in dics:
            if dic['player_name'] == self.name:
                player_index = dic['player_index']
                self.image.blit(self.indicators[player_index], self.positions[i])
                i += 1

    def draw_scaled(self) -> None:
        self.rect = self.scaled_global_rect
        self.image = pygame.transform.scale(self.image, self.rect.size)
        self.image.fill('yellow')
        self.image.blit(self.scaled_role_pic, (0, 0))  # 图片

    def draw_unselected(self) -> None:
        self.rect = self.normal_global_rect
        self.image = pygame.transform.scale(self.image, self.rect.size)
        pygame.transform.scale(self.image, self.rect.size)
        self.image.fill('orange')
        pygame.draw.rect(self.image, 'black', self.normal_rect, 2)  # 边框
        self.image.blit(self.role_pic, (0, 0))  # 图片
