import os
from dataclasses import dataclass, field
from typing import Optional
from utils import parse_filename

@dataclass(frozen=True)
class Track:
    path: str
    filename: str = field(init=False)
    artist: str = field(init=False)
    title: str = field(init=False)
    duration: int = field(default=0)  # In seconds

    def __post_init__(self):
        filename = os.path.basename(self.path)
        object.__setattr__(self, 'filename', filename)
        artist, title = parse_filename(filename)
        object.__setattr__(self, 'artist', artist)
        object.__setattr__(self, 'title', title)
        
        if self.duration == 0:
            try:
                from mutagen.mp3 import MP3
                audio = MP3(self.path)
                object.__setattr__(self, 'duration', int(audio.info.length))
            except Exception:
                pass

    @classmethod
    def from_path(cls, path: str):
        # We can optimize duration extraction later or pass it here
        return cls(path=path)

    def with_duration(self, duration: int):
        return Track(path=self.path, duration=duration)

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
