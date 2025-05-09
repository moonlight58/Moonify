import os
import random
import pygame
from threading import Thread
from cover import extract_cover, upload_to_imgur
from utils import parse_filename
from discord_rpc import DiscordRPC
from earphone import listen_for_earphone_events

class Player:
    def __init__(self, folder, loop=False, shuffle=False, earphone_device=None):
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
        self.discord_rpc = DiscordRPC()
        if self.earphone_device and os.path.exists(self.earphone_device):
            self.event_thread = Thread(
                target=listen_for_earphone_events,
                args=(self.earphone_device, self.earphone_events),
                daemon=True
            )
            self.event_thread.start()
        pygame.mixer.init()

    def play_with_tui(self, stdscr):
        import curses
        jump_to_song = False
        while True:
            music_file = self.music_files[self.current_index]
            music_path = os.path.join(self.folder, music_file)
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play()
            
            track_artist, track_title = parse_filename(music_file)

            if self.discord_rpc.is_discord_running():   
                cover_path = "/tmp/current_cover.jpg"
                cover_url = None
                
                if extract_cover(music_path, cover_path):
                    cover_url = upload_to_imgur(cover_path)
                
                self.discord_rpc.show_track(
                    title=track_title,
                    artist=track_artist,
                    cover_url=cover_url
                )
            
            try:
                from mutagen.mp3 import MP3
                audio = MP3(music_path)
                total_length = int(audio.info.length)
            except:
                total_length = 0
            while True:
                stdscr.clear()
                stdscr.addstr(0, 0, f"Now playing: {track_title} - {track_artist}")
                stdscr.addstr(2, 0, "Controls: [P]ause/[R]esume, [N]ext, [B]ack, [Q]uit, [+/-] Volume, [C]hange playlist, [S]earch")
                if self.earphone_device:
                    stdscr.addstr(3, 0, "Earphone controls: Play/Pause, Next, Previous, Volume Up/Down")
                stdscr.addstr(4, 0, f"Volume: {int(pygame.mixer.music.get_volume() * 100)}%")
                stdscr.addstr(5, 0, f"Status: {'Paused' if self.paused else 'Playing'}")
                elapsed_ms = pygame.mixer.music.get_pos()
                elapsed_sec = max(elapsed_ms // 1000, 0)
                elapsed_min = elapsed_sec // 60
                elapsed_sec = elapsed_sec % 60
                total_min = total_length // 60
                total_sec = total_length % 60
                bar_length = 30
                progress_ratio = min(elapsed_ms / 1000 / total_length, 1.0) if total_length > 0 else 0
                filled_length = int(bar_length * progress_ratio)
                bar = '#' * filled_length + '-' * (bar_length - filled_length)
                progress_line = f"[{bar}] {elapsed_min:02d}:{elapsed_sec:02d} / {total_min:02d}:{total_sec:02d}"
                stdscr.addstr(7, 0, progress_line)
                stdscr.addstr(9, 0, "Prochaines chansons :")
                for i in range(1, 11):
                    next_index = (self.current_index + i) % len(self.music_files)
                    prefix = f"{i}. "
                    song_title = self.music_files[next_index]
                    stdscr.addstr(9 + i, 2, f"{prefix}{song_title}")
                stdscr.refresh()
                key = -1
                if self.earphone_events:
                    _, mapped_key = self.earphone_events.pop(0)
                    key = mapped_key
                else:
                    curses.halfdelay(1)
                    try:
                        key = stdscr.getch()
                    except curses.error:
                        key = -1
                if key == ord('p'):
                    if not self.paused:
                        pygame.mixer.music.pause()
                        self.paused = True
                elif key == ord('r'):
                    if self.paused:
                        pygame.mixer.music.unpause()
                        self.paused = False
                elif key == ord('n'):
                    pygame.mixer.music.stop()
                    self.current_index += 1
                    if self.current_index >= len(self.music_files):
                        if self.loop:
                            self.current_index = 0
                        else:
                            stdscr.addstr(8, 0, "End of playlist.")
                            stdscr.refresh()
                            stdscr.getch()
                            return
                    break
                elif key == ord('b'):
                    pygame.mixer.music.stop()
                    self.current_index -= 1
                    if self.current_index < 0:
                        self.current_index = len(self.music_files) - 1
                    break
                elif key == ord('q'):
                    pygame.mixer.music.stop()
                    self.discord_rpc.clear()
                    return
                elif key == ord('+'):
                    current_volume = pygame.mixer.music.get_volume()
                    pygame.mixer.music.set_volume(min(current_volume + 0.1, 1.0))
                elif key == ord('-'):
                    current_volume = pygame.mixer.music.get_volume()
                    pygame.mixer.music.set_volume(max(current_volume - 0.1, 0.0))
                elif key == ord('c'):
                    pygame.mixer.music.stop()
                    from tui import select_playlist_with_curses
                    stdscr.addstr(9, 0, "Changing playlist...")
                    stdscr.refresh()
                    new_playlist = select_playlist_with_curses(stdscr, os.path.dirname(self.folder))
                    if new_playlist:
                        self.folder = new_playlist
                        self.music_files = [f for f in os.listdir(self.folder) if f.endswith('.mp3')]
                        if not self.music_files:
                            stdscr.addstr(10, 0, "No .mp3 files found in the selected playlist.")
                            stdscr.refresh()
                            stdscr.getch()
                            return
                        if self.shuffle:
                            random.shuffle(self.music_files)
                        self.current_index = 0
                        break
                    else:
                        stdscr.addstr(8, 0, "No playlist selected. Continuing current playlist.")
                        stdscr.refresh()
                elif key == ord('s'):
                    stdscr.addstr(21, 0, "Enter search term: ")
                    stdscr.refresh()
                    import curses
                    curses.echo()
                    search_term = stdscr.getstr(22, 0, 30).decode('utf-8').lower()
                    curses.noecho()
                    filtered_songs = [song for song in self.music_files if search_term in song.lower()]
                    if not filtered_songs or search_term == "":
                        stdscr.addstr(23, 0, "No songs found matching the search term.")
                        stdscr.refresh()
                        stdscr.getch()
                        continue
                    jump_to_song = False
                    selected_index = 0
                    while True:
                        stdscr.clear()
                        stdscr.addstr(0, 0, "Search results:")
                        height, width = stdscr.getmaxyx()
                        max_display = height - 5
                        start = max(0, selected_index - max_display // 2)
                        end = min(len(filtered_songs), start + max_display)
                        for i in range(start, end):
                            display_name = filtered_songs[i][:width-4]
                            if i == selected_index:
                                stdscr.addstr(i - start + 1, 0, f"> {display_name}", curses.A_REVERSE)
                            else:
                                stdscr.addstr(i - start + 1, 0, f"  {display_name}")
                        stdscr.addstr(max_display + 2, 0, "Use UP/DOWN arrows to navigate, ENTER to select, Q to cancel.")
                        stdscr.refresh()
                        key = stdscr.getch()
                        if key == curses.KEY_UP:
                            selected_index = (selected_index - 1) % len(filtered_songs)
                        elif key == curses.KEY_DOWN:
                            selected_index = (selected_index + 1) % len(filtered_songs)
                        elif key == ord('\n'):
                            selected_song = filtered_songs[selected_index]
                            stdscr.clear()
                            stdscr.addstr(0, 0, f"Selected: {selected_song[:width-10]}")
                            stdscr.addstr(1, 0, "Play now (P) or Queue next (Q)?")
                            stdscr.refresh()
                            action_key = stdscr.getch()
                            if action_key in (ord('p'), ord('P')):
                                pygame.mixer.music.stop()
                                self.current_index = self.music_files.index(selected_song)
                                jump_to_song = True
                                break
                            elif action_key in (ord('q'), ord('Q')):
                                self.music_files.insert(self.current_index + 1, self.music_files.pop(self.music_files.index(selected_song)))
                                stdscr.addstr(2, 0, f"{selected_song} queued next.")
                                stdscr.refresh()
                                stdscr.getch()
                                break
                        elif key == ord('q'):
                            break
                if not pygame.mixer.music.get_busy() and not self.paused:
                    if not jump_to_song:
                        self.current_index += 1
                    if self.current_index >= len(self.music_files):
                        if self.loop:
                            self.current_index = 0
                        else:
                            stdscr.addstr(7, 0, "End of playlist.")
                            stdscr.refresh()
                            stdscr.getch()
                            return
                    break