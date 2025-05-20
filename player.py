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
        self.music_files = [f for f in os.listdir(folder) if f.endswith('.mp3')]
        if self.shuffle:
            random.shuffle(self.music_files)
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


    def _discord_rpc_worker(self):
        """Thread to handle Discord RPC updates."""
        while not self.rpc_stop_event.is_set():
            if self.rpc_info:
                try:
                    # Extract cover and upload to imgur in the thread
                    music_path = self.rpc_info["music_path"]
                    cover_path = "/tmp/current_cover.jpg"
                    extract_cover(music_path, cover_path)
                    cover_url = upload_to_imgur(cover_path)
                    self.discord_rpc.show_track(
                        title=self.rpc_info["title"],
                        artist=self.rpc_info["artist"],
                        cover_url=cover_url
                    )
                except Exception as e:
                    print(f"[DiscordRPC] Failed to update: {e}")
                self.rpc_info = None
            # Sleep a bit to avoid busy waiting
            self.rpc_stop_event.wait(1)

    def play(self):
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

    def pause(self):
        pygame.mixer.music.pause()
        self.paused = True

    def resume(self):
        pygame.mixer.music.unpause()
        self.paused = False

    def next_track(self):
        pygame.mixer.music.stop()
        self.current_index += 1
        if self.current_index >= len(self.music_files):
            if self.loop:
                self.current_index = 0
            else:
                self.current_index = len(self.music_files) - 1
        self.play()

    def previous_track(self):
        pygame.mixer.music.stop()
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.music_files) - 1
        self.play()

    def set_volume(self, volume):
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    def get_current_track_info(self):
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