import pygame

from ui.components.dialogue import Dialogue
from entities.player import Player
from scenes.scene import Scene, SceneStatus
from entities.sprites import DynamicBackGround


class Level(Scene):
    def __init__(self, game_input):
        super().__init__(game_input)
        self.dialogue = Dialogue(game_input)
        self.display_sprites = pygame.sprite.Group()
        self.create_player()
        DynamicBackGround(self.display_sprites)

    def create_player(self):
        for info in self.game_input.controllers.values():
            if info['player_index'] != 'p0':
                Player(info, self.display_sprites, self.dialogue)

    def run(self, dt):
        if self.dialogue.showing:
            if self.dialogue.run():
                return SceneStatus.HOME
        else:
            for sprite in sorted(self.display_sprites, key=lambda item: item.rect.y):
                sprite.update(dt)
                self.screen.blit(sprite.image, sprite.rect)
        return SceneStatus.FIGHTING

    def de_init(self):
        self.game_input.reset()
