import unittest
from unittest.mock import MagicMock
from player import Player
from engine import PlaybackEngine
from models import Track
import os

class MockEngine(PlaybackEngine):
    def __init__(self):
        self.loaded_path = None
        self.playing = False
        self.paused = False
        self.volume = 0.5

    def load(self, path: str):
        self.loaded_path = path

    def play(self):
        self.playing = True

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.playing = False

    def get_pos_ms(self) -> int:
        return 1000

    def is_busy(self) -> bool:
        return self.playing and not self.paused

    def set_volume(self, volume: float):
        self.volume = volume

    def get_volume(self) -> float:
        return self.volume

class PlayerTest(unittest.TestCase):
    def setUp(self):
        self.music_folder = "music/liked songs"
        self.engine = MockEngine()
        self.player = Player(self.music_folder, engine=self.engine)

    def test_play_loads_and_plays_current_track(self):
        self.player.play()
        self.assertTrue(self.engine.playing)
        self.assertIsNotNone(self.engine.loaded_path)
        self.assertFalse(self.player.paused)

    def test_pause_toggles_engine_and_state(self):
        self.player.play()
        self.player.pause()
        self.assertTrue(self.engine.paused)
        self.assertTrue(self.player.paused)

    def test_next_track_advances_queue_and_plays(self):
        initial_track = self.player.queue.current()
        self.player.next_track()
        next_track = self.player.queue.current()
        self.assertNotEqual(initial_track, next_track)
        self.assertTrue(self.engine.playing)

    def test_event_emission(self):
        events_received = []
        self.player.events.subscribe("track_started", lambda data: events_received.append(data))
        
        self.player.play()
        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0]["title"], self.player.queue.current().title)

if __name__ == "__main__":
    unittest.main()
