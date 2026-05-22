import unittest
from contextlib import redirect_stdout
from io import StringIO

from presence import DiscordPresence


TRACK = {
    "path": "song.mp3",
    "title": "Song",
    "artist": "Artist",
}


class FakeTransport:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.shown = []
        self.closed = False

    def is_enabled(self):
        return self.enabled

    def show_track(self, title, artist, cover_url=None):
        self.shown.append({
            "title": title,
            "artist": artist,
            "cover_url": cover_url,
        })

    def close(self):
        self.closed = True


class FakeCoverProvider:
    def __init__(self, cover_url=None, error=None):
        self.cover_url = cover_url
        self.error = error
        self.tracks = []

    def cover_url_for(self, track):
        self.tracks.append(track)
        if self.error:
            raise self.error
        return self.cover_url


class DiscordPresenceTest(unittest.TestCase):
    def test_show_track_uses_cover_provider_and_transport(self):
        transport = FakeTransport()
        cover_provider = FakeCoverProvider(cover_url="https://example.test/cover.jpg")
        presence = DiscordPresence(transport=transport, cover_provider=cover_provider)

        presence._show_track(TRACK)

        self.assertEqual(cover_provider.tracks, [TRACK])
        self.assertEqual(transport.shown, [{
            "title": "Song",
            "artist": "Artist",
            "cover_url": "https://example.test/cover.jpg",
        }])

    def test_cover_failure_still_publishes_track_without_cover(self):
        transport = FakeTransport()
        cover_provider = FakeCoverProvider(error=RuntimeError("upload failed"))
        presence = DiscordPresence(transport=transport, cover_provider=cover_provider)

        with redirect_stdout(StringIO()):
            presence._show_track(TRACK)

        self.assertEqual(transport.shown, [{
            "title": "Song",
            "artist": "Artist",
            "cover_url": None,
        }])

    def test_disabled_transport_ignores_started_track(self):
        transport = FakeTransport(enabled=False)
        presence = DiscordPresence(transport=transport, cover_provider=FakeCoverProvider())

        presence.track_started(TRACK)

        self.assertIsNone(presence.pending_track)

    def test_close_closes_transport(self):
        transport = FakeTransport()
        presence = DiscordPresence(transport=transport, cover_provider=FakeCoverProvider())

        presence.close()

        self.assertTrue(transport.closed)


if __name__ == "__main__":
    unittest.main()
