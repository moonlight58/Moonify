import os

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, ListItem, ListView, Static

from earphone import find_earphone_device
from player import Player


def format_time(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def progress_bar(elapsed, total, width=36):
    if total <= 0:
        return "[" + (" " * width) + "]"
    ratio = min(max(elapsed / total, 0), 1)
    filled = int(ratio * width)
    return "[" + ("█" * filled) + (" " * (width - filled)) + "]"


class MessageScreen(ModalScreen):
    BINDINGS = [Binding("escape,enter,q", "dismiss", "Close")]

    def __init__(self, title, message):
        super().__init__()
        self.title = title
        self.message = message

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self.title, id="dialog-title")
            yield Static(self.message, id="dialog-message")
            yield Button("OK", id="ok", variant="primary")

    @on(Button.Pressed, "#ok")
    def close_dialog(self):
        self.dismiss()


class SearchScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("p", "play_now", "Play"),
        Binding("q", "queue_next", "Queue"),
    ]

    def __init__(self, songs):
        super().__init__()
        self.songs = songs
        self.matches = songs[:]

    def compose(self) -> ComposeResult:
        with Container(id="search-dialog"):
            yield Label("Search tracks", id="dialog-title")
            yield Input(placeholder="Type part of a file name", id="search-input")
            yield ListView(id="search-results")
            with Horizontal(id="dialog-actions"):
                yield Button("Play now", id="play-now", variant="primary")
                yield Button("Queue next", id="queue-next")
                yield Button("Cancel", id="cancel")

    def on_mount(self):
        self.query_one("#search-input", Input).focus()
        self.update_results("")

    @on(Input.Changed, "#search-input")
    def search_changed(self, event: Input.Changed):
        self.update_results(event.value)

    @on(Input.Submitted, "#search-input")
    def search_submitted(self):
        self.action_play_now()

    @on(Button.Pressed, "#play-now")
    def play_pressed(self):
        self.action_play_now()

    @on(Button.Pressed, "#queue-next")
    def queue_pressed(self):
        self.action_queue_next()

    @on(Button.Pressed, "#cancel")
    def cancel_pressed(self):
        self.dismiss(None)

    def action_cancel(self):
        self.dismiss(None)

    def action_play_now(self):
        song = self.selected_song()
        if song:
            self.dismiss(("play", song))

    def action_queue_next(self):
        song = self.selected_song()
        if song:
            self.dismiss(("queue", song))

    def selected_song(self):
        results = self.query_one("#search-results", ListView)
        if not self.matches:
            return None
        index = results.index if results.index is not None else 0
        return self.matches[index]

    def update_results(self, term):
        term = term.lower().strip()
        self.matches = [song for song in self.songs if term in song.lower()] if term else self.songs[:]
        results = self.query_one("#search-results", ListView)
        results.clear()
        if not self.matches:
            results.append(ListItem(Label("No tracks found")))
            return
        for song in self.matches:
            results.append(ListItem(Label(song)))
        results.index = 0


class PlaylistScreen(Screen):
    BINDINGS = [Binding("escape,q", "cancel", "Cancel")]

    def __init__(self, base_folder, title="Select playlist"):
        super().__init__()
        self.base_folder = base_folder
        self.title = title
        self.playlists = self.load_playlists()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="setup"):
            yield Label(self.title, id="setup-title")
            if self.playlists:
                playlist_list = ListView(id="playlists")
                for name, path in self.playlists:
                    item = ListItem(Label(name))
                    item.playlist_path = path
                    playlist_list.append(item)
                yield playlist_list
                yield Static("Enter selects a playlist. Esc cancels.", classes="hint")
            else:
                yield Static("No playlist folders found in music/.", classes="empty")
        yield Footer()

    @on(ListView.Selected, "#playlists")
    def playlist_selected(self, event: ListView.Selected):
        self.dismiss(event.item.playlist_path)

    def action_cancel(self):
        self.dismiss(None)

    def load_playlists(self):
        if not os.path.exists(self.base_folder):
            return []
        return [
            (name, os.path.join(self.base_folder, name))
            for name in sorted(os.listdir(self.base_folder))
            if os.path.isdir(os.path.join(self.base_folder, name))
        ]


class SetupScreen(Screen):
    def __init__(self, music_folder, earphone_device, device_name):
        super().__init__()
        self.music_folder = music_folder
        self.earphone_device = earphone_device
        self.device_name = device_name
        self.playlist = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="setup"):
            yield Label("Moonify", id="setup-title")
            device_text = (
                f"Earphone device detected: {self.device_name}"
                if self.earphone_device
                else "No earphone device detected. Keyboard controls are available."
            )
            yield Static(device_text, id="device-status")
            with Horizontal(id="setup-body"):
                with Vertical(classes="panel"):
                    yield Label("Playlist", classes="panel-title")
                    yield ListView(id="playlists")
                with Vertical(classes="panel"):
                    yield Label("Options", classes="panel-title")
                    yield Checkbox("Discord Rich Presence", id="rpc")
                    yield Checkbox("Loop playlist", id="loop")
                    yield Checkbox("Shuffle tracks", id="shuffle")
                    yield Button("Start", id="start", variant="primary")
        yield Footer()

    def on_mount(self):
        playlists = self.load_playlists()
        playlist_list = self.query_one("#playlists", ListView)
        for name, path in playlists:
            item = ListItem(Label(name))
            item.playlist_path = path
            playlist_list.append(item)
        if playlists:
            playlist_list.index = 0
            self.playlist = playlists[0][1]
        else:
            self.query_one("#start", Button).disabled = True
            playlist_list.append(ListItem(Label("No playlist folders found in music/")))

    @on(ListView.Highlighted, "#playlists")
    def playlist_highlighted(self, event: ListView.Highlighted):
        if hasattr(event.item, "playlist_path"):
            self.playlist = event.item.playlist_path

    @on(ListView.Selected, "#playlists")
    def playlist_selected(self, event: ListView.Selected):
        if hasattr(event.item, "playlist_path"):
            self.playlist = event.item.playlist_path
            self.start_player()

    @on(Button.Pressed, "#start")
    def start_pressed(self):
        self.start_player()

    def start_player(self):
        if not self.playlist:
            self.app.push_screen(MessageScreen("Playlist required", "Select a playlist before starting."))
            return
        if not [song for song in os.listdir(self.playlist) if song.endswith(".mp3")]:
            self.app.push_screen(MessageScreen("Empty playlist", "The selected playlist has no .mp3 files."))
            return
        player = Player(
            self.playlist,
            loop=self.query_one("#loop", Checkbox).value,
            shuffle=self.query_one("#shuffle", Checkbox).value,
            earphone_device=self.earphone_device,
            enable_rpc=self.query_one("#rpc", Checkbox).value,
        )
        self.app.switch_screen(PlayerScreen(player))

    def load_playlists(self):
        if not os.path.exists(self.music_folder):
            return []
        return [
            (name, os.path.join(self.music_folder, name))
            for name in sorted(os.listdir(self.music_folder))
            if os.path.isdir(os.path.join(self.music_folder, name))
        ]


class PlayerScreen(Screen):
    BINDINGS = [
        Binding("p", "pause", "Pause"),
        Binding("r", "resume", "Resume"),
        Binding("space", "toggle_pause", "Play/Pause"),
        Binding("n", "next", "Next"),
        Binding("b", "previous", "Back"),
        Binding("+", "volume_up", "Volume +"),
        Binding("-", "volume_down", "Volume -"),
        Binding("c", "change_playlist", "Playlist"),
        Binding("s", "search", "Search"),
        Binding("q", "quit_app", "Quit"),
    ]

    def __init__(self, player):
        super().__init__()
        self.player = player
        self.started = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="player"):
            with Horizontal(id="player-grid"):
                with Vertical(classes="panel", id="now-playing-panel"):
                    yield Label("Now playing", classes="panel-title")
                    yield Static("", id="track-title")
                    yield Static("", id="track-artist")
                    yield Static("", id="status")
                    yield Static("", id="progress")
                    yield Static("", id="volume")
                with Vertical(classes="panel", id="queue-panel"):
                    yield Label("Up next", classes="panel-title")
                    yield ListView(id="queue")
            yield Static("", id="controls")
        yield Footer()

    def on_mount(self):
        self.player.play()
        self.started = True
        self.set_interval(0.25, self.refresh_player)
        self.refresh_player()

    def on_unmount(self):
        if self.started:
            self.player.stop()

    def refresh_player(self):
        self.handle_earphone_events()
        self.player.advance_if_finished()

        info = self.player.get_current_track_info()
        elapsed = max(self.player.get_elapsed_ms() // 1000, 0)
        total = info["duration"]
        status = "Paused" if self.player.paused else "Playing"

        self.query_one("#track-title", Static).update(info["title"])
        self.query_one("#track-artist", Static).update(info["artist"])
        self.query_one("#status", Static).update(f"{status} · Track {info['index'] + 1}/{info['track_count']}")
        self.query_one("#progress", Static).update(
            f"{progress_bar(elapsed, total)} {format_time(elapsed)} / {format_time(total)}"
        )
        self.query_one("#volume", Static).update(f"Volume {int(info['volume'] * 100)}%")
        self.query_one("#controls", Static).update(
            "Space play/pause · N next · B back · +/- volume · S search · C playlist · Q quit"
        )
        self.refresh_queue()

    def refresh_queue(self):
        queue = self.query_one("#queue", ListView)
        queue.clear()
        for offset, song in self.player.upcoming_tracks():
            queue.append(ListItem(Label(f"{offset}. {song}")))

    def handle_earphone_events(self):
        for action in self.player.pop_earphone_actions():
            if action == "pause":
                self.action_pause()
            elif action == "resume":
                self.action_resume()
            elif action == "next":
                self.action_next()
            elif action == "previous":
                self.action_previous()
            elif action == "volume_up":
                self.action_volume_up()
            elif action == "volume_down":
                self.action_volume_down()

    def action_pause(self):
        if not self.player.paused:
            self.player.pause()
            self.refresh_player()

    def action_resume(self):
        if self.player.paused:
            self.player.resume()
            self.refresh_player()

    def action_toggle_pause(self):
        self.player.toggle_pause()
        self.refresh_player()

    def action_next(self):
        self.player.next_track()
        self.refresh_player()

    def action_previous(self):
        self.player.previous_track()
        self.refresh_player()

    def action_volume_up(self):
        self.player.adjust_volume(0.1)
        self.refresh_player()

    def action_volume_down(self):
        self.player.adjust_volume(-0.1)
        self.refresh_player()

    def action_change_playlist(self):
        self.app.push_screen(PlaylistScreen(self.player.playlist_base_folder(), "Change playlist"), self.change_playlist)

    def change_playlist(self, playlist):
        if not playlist:
            return
        if not self.player.change_playlist(playlist):
            self.app.push_screen(MessageScreen("Empty playlist", "The selected playlist has no .mp3 files."))
            return
        self.refresh_player()

    def action_search(self):
        self.app.push_screen(SearchScreen(self.player.track_names()), self.handle_search_result)

    def handle_search_result(self, result):
        if not result:
            return
        action, song = result
        if action == "play":
            self.player.play_song(song)
        elif action == "queue":
            self.player.queue_next(song)
        self.refresh_player()

    def action_quit_app(self):
        self.player.stop()
        self.app.exit()


class MoonifyTUI(App):
    CSS = """
    Screen {
        background: #101418;
        color: #d7dde5;
    }

    Header {
        background: #1f6f78;
        color: #ffffff;
    }

    Footer {
        background: #151b20;
        color: #d7dde5;
    }

    #setup, #player {
        height: 100%;
        padding: 1 2;
    }

    #setup-title {
        text-style: bold;
        color: #f4c95d;
        margin-bottom: 1;
    }

    #device-status {
        margin-bottom: 1;
    }

    #setup-body, #player-grid {
        height: 1fr;
    }

    .panel {
        border: round #4d6a7a;
        padding: 1 2;
        margin-right: 1;
        width: 1fr;
        height: 100%;
        background: #151b20;
    }

    .panel-title {
        text-style: bold;
        color: #f4c95d;
        margin-bottom: 1;
    }

    #track-title {
        text-style: bold;
        color: #ffffff;
        margin-bottom: 1;
    }

    #track-artist, #status, #progress, #volume, #controls {
        margin-bottom: 1;
    }

    #controls {
        color: #aeb9c5;
        padding-top: 1;
    }

    ListView {
        height: 1fr;
    }

    ListView > ListItem.--highlight {
        background: #1f6f78;
        color: #ffffff;
    }

    Checkbox {
        margin-bottom: 1;
    }

    Button {
        margin-top: 1;
        width: 100%;
    }

    #dialog, #search-dialog {
        width: 70%;
        height: auto;
        max-height: 80%;
        margin: 2 4;
        padding: 1 2;
        border: round #f4c95d;
        background: #151b20;
    }

    #search-results {
        height: 12;
        margin-top: 1;
    }

    #dialog-title {
        text-style: bold;
        color: #f4c95d;
        margin-bottom: 1;
    }

    #dialog-actions {
        height: auto;
        margin-top: 1;
    }

    #dialog-actions Button {
        width: 1fr;
        margin-right: 1;
    }

    .hint, .empty {
        color: #aeb9c5;
    }
    """

    TITLE = "Moonify"

    def on_mount(self):
        music_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music")
        if not os.path.exists(music_folder):
            self.push_screen(MessageScreen("Missing music folder", "Create a music/ folder before starting."))
            return
        earphone_device, device_name = find_earphone_device()
        self.push_screen(SetupScreen(music_folder, earphone_device, device_name))


def main():
    MoonifyTUI().run()


if __name__ == "__main__":
    main()
