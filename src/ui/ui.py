from random import randint, random

import pygame

from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.core.support import resource_path


class PlayerInfoCard:
    def __init__(self, player_index, image, surface: pygame.Surface):
        self.player_index = player_index
        self.screen = surface
        self.avatar = pygame.transform.scale(image, (64, 64)) # 放大头像，更具冲击力
        
        from src.settings import SCREEN_WIDTH
        if player_index == 'p1':
            # P1 (左侧)：头像在最左边，血条向右伸展
            self.avatar_pos = (20, 20)
            self.blood_rect = pygame.rect.Rect(95, 30, 480, 24)
        else:
            # P2 (右侧)：头像在最右边，血条向左伸展
            self.avatar_pos = (SCREEN_WIDTH - 20 - 64, 20)
            self.blood_rect = pygame.rect.Rect(SCREEN_WIDTH - 95 - 480, 30, 480, 24)

    def display(self, health, shadow_health, max_health) -> None:
        # 1. 绘制头像
        self.screen.blit(self.avatar, self.avatar_pos)
        
        # 2. 绘制黑色血条背景底槽与细白描边
        pygame.draw.rect(self.screen, (20, 20, 20), self.blood_rect, border_radius=4)
        pygame.draw.rect(self.screen, (80, 80, 80), self.blood_rect, 1, border_radius=4)
        
        # 3. 计算比例
        shadow_ratio = max(0.0, min(1.0, shadow_health / max_health))
        actual_ratio = max(0.0, min(1.0, health / max_health))
        
        # 4. 绘制红色残血阴影层 (Damage Shadow Bar)
        shadow_rect = self.blood_rect.copy().inflate(-4, -4)
        shadow_w = int(shadow_rect.w * shadow_ratio)
        
        if self.player_index == 'p1':
            # P1 正常从左往右增长
            shadow_rect.w = shadow_w
        else:
            # P2 镜像：右对齐往左生长
            shadow_rect.x = shadow_rect.right - shadow_w
            shadow_rect.w = shadow_w
            
        pygame.draw.rect(self.screen, (200, 30, 30), shadow_rect, border_radius=2)
        
        # 5. 绘制实际当前血条层 (Actual Health Bar)
        rect = self.blood_rect.copy().inflate(-4, -4)
        actual_w = int(rect.w * actual_ratio)
        
        if self.player_index == 'p1':
            rect.w = actual_w
        else:
            rect.x = rect.right - actual_w
            rect.w = actual_w
            
        # 根据实际血量比例动态变色 (绿 -> 黄 -> 红)
        if actual_ratio > 0.5:
            color = (0, 230, 100) # 亮绿
        elif actual_ratio > 0.2:
            color = (240, 200, 10) # 亮黄
        else:
            color = (255, 30, 30) # 亮红
            
        pygame.draw.rect(self.screen, color, rect, border_radius=2)


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
