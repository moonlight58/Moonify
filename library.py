import os
import random
from dataclasses import dataclass


SUPPORTED_EXTENSIONS = (".mp3",)


@dataclass(frozen=True)
class Playlist:
    name: str
    path: str


def list_playlists(music_folder):
    if not os.path.isdir(music_folder):
        return []
    return [
        Playlist(name, os.path.join(music_folder, name))
        for name in sorted(os.listdir(music_folder))
        if os.path.isdir(os.path.join(music_folder, name))
    ]


from models import Track

def list_track_files(folder, shuffle=False):
    if not os.path.isdir(folder):
        return []
    tracks = [
        Track.from_path(os.path.join(folder, name))
        for name in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, name)) and name.lower().endswith(SUPPORTED_EXTENSIONS)
    ]
    tracks.sort(key=lambda t: t.filename)
    if shuffle:
        random.shuffle(tracks)
    return tracks


def playlist_has_tracks(folder):
    return bool(list_track_files(folder))
