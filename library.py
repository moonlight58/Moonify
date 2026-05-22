import os
import random
from dataclasses import dataclass

from models import Track
from utils import parse_filename


SUPPORTED_EXTENSIONS = (".mp3",)


@dataclass(frozen=True)
class Playlist:
    name: str
    path: str


@dataclass(frozen=True)
class LoadedPlaylist:
    playlist: Playlist
    tracks: list[Track]

    @property
    def is_playable(self):
        return bool(self.tracks)


class Library:
    def __init__(self, supported_extensions=SUPPORTED_EXTENSIONS):
        self.supported_extensions = tuple(ext.lower() for ext in supported_extensions)

    def list_playlists(self, music_folder):
        if not os.path.isdir(music_folder):
            return []
        return [
            Playlist(name, os.path.join(music_folder, name))
            for name in sorted(os.listdir(music_folder))
            if os.path.isdir(os.path.join(music_folder, name))
        ]

    def load_playlist(self, folder, shuffle=False):
        playlist = Playlist(os.path.basename(folder), folder)
        return LoadedPlaylist(playlist=playlist, tracks=self.load_tracks(folder, shuffle=shuffle))

    def load_tracks(self, folder, shuffle=False):
        if not os.path.isdir(folder):
            return []
        tracks = [
            self.track_from_file(os.path.join(folder, name))
            for name in os.listdir(folder)
            if self.is_supported_track_file(os.path.join(folder, name))
        ]
        tracks.sort(key=lambda t: t.filename)
        if shuffle:
            random.shuffle(tracks)
        return tracks

    def playlist_has_tracks(self, folder):
        if not os.path.isdir(folder):
            return False
        return any(
            self.is_supported_track_file(os.path.join(folder, name))
            for name in os.listdir(folder)
        )

    def is_supported_track_file(self, path):
        return os.path.isfile(path) and path.lower().endswith(self.supported_extensions)

    def track_from_file(self, path):
        filename = os.path.basename(path)
        artist, title = parse_filename(filename)
        return Track(
            path=path,
            filename=filename,
            artist=artist,
            title=title,
            duration=self.read_track_duration(path),
        )

    def read_track_duration(self, path):
        try:
            from mutagen.mp3 import MP3

            audio = MP3(path)
            return int(audio.info.length)
        except Exception:
            return 0


default_library = Library()


def list_playlists(music_folder):
    return default_library.list_playlists(music_folder)


def track_from_file(path):
    return default_library.track_from_file(path)


def read_track_duration(path):
    return default_library.read_track_duration(path)


def list_track_files(folder, shuffle=False):
    return default_library.load_tracks(folder, shuffle=shuffle)


def playlist_has_tracks(folder):
    return default_library.playlist_has_tracks(folder)
