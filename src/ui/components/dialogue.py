import pygame

from src.core.support import resource_path


class Dialogue:
    def __init__(self, game_input, surface: pygame.Surface = None):
        self.screen = surface if surface else pygame.display.get_surface()
        self.game_input = game_input
        self.device_info = None
        
        # 弹窗本体表面
        self.image = pygame.Surface((400, 180), pygame.SRCALPHA)
        self.border_rect = self.image.get_rect()
        self.rect = self.image.get_rect(center=(640, 360)) 

        # 静态模糊背景图
        try:
            bg_img = pygame.image.load(resource_path('assets/graphics/background/background_blurred.png'))
            self.static_bg = pygame.transform.scale(bg_img, (1280, 720))
            overlay = pygame.Surface((1280, 720))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(100)
            self.static_bg.blit(overlay, (0, 0))
        except:
            self.static_bg = pygame.Surface((1280, 720))
            self.static_bg.fill((0, 0, 0))
            self.static_bg.set_alpha(180)

        self.text = ''
        self.showing = False
        
        # 内部计时器：用于避免触发菜单的那个按键被误认为是“确认”操作
        self.input_lock_timer = 0

    def draw_text(self):
        from src.core.config import config
        lang = config.get('system', 'language')
        path = resource_path('assets/font/SimHei.ttf')
        font_msg = pygame.font.Font(path, 24)
        
        # 绘制背景框和边框
        pygame.draw.rect(self.image, (30, 30, 30), self.border_rect, border_radius=12)
        pygame.draw.rect(self.image, 'orange', self.border_rect, 2, border_radius=12)

        # 1. 绘制消息文本
        text_surf = font_msg.render(self.text, True, 'white')
        text_rect = text_surf.get_rect(midtop=self.border_rect.midtop)
        text_rect.y = 45
        self.image.blit(text_surf, text_rect)

        # 2. 获取提示内容
        if isinstance(self.device_info, dict):
            ctrl = self.device_info['controller']
            if hasattr(ctrl, 'get_button_name'): # 手柄
                conf_hint = ctrl.get_button_name(0)
                cancel_hint = ctrl.get_button_name(1)
            else: # 键盘
                conf_hint = "⏎"
                cancel_hint = "ESC"
        else:
            conf_hint = self.game_input.get_confirm_hint(lang)
            cancel_hint = self.game_input.get_menu_hint(lang)

        conf_label = '确定' if lang == 'zh_CN' else 'CONFIRM'
        cancel_label = '取消' if lang == 'zh_CN' else 'CANCEL'
        
        # 3. 使用统一渲染
        from src.ui.text import Menu
        hints_data = [(conf_hint, conf_label), (cancel_hint, cancel_label)]
        tip_surf = Menu.get_tip_surf_multi(hints_data)
        tip_rect = tip_surf.get_rect(midbottom=(self.border_rect.centerx, self.border_rect.bottom - 35))
        self.image.blit(tip_surf, tip_rect)

    def show(self, text, device_info=None):
        if not device_info:
            device_info = list(self.game_input.controllers.values())
        self.text = text
        self.device_info = device_info
        self.showing = True
        
        # 核心修复：强制重置发起设备的按键释放状态
        # 这样可以确保进入弹窗后的第一下按键立刻被识别，而不会被之前的状态“吞掉”
        if isinstance(self.device_info, dict):
            self.device_info['controller'].release_all()
        elif isinstance(self.device_info, list):
            for item in self.device_info:
                item['controller'].release_all()
                
        # 设置一个微乎其微的冷却时间 (50ms)，仅用于消除物理按键抖动
        self.input_lock_timer = pygame.time.get_ticks() + 50

    def run(self):
        if self.showing:
            # 1. 绘制背景
            self.screen.blit(self.static_bg, (0, 0))
            
            # 2. 绘制弹窗
            self.image.fill((0, 0, 0, 0))
            self.draw_text()
            self.screen.blit(self.image, self.rect)
            
            # 3. 检查输入 (仅在冷却结束后)
            if pygame.time.get_ticks() > self.input_lock_timer:
                if isinstance(self.device_info, list):
                    for item in self.device_info:
                        res = self.handle_input(item)
                        if res is not None: return res
                else:
                    return self.handle_input(self.device_info)
        return None

    def handle_input(self, device_info):
        ctrl = device_info['controller']
        if ctrl.ui_performed('confirm'):
            self.showing = False
            return True
        if ctrl.ui_performed('cancel'):
            self.showing = False
            return False
        return None
