import pygame

from src.ui.components.dialogue import Dialogue
from src.entities.player import Player
from src.scenes.scene import Scene, SceneStatus
from src.entities.sprites import DynamicBackGround


class Level(Scene):
    def __init__(self, game_input, surface: pygame.Surface):
        super().__init__(game_input, surface)
        self.dialogue = Dialogue(game_input, self.screen)
        self.display_sprites = pygame.sprite.Group()
        self.create_player()
        DynamicBackGround(self.display_sprites)

    def create_player(self):
        for info in self.game_input.controllers.values():
            if info['player_index'] != 'p0':
                Player(info, self.display_sprites, self.dialogue, self.screen)

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
