import unittest

from playback_queue import TrackQueue
from models import Track


class TrackQueueTest(unittest.TestCase):
    def test_move_next_stops_at_end_without_loop(self):
        tracks = [Track(path="a.mp3"), Track(path="b.mp3")]
        queue = TrackQueue(tracks)

        self.assertTrue(queue.move_next(loop=False))
        self.assertFalse(queue.move_next(loop=False))
        self.assertEqual(queue.current().filename, "b.mp3")

    def test_move_next_wraps_with_loop(self):
        tracks = [Track(path="a.mp3"), Track(path="b.mp3")]
        queue = TrackQueue(tracks)
        queue.move_next(loop=True)

        self.assertTrue(queue.move_next(loop=True))
        self.assertEqual(queue.current().filename, "a.mp3")

    def test_queue_next_preserves_current_track_when_moving_prior_track(self):
        tracks = [Track(path="a.mp3"), Track(path="b.mp3"), Track(path="c.mp3"), Track(path="d.mp3")]
        queue = TrackQueue(tracks)
        queue.select(tracks[2]) # c.mp3

        self.assertTrue(queue.queue_next(tracks[0])) # a.mp3

        self.assertEqual(queue.current().filename, "c.mp3")
        self.assertEqual([t.filename for t in queue.get_tracks()], ["b.mp3", "c.mp3", "a.mp3", "d.mp3"])

    def test_upcoming_wraps_from_current_track(self):
        tracks = [Track(path="a.mp3"), Track(path="b.mp3"), Track(path="c.mp3")]
        queue = TrackQueue(tracks)
        queue.select(tracks[1]) # b.mp3

        self.assertEqual([(offset, t.filename) for offset, t in queue.upcoming(limit=3)], [(1, "c.mp3"), (2, "a.mp3")])


if __name__ == "__main__":
    unittest.main()
