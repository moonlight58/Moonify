import os
import tempfile
import unittest

from library import list_playlists, list_track_files, playlist_has_tracks


class LibraryTest(unittest.TestCase):
    def test_list_playlists_returns_sorted_folders_only(self):
        with tempfile.TemporaryDirectory() as music:
            os.mkdir(os.path.join(music, "B"))
            os.mkdir(os.path.join(music, "A"))
            with open(os.path.join(music, "track.mp3"), "w", encoding="utf-8"):
                pass

            playlists = list_playlists(music)

        self.assertEqual([playlist.name for playlist in playlists], ["A", "B"])

    def test_list_track_files_returns_sorted_mp3_files_case_insensitive(self):
        with tempfile.TemporaryDirectory() as playlist:
            for name in ["b.MP3", "notes.txt", "a.mp3"]:
                with open(os.path.join(playlist, name), "w", encoding="utf-8"):
                    pass

            tracks = list_track_files(playlist)

        self.assertEqual([t.filename for t in tracks], ["a.mp3", "b.MP3"])

    def test_playlist_has_tracks(self):
        with tempfile.TemporaryDirectory() as playlist:
            self.assertFalse(playlist_has_tracks(playlist))
            with open(os.path.join(playlist, "song.mp3"), "w", encoding="utf-8"):
                pass
            self.assertTrue(playlist_has_tracks(playlist))


if __name__ == "__main__":
    unittest.main()
