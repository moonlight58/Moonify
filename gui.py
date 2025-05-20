import sys
import os
import random
from threading import Thread
import pygame
from cover import extract_cover, upload_to_imgur
from utils import parse_filename
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QSlider, QListWidget, QFileDialog, QHBoxLayout, QProgressBar, QComboBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QIcon
from player import Player

class MusicPlayerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Moonify - Music Player GUI")
        self.setGeometry(100, 100, 600, 500)
        self.player = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.waiting_for_next = False  # Add this line
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Album art
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(200, 200)
        self.cover_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.cover_label, alignment=Qt.AlignCenter)

        # Track info
        self.label = QLabel("No track loaded")
        main_layout.addWidget(self.label)

        # Playlist view
        self.playlist_widget = QListWidget()
        self.playlist_widget.itemDoubleClicked.connect(self.select_song)
        main_layout.addWidget(self.playlist_widget)

        # Progress bar and timer
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.time_label = QLabel("00:00 / 00:00")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.time_label)
        main_layout.addLayout(progress_layout)

        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)
        controls_layout.setAlignment(Qt.AlignCenter)

        self.shuffle_btn = QPushButton("⤨")
        self.shuffle_btn.setCheckable(True)
        self.shuffle_btn.setToolTip("Shuffle")
        self.shuffle_btn.setFixedSize(40, 40)
        controls_layout.addWidget(self.shuffle_btn)

        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setFixedSize(50, 50)
        controls_layout.addWidget(self.prev_btn)

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(60, 60)
        self.play_btn.setStyleSheet("QPushButton { font-size: 28pt; border-radius: 30px; background-color: #1DB954; color: #191414; } QPushButton:hover { background-color: #1ed760; }")
        controls_layout.addWidget(self.play_btn)

        self.next_btn = QPushButton("⏭")
        self.next_btn.setFixedSize(50, 50)
        controls_layout.addWidget(self.next_btn)

        main_layout.addLayout(controls_layout)

        # Connect buttons to their respective functions
        self.shuffle_btn.clicked.connect(self.toggle_shuffle)
        self.prev_btn.clicked.connect(self.prev_track)
        self.play_btn.clicked.connect(self.toggle_play_pause)
        self.next_btn.clicked.connect(self.next_track)

        # Volume
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        main_layout.addWidget(QLabel("Volume"))
        main_layout.addWidget(self.volume_slider)

        # Playlist dropdown
        self.playlist_dropdown = QComboBox()
        self.playlist_dropdown.currentIndexChanged.connect(self.change_playlist)
        main_layout.addWidget(QLabel("Playlists"))
        main_layout.addWidget(self.playlist_dropdown)
        self.populate_playlists()

        self.setLayout(main_layout)

    def populate_playlists(self):
        self.playlist_dropdown.clear()
        music_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music")
        if os.path.exists(music_dir):
            playlists = [d for d in os.listdir(music_dir) if os.path.isdir(os.path.join(music_dir, d))]
            self.playlist_dropdown.addItems(playlists)
            if playlists:
                self.change_playlist(0)

    def change_playlist(self, index):
        music_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music")
        playlist_name = self.playlist_dropdown.currentText()
        if playlist_name:
            folder = os.path.join(music_dir, playlist_name)
            self.player = Player(folder)
            self.label.setText(f"Playlist loaded: {playlist_name}")
            self.update_playlist()
            self.show_cover()
            self.timer.start(500)

    def update_playlist(self):
        self.playlist_widget.clear()
        if self.player:
            for song in self.player.music_files:
                self.playlist_widget.addItem(song)

    def select_song(self, item):
        if self.player:
            index = self.player.music_files.index(item.text())
            self.player.current_index = index
            self.play()

    def play(self):
        if self.player:
            music_file = self.player.music_files[self.player.current_index]
            music_path = os.path.join(self.player.folder, music_file)
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play()
            self.player.paused = False
            track_artist, track_title = parse_filename(music_file)
            cover_url = None

            cover_path = "/tmp/current_cover.jpg"
            extract_cover(music_path, cover_path)

            # Only set rpc_info, do NOT call show_track here!
            if self.player.discord_rpc.is_discord_running() and self.player.discord_rpc.user_choice == 1:
                cover_url = upload_to_imgur(cover_path)
                self.player.rpc_info = {
                    "title": track_title,
                    "artist": track_artist,
                    "cover_url": cover_url
                }
                if not self.player.rpc_thread or not self.player.rpc_thread.is_alive():
                    self.player.rpc_stop_event.clear()
                    self.player.rpc_thread = Thread(target=self.player._discord_rpc_worker, daemon=True)
                    self.player.rpc_thread.start()

            self.waiting_for_next = False
            info = self.player.get_current_track_info()
            self.label.setText(f"Playing: {info['title']} - {info['artist']}")
            self.playlist_widget.setCurrentRow(self.player.current_index)
            self.show_cover()
            self.timer.start(500)
            self.play_btn.setText("⏸")

    def pause(self):
        if self.player:
            self.player.pause()
            self.label.setText("Paused")
            self.play_btn.setText("▶")

    def toggle_play_pause(self):
        if not self.player:
            return
        if self.player.paused or not self.player.is_playing():
            self.player.resume()
            self.play_btn.setText("⏸")
            self.label.setText(f"Playing: {self.player.get_current_track_info()['title']} - {self.player.get_current_track_info()['artist']}")
        else:
            self.player.pause()
            self.play_btn.setText("▶")
            self.label.setText("Paused")

    def next_track(self):
        if self.player:
            self.player.next_track()
            self.play()

    def prev_track(self):
        if self.player:
            self.player.previous_track()
            self.play()

    def set_volume(self, value):
        if self.player:
            self.player.set_volume(value / 100)

    def update_progress(self):
        if not self.player:
            return
        info = self.player.get_current_track_info()
        duration = info["duration"]
        elapsed_ms = self.player.get_elapsed_ms() if hasattr(self.player, "get_elapsed_ms") else 0
        elapsed_sec = max(elapsed_ms // 1000, 0)
        total_sec = duration
        if total_sec > 0:
            progress = int((elapsed_sec / total_sec) * 100)
        else:
            progress = 0
        self.progress_bar.setValue(progress)
        elapsed_min = elapsed_sec // 60
        elapsed_sec = elapsed_sec % 60
        total_min = total_sec // 60
        total_sec = total_sec % 60
        self.time_label.setText(f"{elapsed_min:02d}:{elapsed_sec:02d} / {total_min:02d}:{total_sec:02d}")

        # --- Auto-skip to next track if finished ---
        if not self.player.paused and not self.player.is_playing() and not self.waiting_for_next:
            self.waiting_for_next = True
            self.next_track()

    def show_cover(self):
        # Try to show cover art if available
        if self.player:
            info = self.player.get_current_track_info()
            cover_path = "/tmp/current_cover.jpg"
            if os.path.exists(cover_path):
                pixmap = QPixmap(cover_path)
                self.cover_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            else:
                self.cover_label.clear()
    
    def toggle_shuffle(self):
        if not self.player:
            return
        self.player.shuffle = not self.player.shuffle
        if self.player.shuffle:
            self.shuffle_btn.setText("⤨·")
            random.shuffle(self.player.music_files)
        else:
            self.shuffle_btn.setText("⤨")
            self.player.music_files.sort()
        self.update_playlist()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Example dark theme QSS
    dark_qss = """
    QWidget {
        background-color: #232629;
        color: #f0f0f0;
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 12pt;
    }
    QProgressBar {
        background: #444;
        border: 1px solid #222;
        border-radius: 5px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #0078d7;
        width: 10px;
    }
    QPushButton {
        background-color: #333;
        border: 1px solid #555;
        border-radius: 5px;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: #444;
    }
    QSlider::groove:horizontal {
        border: 1px solid #222;
        height: 8px;
        background: #444;
        margin: 2px 0;
        border-radius: 4px;
    }
    QSlider::handle:horizontal {
        background: #0078d7;
        border: 1px solid #222;
        width: 18px;
        margin: -2px 0;
        border-radius: 9px;
    }
    QListWidget, QComboBox {
        background-color: #2a2d2e;
        color: #f0f0f0;
        border: 1px solid #444;
    }
    QComboBox QAbstractItemView {
        background-color: #232629;
        selection-background-color: #0078d7;
        color: #f0f0f0;
    }
    """
    
    spotify_qss = """
    QWidget {
        background-color: #191414;
        color: #FFFFFF;
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 12pt;
    }
    QLabel {
        color: #FFFFFF;
    }
    QProgressBar {
        background: #404040;
        border: none;
        border-radius: 5px;
        height: 8px;
        text-align: center;
        color: #b3b3b3;
    }
    QProgressBar::chunk {
        background-color: #1DB954;
        border-radius: 5px;
    }
    QPushButton {
        background-color: transparent;
        color: #b3b3b3;
        border: none;
        padding: 8px;
        font-size: 16pt;
    }
    QPushButton:checked, QPushButton:pressed {
        color: #1DB954;
    }
    QPushButton:hover {
        color: #1DB954;
    }
    QSlider::groove:horizontal {
        border: none;
        height: 8px;
        background: #404040;
        border-radius: 4px;
    }
    QSlider::handle:horizontal {
        background: #1DB954;
        border: none;
        width: 18px;
        margin: -5px 0;
        border-radius: 9px;
    }
    QListWidget, QComboBox {
        background-color: #282828;
        color: #FFFFFF;
        border: none;
    }
    QComboBox QAbstractItemView {
        background-color: #282828;
        selection-background-color: #1DB954;
        color: #FFFFFF;
    }
    """

    app.setStyleSheet(spotify_qss)


    window = MusicPlayerGUI()
    window.show()
    sys.exit(app.exec_())