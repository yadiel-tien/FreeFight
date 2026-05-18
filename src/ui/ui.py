from random import randint, random

import pygame

from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.core.support import resource_path


class PlayerInfoCard:
    def __init__(self, pos, image, surface: pygame.Surface):
        self.pos = pos
        self.image = pygame.transform.scale(image, (50, 50))
        x, y = pos
        self.blood_rect = pygame.rect.Rect(x + 70, y + 10, 150, 20)
        self.screen = surface

    def display(self, health, max_health) -> None:
        self.screen.blit(self.image, self.pos)
        # 底色
        pygame.draw.rect(self.screen, 'black', self.blood_rect)
        # 边框
        pygame.draw.rect(self.screen, 'black', self.blood_rect, 2)
        
        # 计算比例
        ratio = max(0.0, min(1.0, health / max_health))
        rect = self.blood_rect.copy().inflate(-4, -4)
        rect.w *= ratio
        
        # 颜色变化: 绿色 -> 黄色 -> 红色
        if ratio > 0.5:
            color = (0, 255, 0) # Green
        elif ratio > 0.2:
            color = (255, 255, 0) # Yellow
        else:
            color = (255, 0, 0) # Red
            
        # 血量
        pygame.draw.rect(self.screen, color, rect)


class HitSpark(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        # 绘制一个简单的闪光十字
        pygame.draw.line(self.image, (255, 255, 255), (0, 20), (40, 20), 4)
        pygame.draw.line(self.image, (255, 255, 255), (20, 0), (20, 40), 4)
        # 内部核心
        pygame.draw.circle(self.image, (255, 255, 0), (20, 20), 10)
        
        self.rect = self.image.get_rect(center=pos)
        self.start_time = pygame.time.get_ticks()
        self.duration = 100 # 极短的闪烁

    def update(self, dt):
        if pygame.time.get_ticks() - self.start_time > self.duration:
            self.kill()


class Particle(pygame.sprite.Sprite):
    # 类属性缓存图像，避免重复加载
    cached_ball = None

    def __init__(self, groups):
        super().__init__(groups)
        if Particle.cached_ball is None:
            Particle.cached_ball = pygame.image.load(resource_path('assets/graphics/element/ball.png')).convert_alpha()
        
        size = randint(8, 18)
        self.original_image = pygame.transform.scale(Particle.cached_ball, (size, size))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(randint(0, SCREEN_WIDTH), randint(SCREEN_HEIGHT - 50, SCREEN_HEIGHT)))
        
        self.alpha = float(randint(200, 255))
        self.start_time = pygame.time.get_ticks()
        self.life_time = randint(3000, 5000)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.direction = pygame.math.Vector2(randint(-2, 2), randint(-4, -1))
        self.speed = randint(20, 30)
        self.alpha_speed = -30 # 稍微快一点的淡出

        self.count = 0

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        
        # 左右随机摆动
        if current_time // 100 > self.count:
            self.direction.x += randint(-1, 1) * 0.2
            self.count += 1
            
        if elapsed > 500:
            self.alpha += dt * self.alpha_speed
            if self.alpha <= 0:
                self.kill()
                return
            
            # 重新创建带 alpha 的图像，避免 set_alpha 在某些混色模式下的方框问题
            self.image = self.original_image.copy()
            # 这种方式对带有 SRCALPHA 的 Surface 最稳定
            alpha_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            alpha_surf.fill((255, 255, 255, int(self.alpha)))
            self.image.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.pos += self.speed * self.direction * dt
        self.rect.center = self.pos
        if elapsed > self.life_time:
            self.kill()


class Particles:
    def __init__(self, probability, surface: pygame.Surface):
        self.group = pygame.sprite.Group()
        self.screen = surface
        self.probability = probability

    def update(self, dt):
        if random() < self.probability:
            Particle(self.group)
        self.group.update(dt)
        self.group.draw(self.screen)
