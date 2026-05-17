from models import Track

class TrackQueue:
    def __init__(self, tracks: list[Track]):
        self.tracks = list(tracks)
        self.index = 0

    def __len__(self):
        return len(self.tracks)

    def current(self) -> Track | None:
        if not self.tracks:
            return None
        return self.tracks[self.index]

    def get_tracks(self):
        return self.tracks[:]

    def move_next(self, loop=False):
        if not self.tracks:
            return False
        next_index = self.index + 1
        if next_index >= len(self.tracks):
            if not loop:
                self.index = len(self.tracks) - 1
                return False
            next_index = 0
        self.index = next_index
        return True

    def move_previous(self):
        if not self.tracks:
            return False
        self.index -= 1
        if self.index < 0:
            self.index = len(self.tracks) - 1
        return True

    def select(self, track: Track):
        if track not in self.tracks:
            return False
        self.index = self.tracks.index(track)
        return True

    def queue_next(self, track: Track):
        if track not in self.tracks:
            return False
        current_position = self.tracks.index(track)
        if current_position == self.index:
            return True
        track_obj = self.tracks.pop(current_position)
        if current_position < self.index:
            self.index -= 1
        insert_at = min(self.index + 1, len(self.tracks))
        self.tracks.insert(insert_at, track_obj)
        return True

    def replace(self, tracks: list[Track]):
        self.tracks = list(tracks)
        self.index = 0

    def upcoming(self, limit=10):
        if not self.tracks:
            return []
        upcoming = []
        for offset in range(1, min(limit + 1, len(self.tracks))):
            index = (self.index + offset) % len(self.tracks)
            upcoming.append((offset, self.tracks[index]))
        return upcoming
