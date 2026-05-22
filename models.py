from dataclasses import dataclass

@dataclass(frozen=True)
class Track:
    path: str
    filename: str
    artist: str
    title: str
    duration: int = 0  # In seconds

    def to_dict(self):
        return {
            "path": self.path,
            "filename": self.filename,
            "artist": self.artist,
            "title": self.title,
            "duration": self.duration
        }

    def __str__(self):
        return self.filename


@dataclass(frozen=True)
class QueueEntry:
    offset: int
    track: Track


@dataclass(frozen=True)
class PlaybackSnapshot:
    current: Track | None
    index: int
    paused: bool
    volume: float
    track_count: int
    elapsed_seconds: int
    upcoming: list[QueueEntry]

    @property
    def artist(self):
        return self.current.artist if self.current else "Unknown Artist"

    @property
    def title(self):
        return self.current.title if self.current else "No track"

    @property
    def filename(self):
        return self.current.filename if self.current else ""

    @property
    def path(self):
        return self.current.path if self.current else ""

    @property
    def duration(self):
        return self.current.duration if self.current else 0

    def to_current_track_dict(self):
        return {
            "artist": self.artist,
            "title": self.title,
            "filename": self.filename,
            "path": self.path,
            "duration": self.duration,
            "index": self.index,
            "paused": self.paused,
            "volume": self.volume,
            "track_count": self.track_count,
        }
