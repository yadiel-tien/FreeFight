from random import randint, random

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from core.support import resource_path


class PlayerInfoCard:
    def __init__(self, pos, image):
        self.pos = pos
        self.image = pygame.transform.scale(image, (50, 50))
        x, y = pos
        self.blood_rect = pygame.rect.Rect(x + 70, y + 10, 150, 20)
        self.screen = pygame.display.get_surface()

    def display(self) -> None:
        self.screen.blit(self.image, self.pos)
        # 底色
        pygame.draw.rect(self.screen, 'black', self.blood_rect)
        # 边框
        pygame.draw.rect(self.screen, 'black', self.blood_rect, 2)
        rect = self.blood_rect.copy().inflate(-4, -4)
        rect.w *= 0.8
        # 血量
        pygame.draw.rect(self.screen, 'orange', rect)


class Particle(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.groups = groups
        self.ball = pygame.image.load(resource_path('assets/graphics/element/ball.png')).convert_alpha()
        size = randint(8, 18)
        self.ball = pygame.transform.scale(self.ball, (size, size))
        self.image = pygame.surface.Surface((size, size), pygame.SRCALPHA)
        # 确定ball图像的矩形用于绘制
        self.rect = self.image.get_rect(center=(randint(0, SCREEN_WIDTH), randint(SCREEN_HEIGHT - 50, SCREEN_HEIGHT)))
        self.alpha = randint(200, 255)

        self.start_time = pygame.time.get_ticks()
        self.life_time = randint(3000, 5000)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.direction = pygame.math.Vector2(randint(-2, 2), randint(-4, -1))
        self.speed = randint(20, 30)
        self.alpha_speed = -20

        self.image.blit(self.ball, (0, 0))
        self.count = 0

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        # 左右随机摆动
        if current_time // 100 > self.count:
            self.direction.x += randint(-1, 1) * 0.2
            self.count += 1
        if current_time - self.start_time > 500:
            self.alpha += dt * self.alpha_speed
            self.alpha = 0 if self.alpha < 0 else int(self.alpha)
            self.image.get_rect().inflate_ip(-2, -2)
            pygame.transform.scale(self.image, self.image.get_size())
            self.image.set_alpha(self.alpha)

        self.pos += self.speed * self.direction * dt
        self.rect.center = self.pos
        if current_time - self.start_time > self.life_time:
            self.kill()


class Particles:
    def __init__(self, probability):
        self.group = pygame.sprite.Group()
        self.screen = pygame.display.get_surface()
        self.probability = probability

    def update(self, dt):
        if random() < self.probability:
            Particle(self.group)
        self.group.update(dt)
        self.group.draw(self.screen)
