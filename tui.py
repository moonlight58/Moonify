import os
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

def main_menu(stdscr):
    import curses
    import time

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
    stdscr.refresh()
    stdscr.getch()

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

    player = Player(selected_playlist, loop, shuffle, earphone_device)
    player.play_with_tui(stdscr)