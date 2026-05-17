import pygame
from src.core.support import import_gifs_dict


class DynamicBackGround(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.pos = (0, 0)
        self.frames = import_gifs_dict('assets/graphics/background')['bg']
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=self.pos)
        self.frame_index = 0

    def update(self, dt):
        self.frame_index += 5 * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        original = self.frames[int(self.frame_index)]
        self.image = pygame.transform.scale(original, (1280, 768))
