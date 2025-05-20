import os
import time
import subprocess
from pypresence import Presence

class DiscordRPC:
    def __init__(self, enable_rpc=False):
        self.client_id = os.getenv("DISCORD_CLIENT_ID")
        self.rpc = None
        self.user_choice = 1 if enable_rpc else 0

        if self.user_choice and self.client_id and self.is_discord_running():
            try:
                self.rpc = Presence(self.client_id)
                self.rpc.connect()
                print("[DiscordRPC] Discord Rich Presence enabled.")
            except Exception as e:
                print(f"[DiscordRPC] Failed to connect: {e}")
                self.rpc = None
        else:
            print("[DiscordRPC] Discord Rich Presence disabled or Discord not running.")

    def is_discord_running(self):
        """Check if Discord is running (Linux only)."""
        try:
            output = subprocess.check_output(["pgrep", "-f", "discord"], text=True)
            return bool(output.strip())
        except Exception:
            return False

    def show_track(self, title, artist, cover_url=None):
        """Display current track in Discord Rich Presence."""
        if not self.rpc:
            return

        start_time = int(time.time())

        activity = {
            "details": f"🎧 {title}",
            "state": f"{artist}",
            "start": start_time,
            "small_text": "Moonify 🎶"
        }

        if cover_url:
            activity["large_image"] = cover_url  # Imgur image ID or Discord asset key
        else:
            activity["large_image"] = "default_album"  # Use a fallback image set in Dev Portal

        try:
            self.rpc.update(**activity)
        except Exception as e:
            print(f"[DiscordRPC] Failed to update: {e}")

    def clear(self):
        """Clear Discord presence on stop/exit."""
        if self.rpc:
            try:
                self.rpc.clear()
                self.rpc.close()
            except Exception as e:
                print(f"[DiscordRPC] Failed to clear: {e}")
