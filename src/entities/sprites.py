import pygame
from src.core.support import import_gifs_dict


class DynamicBackground(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        # 舞台总宽度比屏幕宽 1000 (左右各 500)
        # 所以背景图需要拉伸到足够覆盖这个范围
        from src.core.constants import SCREEN_WIDTH, SCREEN_HEIGHT
        self.width = SCREEN_WIDTH + 1000
        self.height = SCREEN_HEIGHT
        
        # 初始位置：居中放置在扩展舞台上
        self.pos = (-500, 0)
        self.frames = import_gifs_dict('assets/graphics/background')['bg']
        self.image = pygame.transform.scale(self.frames[0], (self.width, self.height))
        self.rect = self.image.get_rect(topleft=self.pos)
        self.frame_index = 0

    def update(self, dt):
        self.frame_index += 5 * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        original = self.frames[int(self.frame_index)]
        # 每一帧都拉伸到大舞台尺寸
        self.image = pygame.transform.scale(original, (self.width, self.height))
