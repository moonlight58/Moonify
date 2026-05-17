import unittest

from utils import parse_filename


class ParseFilenameTest(unittest.TestCase):
    def test_parses_artist_and_title(self):
        self.assertEqual(parse_filename("THÉA - CAVALE! CAVALE!.mp3"), ("THÉA", "CAVALE! CAVALE!"))

    def test_parses_multiple_artists(self):
        self.assertEqual(parse_filename("Artist A, Artist B - Track.mp3"), ("Artist A, Artist B", "Track"))

    def test_falls_back_when_separator_is_missing(self):
        self.assertEqual(parse_filename("Track Only.mp3"), ("Unknown Artist", "Track Only"))


if __name__ == "__main__":
    unittest.main()
