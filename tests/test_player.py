import unittest
from library import LoadedPlaylist, Playlist
from player import Player
from engine import PlaybackEngine
from models import Track


def track(filename):
    return Track(
        path=filename,
        filename=filename,
        artist="Test Artist",
        title=filename.rsplit(".", 1)[0],
        duration=0,
    )


class FakeLibrary:
    def __init__(self, tracks):
        self.tracks = tracks
        self.loaded_folders = []

    def load_tracks(self, folder, shuffle=False):
        self.loaded_folders.append((folder, shuffle))
        return self.tracks[:]

    def load_playlist(self, folder, shuffle=False):
        return LoadedPlaylist(
            playlist=Playlist(name=folder, path=folder),
            tracks=self.load_tracks(folder, shuffle=shuffle),
        )

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
        self.library = FakeLibrary([track("a.mp3"), track("b.mp3")])
        self.player = Player(self.music_folder, engine=self.engine, library=self.library)

    def test_loads_tracks_from_folder_through_library(self):
        self.assertEqual(self.library.loaded_folders, [(self.music_folder, False)])
        self.assertEqual([track.filename for track in self.player.get_tracks()], ["a.mp3", "b.mp3"])

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

    def test_pause_command_is_idempotent(self):
        self.player.play()

        self.assertTrue(self.player.handle_command("pause"))
        self.assertFalse(self.player.handle_command("pause"))

        self.assertTrue(self.engine.paused)
        self.assertTrue(self.player.paused)

    def test_resume_command_is_idempotent(self):
        self.player.play()
        self.player.pause()

        self.assertTrue(self.player.handle_command("resume"))
        self.assertFalse(self.player.handle_command("resume"))

        self.assertFalse(self.engine.paused)
        self.assertFalse(self.player.paused)

    def test_volume_command_adjusts_engine_volume(self):
        self.player.handle_command("volume_up")
        self.assertEqual(self.engine.volume, 0.6)

    def test_unknown_command_is_ignored(self):
        self.assertFalse(self.player.handle_command("unknown"))

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

    def test_snapshot_contains_current_playback_state(self):
        self.player.play()

        snapshot = self.player.snapshot()

        self.assertEqual(snapshot.title, "a")
        self.assertEqual(snapshot.artist, "Test Artist")
        self.assertEqual(snapshot.elapsed_seconds, 1)
        self.assertEqual(snapshot.volume, 0.5)
        self.assertEqual(snapshot.track_count, 2)
        self.assertEqual([(entry.offset, entry.track.filename) for entry in snapshot.upcoming], [(1, "b.mp3")])

    def test_empty_snapshot_uses_fallback_current_track_values(self):
        player = Player(self.music_folder, engine=self.engine, library=FakeLibrary([]))

        snapshot = player.snapshot()

        self.assertEqual(snapshot.title, "No track")
        self.assertEqual(snapshot.artist, "Unknown Artist")
        self.assertEqual(snapshot.duration, 0)
        self.assertEqual(snapshot.upcoming, [])

if __name__ == "__main__":
    unittest.main()
