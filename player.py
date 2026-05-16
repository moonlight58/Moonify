import os
import random
import pygame
import threading
from threading import Thread
from cover import extract_cover, upload_to_imgur
from utils import parse_filename
from discord_rpc import DiscordRPC
from earphone import listen_for_earphone_events

class Player:
    def __init__(self, folder, loop=False, shuffle=False, earphone_device=None, enable_rpc=False):
        self.folder = folder
        self.loop = loop
        self.shuffle = shuffle
        self.earphone_device = earphone_device
        self.music_files = self._load_music_files(folder)
        self.current_index = 0
        self.paused = False
        self.earphone_events = []
        self.event_thread = None
        
        """ Discord Rich Presence - MultiThreading """
        self.discord_rpc = DiscordRPC(enable_rpc)
        self.rpc_thread = None
        self.rpc_stop_event = threading.Event()
        self.rpc_info = None        
        
        """ Earphone detection not working >:( """
        if self.earphone_device and os.path.exists(self.earphone_device):
            self.event_thread = Thread(
                target=listen_for_earphone_events,
                args=(self.earphone_device, self.earphone_events),
                daemon=True
            )
            self.event_thread.start()        
        pygame.mixer.init()

    def _load_music_files(self, folder):
        music_files = [f for f in os.listdir(folder) if f.endswith(".mp3")]
        music_files.sort()
        if self.shuffle:
            random.shuffle(music_files)
        return music_files

    def _discord_rpc_worker(self):
        """Thread to handle Discord RPC updates with debounce."""
        last_info = None
        while not self.rpc_stop_event.is_set():
            if self.rpc_info and self.rpc_info != last_info:
                # Debounce: wait for 2 seconds before updating
                info_snapshot = self.rpc_info.copy()
                waited = 0
                while waited < 2:
                    self.rpc_stop_event.wait(0.1)
                    waited += 0.1
                    # if new info arrives, break
                    if self.rpc_info != info_snapshot:
                        break
                else:
                    # if no new info, proceed with the last snapshot
                    try:
                        music_path = info_snapshot["music_path"]
                        cover_path = "/tmp/current_cover.jpg"
                        extract_cover(music_path, cover_path)
                        cover_url = upload_to_imgur(cover_path)
                        self.discord_rpc.show_track(
                            title=info_snapshot["title"],
                            artist=info_snapshot["artist"],
                            cover_url=cover_url
                        )
                    except Exception as e:
                        print(f"[DiscordRPC] Failed to update: {e}")
                    self.rpc_info = None
                    last_info = info_snapshot
            else:
                self.rpc_stop_event.wait(0.1)

    def play(self):
        if not self.music_files:
            return False
        music_file = self.music_files[self.current_index]
        music_path = os.path.join(self.folder, music_file)
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play()
        self.paused = False

        track_artist, track_title = parse_filename(music_file)

        # Only set rpc_info, let the thread handle cover extraction/upload
        if self.discord_rpc.is_discord_running() and self.discord_rpc.user_choice == 1:
            self.rpc_info = {
                "title": track_title,
                "artist": track_artist,
                "music_path": music_path
            }
            if not self.rpc_thread or not self.rpc_thread.is_alive():
                self.rpc_stop_event.clear()
                self.rpc_thread = Thread(target=self._discord_rpc_worker, daemon=True)
                self.rpc_thread.start()
        return True

    def pause(self):
        pygame.mixer.music.pause()
        self.paused = True

    def resume(self):
        pygame.mixer.music.unpause()
        self.paused = False

    def toggle_pause(self):
        if self.paused:
            self.resume()
        else:
            self.pause()

    def next_track(self):
        if not self.music_files:
            return False
        pygame.mixer.music.stop()
        next_index = self.current_index + 1
        if next_index >= len(self.music_files):
            if self.loop:
                next_index = 0
            else:
                self.current_index = len(self.music_files) - 1
                self.paused = True
                return False
        self.current_index = next_index
        return self.play()

    def previous_track(self):
        if not self.music_files:
            return False
        pygame.mixer.music.stop()
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.music_files) - 1
        return self.play()

    def set_volume(self, volume):
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    def adjust_volume(self, delta):
        self.set_volume(pygame.mixer.music.get_volume() + delta)

    def change_playlist(self, folder):
        music_files = self._load_music_files(folder)
        if not music_files:
            return False
        pygame.mixer.music.stop()
        self.folder = folder
        self.music_files = music_files
        self.current_index = 0
        return self.play()

    def playlist_base_folder(self):
        return os.path.dirname(self.folder)

    def track_names(self):
        return self.music_files[:]

    def track_count(self):
        return len(self.music_files)

    def play_song(self, song):
        if song not in self.music_files:
            return False
        pygame.mixer.music.stop()
        self.current_index = self.music_files.index(song)
        return self.play()

    def queue_next(self, song):
        if song not in self.music_files:
            return False
        current_position = self.music_files.index(song)
        if current_position == self.current_index:
            return True
        song_name = self.music_files.pop(current_position)
        if current_position < self.current_index:
            self.current_index -= 1
        insert_at = min(self.current_index + 1, len(self.music_files))
        self.music_files.insert(insert_at, song_name)
        return True

    def upcoming_tracks(self, limit=10):
        if not self.music_files:
            return []
        upcoming = []
        for offset in range(1, min(limit + 1, len(self.music_files))):
            index = (self.current_index + offset) % len(self.music_files)
            upcoming.append((offset, self.music_files[index]))
        return upcoming

    def advance_if_finished(self):
        if self.paused or self.is_playing():
            return False
        return self.next_track()

    def pop_earphone_actions(self):
        actions = []
        mapping = {
            ord("p"): "pause",
            ord("r"): "resume",
            ord("n"): "next",
            ord("b"): "previous",
            ord("+"): "volume_up",
            ord("-"): "volume_down",
        }
        while self.earphone_events:
            _, mapped_key = self.earphone_events.pop(0)
            action = mapping.get(mapped_key)
            if action:
                actions.append(action)
        return actions

    def get_current_track_info(self):
        if not self.music_files:
            return {
                "artist": "Unknown Artist",
                "title": "No track",
                "filename": "",
                "path": "",
                "duration": 0,
                "index": 0,
                "paused": self.paused,
                "volume": pygame.mixer.music.get_volume(),
                "track_count": 0,
            }
        music_file = self.music_files[self.current_index]
        music_path = os.path.join(self.folder, music_file)
        track_artist, track_title = parse_filename(music_file)
        try:
            from mutagen.mp3 import MP3
            audio = MP3(music_path)
            total_length = int(audio.info.length)
        except Exception:
            total_length = 0
        return {
            "artist": track_artist,
            "title": track_title,
            "filename": music_file,
            "path": music_path,
            "duration": total_length,
            "index": self.current_index,
            "paused": self.paused,
            "volume": pygame.mixer.music.get_volume(),
            "track_count": len(self.music_files),
        }

    def is_playing(self):
        return pygame.mixer.music.get_busy() and not self.paused

    def stop(self):
        pygame.mixer.music.stop()
        self.discord_rpc.clear()
        if self.rpc_thread and self.rpc_thread.is_alive():
            self.rpc_stop_event.set()
            self.rpc_thread.join(timeout=2)
        
    def get_elapsed_ms(self):
        return pygame.mixer.music.get_pos()
