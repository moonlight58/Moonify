import tempfile
import unittest
from pathlib import Path

from library import Library


class LibraryTest(unittest.TestCase):
    def setUp(self):
        self.library = Library()

    def test_list_playlists_returns_sorted_folders_only(self):
        with tempfile.TemporaryDirectory() as music:
            music_path = Path(music)
            (music_path / "B").mkdir()
            (music_path / "A").mkdir()
            (music_path / "track.mp3").write_text("", encoding="utf-8")

            playlists = self.library.list_playlists(music)

        self.assertEqual([playlist.name for playlist in playlists], ["A", "B"])

    def test_list_track_files_returns_sorted_mp3_files_case_insensitive(self):
        with tempfile.TemporaryDirectory() as playlist:
            playlist_path = Path(playlist)
            for name in ["b.MP3", "notes.txt", "a.mp3"]:
                (playlist_path / name).write_text("", encoding="utf-8")

            tracks = self.library.load_tracks(playlist)

        self.assertEqual([t.filename for t in tracks], ["a.mp3", "b.MP3"])
        self.assertEqual([t.duration for t in tracks], [0, 0])

    def test_playlist_has_tracks(self):
        with tempfile.TemporaryDirectory() as playlist:
            playlist_path = Path(playlist)
            self.assertFalse(self.library.playlist_has_tracks(playlist))
            (playlist_path / "song.mp3").write_text("", encoding="utf-8")
            self.assertTrue(self.library.playlist_has_tracks(playlist))


if __name__ == "__main__":
    unittest.main()
