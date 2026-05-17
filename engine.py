from abc import ABC, abstractmethod
import pygame
import os

class PlaybackEngine(ABC):
    @abstractmethod
    def load(self, path: str):
        pass

    @abstractmethod
    def play(self):
        pass

    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def resume(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def get_pos_ms(self) -> int:
        pass

    @abstractmethod
    def is_busy(self) -> bool:
        pass

    @abstractmethod
    def set_volume(self, volume: float):
        pass

    @abstractmethod
    def get_volume(self) -> float:
        pass

class PygameEngine(PlaybackEngine):
    def __init__(self):
        pygame.mixer.init()

    def load(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Audio file not found: {path}")
        pygame.mixer.music.load(path)

    def play(self):
        pygame.mixer.music.play()

    def pause(self):
        pygame.mixer.music.pause()

    def resume(self):
        pygame.mixer.music.unpause()

    def stop(self):
        pygame.mixer.music.stop()

    def get_pos_ms(self) -> int:
        return pygame.mixer.music.get_pos()

    def is_busy(self) -> bool:
        return pygame.mixer.music.get_busy()

    def set_volume(self, volume: float):
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    def get_volume(self) -> float:
        return pygame.mixer.music.get_volume()
