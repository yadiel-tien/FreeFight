import pygame
from settings import *

from core.support import resource_path

class UIWidget:
    def __init__(self, label, pos, size=(300, 40)):
        self.label = label
        self.pos = pos
        self.size = size
        self.rect = pygame.Rect(pos, size)
        self.selected = False
        # 使用项目自带的黑体字体支持中文
        font_path = resource_path('assets/font/SimHei.ttf')
        self.font = pygame.font.Font(font_path, 24)
        
    def draw(self, surface):
        pass

class Slider(UIWidget):
    def __init__(self, label, pos, value, min_val=0.0, max_val=1.0):
        super().__init__(label, pos)
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.slider_rect = pygame.Rect(pos[0] + 150, pos[1] + 15, 140, 10)
        self.dragging = False

    def handle_mouse(self, mouse_pos, is_down, is_moving=False):
        # 核心逻辑：只要鼠标松开，必须停止拖拽
        if not is_down:
            self.dragging = False
            return None

        # 如果鼠标按下且之前没在拖拽，检查是否点中了滑块区域
        if is_down and not self.dragging:
            if self.slider_rect.inflate(30, 30).collidepoint(mouse_pos):
                self.dragging = True

        # 处于拖拽状态时，更新数值
        if self.dragging:
            # 根据鼠标位置计算数值，限制在滑块条范围内
            rel_x = max(0, min(mouse_pos[0] - self.slider_rect.x, self.slider_rect.w))
            self.value = self.min_val + (rel_x / self.slider_rect.w) * (self.max_val - self.min_val)
            return self.value
        
        return None

    def update_value(self, direction):
        step = 0.05
        if direction == 'left':
            self.value = max(self.min_val, self.value - step)
        elif direction == 'right':
            self.value = min(self.max_val, self.value + step)
        return self.value

    def draw(self, surface):
        # 标签文字
        color = 'orange' if self.selected else 'white'
        txt = self.font.render(self.label, True, color)
        surface.blit(txt, (self.pos[0], self.pos[1] + 5))
        
        # 滑块底色
        pygame.draw.rect(surface, (50, 50, 50), self.slider_rect, border_radius=5)
        
        # 填充进度
        fill_width = int((self.value - self.min_val) / (self.max_val - self.min_val) * self.slider_rect.w)
        fill_rect = pygame.Rect(self.slider_rect.topleft, (fill_width, self.slider_rect.h))
        pygame.draw.rect(surface, color, fill_rect, border_radius=5)
        
        # 滑块头
        handle_pos = (self.slider_rect.x + fill_width, self.slider_rect.centery)
        pygame.draw.circle(surface, 'white' if self.selected or self.dragging else color, handle_pos, 8)

class Selector(UIWidget):
    def __init__(self, label, pos, options, current_index=0):
        super().__init__(label, pos)
        self.options = options
        self.index = current_index

    def update_value(self, direction):
        if direction == 'left':
            self.index = (self.index - 1) % len(self.options)
        elif direction == 'right':
            self.index = (self.index + 1) % len(self.options)
        return self.options[self.index]

    def draw(self, surface):
        color = 'orange' if self.selected else 'white'
        txt = self.font.render(self.label, True, color)
        surface.blit(txt, (self.pos[0], self.pos[1] + 5))
        
        # 当前选项文字
        opt_txt = self.font.render(f"< {self.options[self.index]} >", True, color)
        surface.blit(opt_txt, (self.pos[0] + 150, self.pos[1] + 5))

class Toggle(UIWidget):
    def __init__(self, label, pos, value):
        super().__init__(label, pos)
        self.value = value # True/False
        self.toggle_rect = pygame.Rect(pos[0] + 150, pos[1] + 10, 50, 25)

    def update_value(self, direction=None):
        # 无论是按左、右、还是确认，都是取反
        self.value = not self.value
        return self.value

    def draw(self, surface):
        color = 'orange' if self.selected else 'white'
        txt = self.font.render(self.label, True, color)
        surface.blit(txt, (self.pos[0], self.pos[1] + 5))
        
        # 绘制开关背景
        bg_color = (80, 80, 80) if not self.value else (120, 80, 0)
        pygame.draw.rect(surface, bg_color, self.toggle_rect, border_radius=12)
        pygame.draw.rect(surface, color, self.toggle_rect, 2, border_radius=12)
        
        # 绘制开关头 (小球)
        circle_x = self.toggle_rect.x + (37 if self.value else 13)
        pygame.draw.circle(surface, color, (circle_x, self.toggle_rect.centery), 9)
        
        # 绘制状态文字 (开/关)
        status_txt = self.font.render("开" if self.value else "关", True, color)
        surface.blit(status_txt, (self.toggle_rect.right + 15, self.pos[1] + 5))

class KeyBinder(UIWidget):
    def __init__(self, label, pos, current_key, is_joystick=False):
        super().__init__(label, pos)
        self.key = current_key
        self.waiting_for_input = False
        self.is_joystick = is_joystick

    def draw(self, surface):
        color = 'orange' if self.selected else 'white'
        if self.waiting_for_input: color = 'yellow'
        
        txt = self.font.render(self.label, True, color)
        surface.blit(txt, (self.pos[0], self.pos[1] + 5))
        
        display_val = str(self.key)
        if self.is_joystick:
            display_val = f"Btn {self.key}"
        
        val_txt = self.font.render(f"[{display_val}]" if not self.waiting_for_input else "[按下任意键/按钮]", True, color)
        surface.blit(val_txt, (self.pos[0] + 150, self.pos[1] + 5))

class Button(UIWidget):
    def __init__(self, label, pos, size=(300, 40)):
        super().__init__(label, pos, size)
    
    def draw(self, surface):
        color = 'orange' if self.selected else 'white'
        # 绘制按钮框
        pygame.draw.rect(surface, color, self.rect, 2, border_radius=5)
        if self.selected:
            bg_rect = self.rect.inflate(-4, -4)
            surface.fill((255, 165, 0, 50), bg_rect, special_flags=pygame.BLEND_RGBA_ADD)
            
        txt = self.font.render(self.label, True, color)
        txt_rect = txt.get_rect(center=self.rect.center)
        surface.blit(txt, txt_rect)
