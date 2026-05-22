import threading


class NullPresence:
    def track_started(self, track):
        return None

    def close(self):
        return None


class DiscordTransport:
    def __init__(self, rpc=None):
        if rpc is None:
            from discord_rpc import DiscordRPC

            rpc = DiscordRPC(enable_rpc=True)
        self.rpc = rpc

    def is_enabled(self):
        return self.rpc.is_enabled()

    def show_track(self, title, artist, cover_url=None):
        self.rpc.show_track(title=title, artist=artist, cover_url=cover_url)

    def close(self):
        self.rpc.clear()


class ImgurCoverProvider:
    def __init__(self, cover_path="/tmp/current_cover.jpg", extract_cover_func=None, upload_func=None):
        self.cover_path = cover_path
        self.extract_cover = extract_cover_func
        self.upload = upload_func

    def cover_url_for(self, track):
        if self.extract_cover is None or self.upload is None:
            from cover import extract_cover, upload_to_imgur

            self.extract_cover = extract_cover
            self.upload = upload_to_imgur

        if self.extract_cover(track["path"], self.cover_path):
            return self.upload(self.cover_path)
        return None


class DiscordPresence:
    def __init__(self, transport=None, cover_provider=None, debounce_seconds=2):
        self.transport = transport or DiscordTransport()
        self.cover_provider = cover_provider or ImgurCoverProvider()
        self.debounce_seconds = debounce_seconds
        self.stop_event = threading.Event()
        self.thread = None
        self.pending_track = None
        self.last_track = None

    def track_started(self, track):
        if not self.transport.is_enabled():
            return
        self.pending_track = track.copy()
        if not self.thread or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()

    def close(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=2)
        self.transport.close()

    def _worker(self):
        while not self.stop_event.is_set():
            if not self.pending_track or self.pending_track == self.last_track:
                self.stop_event.wait(0.1)
                continue

            snapshot = self.pending_track.copy()
            waited = 0
            while waited < self.debounce_seconds:
                self.stop_event.wait(0.1)
                waited += 0.1
                if self.pending_track != snapshot:
                    break
            else:
                self._show_track(snapshot)
                self.last_track = snapshot
                self.pending_track = None

    def _show_track(self, track):
        cover_url = None
        try:
            cover_url = self.cover_provider.cover_url_for(track)
        except Exception as exc:
            print(f"[DiscordPresence] Cover upload failed: {exc}")

        self.transport.show_track(
            title=track["title"],
            artist=track["artist"],
            cover_url=cover_url,
        )


def build_presence(enable_rpc=False):
    if not enable_rpc:
        return NullPresence()
    return DiscordPresence()
