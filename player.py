import os
from library import list_track_files
from playback_queue import TrackQueue
from presence import build_presence
from engine import PlaybackEngine, PygameEngine
from events import EventBus
from models import Track
from media_controller import MediaController, LinuxMediaController, NullMediaController

class Player:
    def __init__(self, folder, loop=False, shuffle=False, earphone_device=None, enable_rpc=False, engine: PlaybackEngine = None, events: EventBus = None, media_controller: MediaController = None):
        self.folder = folder
        self.loop = loop
        self.shuffle = shuffle
        self.events = events or EventBus()
        self.engine = engine or PygameEngine()
        
        if media_controller:
            self.media_controller = media_controller
        elif earphone_device:
            self.media_controller = LinuxMediaController(earphone_device)
        else:
            self.media_controller = NullMediaController()

        self.queue = TrackQueue(list_track_files(folder, shuffle=shuffle))
        self.paused = False
        self.presence = build_presence(enable_rpc)
        
        # Subscribe presence to events
        self.events.subscribe("track_started", self.presence.track_started)

    def play(self):
        track = self.queue.current()
        if not track:
            return False
        
        self.engine.load(track.path)
        self.engine.play()
        self.paused = False

        self.events.emit("track_started", track.to_dict())
        return True

    def pause(self):
        self.engine.pause()
        self.paused = True
        self.events.emit("playback_toggled", {"paused": True})

    def resume(self):
        self.engine.resume()
        self.paused = False
        self.events.emit("playback_toggled", {"paused": False})

    def toggle_pause(self):
        if self.paused:
            self.resume()
        else:
            self.pause()

    def next_track(self):
        if not self.queue:
            return False
        self.engine.stop()
        if not self.queue.move_next(loop=self.loop):
            self.paused = True
            self.events.emit("playback_toggled", {"paused": True})
            return False
        return self.play()

    def previous_track(self):
        if not self.queue:
            return False
        self.engine.stop()
        self.queue.move_previous()
        return self.play()

    def set_volume(self, volume):
        self.engine.set_volume(volume)
        self.events.emit("volume_changed", {"volume": self.engine.get_volume()})

    def adjust_volume(self, delta):
        self.set_volume(self.engine.get_volume() + delta)

    def change_playlist(self, folder):
        tracks = list_track_files(folder, shuffle=self.shuffle)
        if not tracks:
            return False
        self.engine.stop()
        self.folder = folder
        self.queue.replace(tracks)
        return self.play()

    def playlist_base_folder(self):
        return os.path.dirname(self.folder)

    def get_tracks(self):
        return self.queue.get_tracks()

    def track_count(self):
        return len(self.queue)

    def play_song(self, track: Track):
        if not self.queue.select(track):
            return False
        self.engine.stop()
        return self.play()

    def queue_next(self, track: Track):
        return self.queue.queue_next(track)

    def upcoming_tracks(self, limit=10):
        return self.queue.upcoming(limit)

    def advance_if_finished(self):
        if self.paused or self.is_playing():
            return False
        return self.next_track()

    def pop_media_actions(self):
        return self.media_controller.pop_actions()

    def get_current_track_info(self):
        track = self.queue.current()
        if not track:
            return {
                "artist": "Unknown Artist",
                "title": "No track",
                "filename": "",
                "path": "",
                "duration": 0,
                "index": 0,
                "paused": self.paused,
                "volume": self.engine.get_volume(),
                "track_count": 0,
            }
        
        info = track.to_dict()
        info.update({
            "index": self.index(),
            "paused": self.paused,
            "volume": self.engine.get_volume(),
            "track_count": len(self.queue),
        })
        return info

    def is_playing(self):
        return self.engine.is_busy() and not self.paused

    def stop(self):
        self.engine.stop()
        self.presence.close()
        
    def get_elapsed_ms(self):
        return self.engine.get_pos_ms()

    def index(self):
        return self.queue.index
