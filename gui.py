import sys
import os
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QSlider, QListWidget, QFileDialog, QHBoxLayout, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
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
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play)
        controls_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause)
        controls_layout.addWidget(self.pause_btn)

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_track)
        controls_layout.addWidget(self.next_btn)

        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.prev_track)
        controls_layout.addWidget(self.prev_btn)
        
        self.shuffle_btn = QPushButton("Shuffle: Off")
        self.shuffle_btn.setCheckable(True)
        self.shuffle_btn.clicked.connect(self.toggle_shuffle)
        controls_layout.addWidget(self.shuffle_btn)

        main_layout.addLayout(controls_layout)

        # Volume
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        main_layout.addWidget(QLabel("Volume"))
        main_layout.addWidget(self.volume_slider)

        # Open playlist
        self.playlist_btn = QPushButton("Open Playlist Folder")
        self.playlist_btn.clicked.connect(self.open_playlist)
        main_layout.addWidget(self.playlist_btn)

        self.setLayout(main_layout)

    def open_playlist(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Playlist Folder")
        if folder:
            self.player = Player(folder)
            self.label.setText("Playlist loaded. Ready to play.")
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
            if self.player.paused:
                self.player.resume()
            else:
                self.player.play()
            self.waiting_for_next = False  # Reset guard when a new song starts
            info = self.player.get_current_track_info()
            self.label.setText(f"Playing: {info['title']} - {info['artist']}")
            self.playlist_widget.setCurrentRow(self.player.current_index)
            self.show_cover()
            self.timer.start(500)

    def pause(self):
        if self.player:
            self.player.pause()
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
            self.shuffle_btn.setText("Shuffle: On")
            random.shuffle(self.player.music_files)
        else:
            self.shuffle_btn.setText("Shuffle: Off")
            self.player.music_files.sort()
        self.update_playlist()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MusicPlayerGUI()
    window.show()
    sys.exit(app.exec_())