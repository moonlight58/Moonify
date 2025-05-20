import os
import pygame
import random
import curses
from player import Player
from earphone import find_earphone_device

def select_playlist_with_curses(stdscr, base_folder):
    playlists = [d for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))]
    if not playlists:
        stdscr.addstr(0, 0, "No playlists found.")
        stdscr.refresh()
        stdscr.getch()
        return None
    current_selection = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Available playlists:")
        for i, playlist in enumerate(playlists):
            if i == current_selection:
                stdscr.addstr(i + 1, 0, f"> {playlist}", curses.A_REVERSE)
            else:
                stdscr.addstr(i + 1, 0, f"  {playlist}")
        stdscr.addstr(len(playlists) + 2, 0, "Use UP/DOWN arrows, ENTER to select, Q to cancel.")
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_selection = (current_selection - 1) % len(playlists)
        elif key == curses.KEY_DOWN:
            current_selection = (current_selection + 1) % len(playlists)
        elif key == ord('\n'):
            return os.path.join(base_folder, playlists[current_selection])
        elif key == ord('q'):
            return None

def play_with_tui(stdscr, player):
    jump_to_song = False
    # Set up the end-of-song event
    END_EVENT = pygame.USEREVENT + 1
    pygame.mixer.music.set_endevent(END_EVENT)

    while True:
        player.play()
        info = player.get_current_track_info()
        total_length = info["duration"]
        track_title = info["title"]
        track_artist = info["artist"]

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, f"Now playing: {track_title} - {track_artist}")
            stdscr.addstr(2, 0, "Controls: [P]ause/[R]esume, [N]ext, [B]ack, [Q]uit, [+/-] Volume, [C]hange playlist, [S]earch")
            if player.earphone_device:
                stdscr.addstr(3, 0, "Earphone controls: Play/Pause, Next, Previous, Volume Up/Down")
            stdscr.addstr(4, 0, f"Volume: {int(player.get_current_track_info()['volume'] * 100)}%")
            stdscr.addstr(5, 0, f"Status: {'Paused' if player.paused else 'Playing'}")

            # Progress bar
            elapsed_ms = pygame.mixer.music.get_pos()
            elapsed_sec = max(elapsed_ms // 1000, 0)
            elapsed_min = elapsed_sec // 60
            elapsed_sec = elapsed_sec % 60
            total_min = total_length // 60
            total_sec = total_length % 60
            bar_length = 30
            progress_ratio = min(elapsed_ms / 1000 / total_length, 1.0) if total_length > 0 else 0
            blocks = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉"]
            full_block = "█"
            filled = int(progress_ratio * bar_length)
            partial_block_idx = int((progress_ratio * bar_length - filled) * (len(blocks) - 1))
            bar = full_block * filled
            if filled < bar_length:
                bar += blocks[partial_block_idx]
                bar += " " * (bar_length - filled - 1)
            else:
                bar += " " * (bar_length - filled)
            progress_line = f"[{bar}] {elapsed_min:02d}:{elapsed_sec:02d} / {total_min:02d}:{total_sec:02d}"
            stdscr.addstr(7, 0, progress_line)

            # Preview next 10 songs (fit to terminal height)
            height, width = stdscr.getmaxyx()
            max_preview = min(10, height - 11)  # leave space for UI
            stdscr.addstr(9, 0, "Prochaines chansons :")
            for i in range(1, max_preview + 1):
                next_index = (player.current_index + i) % len(player.music_files)
                prefix = f"{i}. "
                song_title = player.music_files[next_index]
                # Truncate song title to fit width
                display_str = (prefix + song_title)[:width - 4]
                stdscr.addstr(9 + i, 2, display_str)

            stdscr.refresh()
            key = -1
            if player.earphone_events:
                _, mapped_key = player.earphone_events.pop(0)
                key = mapped_key
            else:
                curses.halfdelay(1)
                try:
                    key = stdscr.getch()
                except curses.error:
                    key = -1
                    
            if not player.paused and not player.is_playing():
                player.next_track()
                jump_to_song = False
                break

            if key == ord('p'):
                if not player.paused:
                    player.pause()
            elif key == ord('r'):
                if player.paused:
                    player.resume()
            elif key == ord('n'):
                player.next_track()
                jump_to_song = False
                break
            elif key == ord('b'):
                player.previous_track()
                jump_to_song = False
                break
            elif key == ord('q'):
                player.stop()
                return
            elif key == ord('+'):
                current_volume = pygame.mixer.music.get_volume()
                player.set_volume(min(current_volume + 0.1, 1.0))
            elif key == ord('-'):
                current_volume = pygame.mixer.music.get_volume()
                player.set_volume(max(current_volume - 0.1, 0.0))
            elif key == ord('c'):
                player.stop()
                from tui import select_playlist_with_curses
                stdscr.addstr(9, 0, "Changing playlist...")
                stdscr.refresh()
                new_playlist = select_playlist_with_curses(stdscr, os.path.dirname(player.folder))
                if new_playlist:
                    player.folder = new_playlist
                    player.music_files = [f for f in os.listdir(player.folder) if f.endswith('.mp3')]
                    if not player.music_files:
                        stdscr.addstr(10, 0, "No .mp3 files found in the selected playlist.")
                        stdscr.refresh()
                        stdscr.getch()
                        return
                    if player.shuffle:
                        random.shuffle(player.music_files)
                    player.current_index = 0
                    jump_to_song = False
                    break
                else:
                    stdscr.addstr(8, 0, "No playlist selected. Continuing current playlist.")
                    stdscr.refresh()
            elif key == ord('s'):
                stdscr.addstr(21, 0, "Enter search term: ")
                stdscr.refresh()
                curses.echo()
                search_term = stdscr.getstr(22, 0, 30).decode('utf-8').lower()
                curses.noecho()
                filtered_songs = [song for song in player.music_files if search_term in song.lower()]
                if not filtered_songs or search_term == "":
                    stdscr.addstr(23, 0, "No songs found matching the search term.")
                    stdscr.refresh()
                    stdscr.getch()
                    continue
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
                            player.stop()
                            player.current_index = player.music_files.index(selected_song)
                            jump_to_song = True
                            break
                        elif action_key in (ord('q'), ord('Q')):
                            player.music_files.insert(player.current_index + 1, player.music_files.pop(player.music_files.index(selected_song)))
                            stdscr.addstr(2, 0, f"{selected_song} queued next.")
                            stdscr.refresh()
                            stdscr.getch()
                            break
                    elif key == ord('q'):
                        break
                if jump_to_song:
                    break

        # Only increment current_index if not jumping to a song (search)
        if jump_to_song:
            jump_to_song = False
            continue

def main_menu(stdscr):
    music_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'music')
    if not os.path.exists(music_folder):
        stdscr.addstr(0, 0, "Music folder does not exist.")
        stdscr.refresh()
        stdscr.getch()
        return

    earphone_device, device_name = find_earphone_device()
    stdscr.clear()
    if earphone_device:
        stdscr.addstr(0, 0, f"Earphone device detected: {device_name}")
        stdscr.addstr(1, 0, f"Device path: {earphone_device}")
    else:
        stdscr.addstr(0, 0, "No earphone device detected automatically.")
        stdscr.addstr(1, 0, "You can still use the player with keyboard controls.")
        stdscr.addstr(2, 0, "Press any key to continue...")
    stdscr.refresh()
    stdscr.getch()

    stdscr.clear()
    stdscr.addstr(0, 0, "Enable Discord Rich Presence? (y/N): ")
    stdscr.refresh()
    enable_rpc = stdscr.getch() in (ord('y'), ord('Y'))

    selected_playlist = select_playlist_with_curses(stdscr, music_folder)
    if not selected_playlist:
        return

    stdscr.clear()
    stdscr.addstr(0, 0, "Enable looping? (y/N): ")
    stdscr.refresh()
    loop = stdscr.getch() in (ord('y'), ord('Y'))

    stdscr.clear()
    stdscr.addstr(0, 0, "Enable shuffle? (y/N): ")
    stdscr.refresh()
    shuffle = stdscr.getch() in (ord('y'), ord('Y'))

    player = Player(selected_playlist, loop, shuffle, earphone_device, enable_rpc=enable_rpc)
    play_with_tui(stdscr, player)