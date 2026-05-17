import pygame

from src.core.support import resource_path


class Dialogue:
    def __init__(self, game_input, surface: pygame.Surface = None):
        # 如果没有传入 surface，则尝试获取当前显示表面 (兼容旧代码或延迟设置)
        self.screen = surface if surface else pygame.display.get_surface()
        self.game_input = game_input
        self.device_info = None
        # 背景
        self.image = pygame.Surface((450, 250), pygame.SRCALPHA)
        self.image.set_alpha(200)
        # 居中 (始终相对于 1280x720 的逻辑画布)
        self.border_rect = self.image.get_rect()
        self.rect = self.image.get_rect(center=(640, 360)) 

        self.text = ''

        # 显示开关
        self.showing = False

    def draw_text(self):
        path = resource_path('assets/font/SimHei.ttf')
        font = pygame.font.Font(path, 30)
        text_surf = font.render(self.text, False, 'white')
        # 提示居中，y为50
        text_rect = text_surf.get_rect(midtop=self.border_rect.midtop)
        text_rect.y = 50
        # 选项居中，y为50
        options_surf = font.render('A 确认        B 取消', False, 'white')
        options_rect = options_surf.get_rect(midtop=self.border_rect.midtop)
        options_rect.y = 150

        # 绘制文字
        self.image.blit(text_surf, text_rect)
        self.image.blit(options_surf, options_rect)
        # 绘制圆圈
        pos = options_rect.x + 7.5, options_rect.y + 15
        pygame.draw.circle(self.image, 'green', pos, 20, 5)
        pygame.draw.circle(self.image, 'red', (pos[0] + 209, pos[1]), 20, 5)

    def show(self, text, device_info=None):
        if not device_info:
            device_info = list(self.game_input.controllers.values())
        self.text = text
        self.device_info = device_info
        self.showing = True

    # 返回True代表确认，False代表取消
    def run(self):
        if self.showing:
            # 确保 screen 引用是最新的 (以防在初始化后才设置)
            if not self.screen: self.screen = pygame.display.get_surface()
            
            self.image.fill('black')
            self.draw_text()
            self.screen.blit(self.image, self.rect)
            # 检查选择
            if isinstance(self.device_info, list):
                # 如果是列表，遍历检查是否有确认或取消的输入
                return any(item for item in self.device_info if self.handle_input(item))
            else:
                return self.handle_input(self.device_info)

    def handle_input(self, device_info):
        ctrl = device_info['controller']
        if ctrl.performed('confirm'):
            self.showing = False
            return True
        if ctrl.performed('cancel'):
            self.showing = False
        return False
