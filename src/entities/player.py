import pygame
from core.support import import_gifs_dict, import_pic
from ui.ui import PlayerInfoCard


class Player(pygame.sprite.Sprite):
    def __init__(self, info, groups, dialogue):
        super().__init__(groups)
        self.device_info = info
        self.dialogue = dialogue
        # 画面相关
        self.status = 'idle'
        self.images = import_gifs_dict(f'assets/graphics/sprites/{info["player_name"]}')
        self.image_index = 0
        self.image = self.images['idle'][0]
        self.display_surf = pygame.display.get_surface()
        player_index = int(info['player_index'][1:])
        self.pos = pygame.math.Vector2(300 * player_index, 700)
        self.rect = self.image.get_rect(midbottom=self.pos)
        self.speed = 150
        self.direction = pygame.math.Vector2()
        self.to_right = True

        # 临时血条展示
        avatar = import_pic(f'assets/graphics/sprites/{info["player_name"]}/avatar.png')
        self.blood_ui = PlayerInfoCard(((player_index - 1) * 300 + 20, 20), avatar)

        # 跳跃控制
        self.gravity = 800
        self.ground_y = 0
        self.jump_velocity = 0
        self.jump_strength = 500

    def update_image(self, dt):
        # frames是一个系列动画图片的列表
        frames = self.images[self.status]
        # 更改当前帧
        self.image_index += dt * 5
        # 动画结束后动作
        if self.image_index >= len(frames):
            self.image_index = 0
            # 跳起后保持跳起最后一帧姿势
            if self.status in ['jump', 'jump attack']:
                self.image_index = len(frames) - 1
            # 动画播放结束还原
            if self.status in ['attack', 'super move 1', 'super move 2', 'finisher',
                               'combo', 'dash attack']:
                self.status = 'idle'
            if self.status == 'super move 3':
                self.status = 'jump'
                self.jump_velocity = 0

        # 更改图片，缩放图片
        original = frames[int(self.image_index)]
        w, h = original.get_size()[0], original.get_size()[1]
        scaled = pygame.transform.scale(original, (w * 0.5, h * 0.5))
        # 左右转向
        self.image = pygame.transform.flip(scaled, self.to_right, False)

    def update(self, dt):
        self.handle_input()
        self.update_image(dt)
        self.mov(dt)
        self.blood_ui.display()

    def mov(self, dt):
        if self.direction.magnitude() == 0 and self.status in ['walk', 'run']:
            self.status = 'idle'
        # 不能移动的动画
        if self.status in ['idle', 'super move 1', 'super move 2', 'super move 3', 'finisher', 'attack']:
            self.direction.update(0, 0)

        # 计算跳起后垂直运动。落地后还原
        if self.status in ['jump', 'jump attack']:
            if self.pos[1] <= self.ground_y:
                self.jump_velocity += self.gravity * dt
                self.pos.y += self.jump_velocity * dt
            else:
                self.jump_velocity = 0
                self.status = 'idle'
        # 计算位置
        self.pos += self.direction * self.speed * dt
        self.rect = self.image.get_rect(midbottom=self.pos)

    def handle_input(self):
        ctrl = self.device_info['controller']
        # 切换状态
        if self.status == 'idle':
            for key in ['left', 'right', 'up', 'down']:
                if ctrl.performed(key):
                    self.status = 'walk'
            if ctrl.performed('run left') or ctrl.performed('run right'):
                self.status = 'run'
        elif self.status != 'walk':
            ctrl.last_released_key = ''  # 避免在其他动画中提前触发跑步事件

        if self.status in ['idle', 'walk']:
            for key in ['super move 1', 'super move 2', 'finisher', 'jump', 'attack']:
                if ctrl.performed(key):
                    self.status = key
                    self.image_index = 0
                    if key == 'jump':  # 设置跳起初始状态
                        self.ground_y = self.pos[1]
                        self.jump_velocity = -self.jump_strength

        if self.status in ['walk', 'jump', 'jump attack']:
            # 水平运动状态
            if ctrl.performed('left'):
                self.direction.x = -1
                self.to_right = False
            elif ctrl.performed('right'):
                self.direction.x = 1
                self.to_right = True
            else:
                self.direction.x = 0

        if self.status in ['walk', 'run', 'dash attack']:
            # 垂直运动状态
            if ctrl.performed('up'):
                self.direction.y = -1
            elif ctrl.performed('down'):
                self.direction.y = 1
            else:
                self.direction.y = 0

        if self.status == 'run':
            if ctrl.performed('run left'):
                self.direction.x = -3
            elif ctrl.performed('run right'):
                self.direction.x = 3
            elif ctrl.performed('attack'):
                if 'dash attack' in self.images:  # 部分人物确动画
                    self.status = 'dash attack'
                    self.image_index = 0
                    self.direction.x *= 1.5
            else:
                self.direction.x = 0

        if self.status == 'jump':
            if ctrl.performed('attack'):
                if 'jump attack' in self.images:  # 部分人物确动画
                    self.status = 'jump attack'
            elif ctrl.performed('super move 1'):
                self.status = 'super move 3'
            # 跳起水平速度增益
            self.direction.x *= 1.5

        if ctrl.performed('menu'):
            self.dialogue.show('确定要退出游戏吗？')
