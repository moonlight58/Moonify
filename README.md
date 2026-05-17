# Moonify (Music Player CLI)

**Moonify** is a cross-platform music player for your local `.mp3` files, featuring a command-line TUI (terminal user interface).  
It supports playlists (folders), Discord Rich Presence, Imgur album art upload, and even earphone hardware controls on Linux.

Moonify was originally created as a **personal alternative to Spotify**, motivated by concerns about how Spotify and similar streaming companies treat artists and handle user data.  
This project aims to provide a lightweight, privacy-friendly, and customizable music experience—without streaming, ads, or telemetry.  
You keep full control of your music library, and artists are supported when you buy or download music directly.

You can browse your music library, search, shuffle, and control playback with keyboard shortcuts or compatible earphones (still in development). Optional Discord Rich Presence uses a Discord Application ID and Imgur credentials to display the current track and cover art.

---

## Prerequisites

Before using this application, you need to:

1. **Create a Discord Application**  
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications).
   - Click "New Application", give it a name, and save.
   - Copy the `Application ID` (this will be your `DISCORD_CLIENT_ID`).
   - (Optional) Set up Rich Presence assets (images) if you want custom cover art.

2. **Set Up Imgur API Access (Only Optional if you want Discord RPC)**  
   - Register for a free account at [Imgur](https://api.imgur.com/oauth2/addclient).
   - Create a new application (select "OAuth 2 authorization without a callback URL").
   - Copy your `Client ID` and `Client Secret` and put it in the `.env`.
   - You can use [Postman](https://www.postman.com/) or any API client to test Imgur API requests.
   - For automated uploads, you may need to generate an access token using your credentials.  
     **!!! See [Imgur API docs](https://apidocs.imgur.com/) for details. !!!**

Copy `.env.example` to `.env` and fill in the values if you want Discord Rich Presence and Imgur cover uploads.

---

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/moonlight58/Moonify
   cd music-player-cli
   ```

2. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

   If you install the project as a package, you can also run it with:
   ```bash
   pip install -e .
   ```

   ```bash
   moonify
   ```

---

## Requirements

- Python 3.9+
- [pygame](https://www.pygame.org/) (audio playback)
- [mutagen](https://mutagen.readthedocs.io/) (MP3 metadata)
- [python-dotenv](https://pypi.org/project/python-dotenv/) (`.env` loading)
- [pypresence](https://qwertyquerty.github.io/pypresence/html/index.html) (Discord Rich Presence)
- [imgurpython](https://pypi.org/project/imgurpython/) (Imgur API)
- [Textual](https://textual.textualize.io/) (TUI window manager)

---

## Usage

1. Place your `.mp3` files inside a folder in the `music/` folder.

It will look like this
```
...
├── music/               <--- this is the parent folder
│   ├── Your Playlist 1/ <--- this is the child folder that will act as a "Playlist"
│   │   ├── song n°1
│   │   ├── song n°2
│   │   └── song n°3
│   ├── Your Playlist 2/
│   ├── Your Playlist 3/
│   ├── Your Playlist 4/
│   └── Your Playlist 5/
...
```

2. Make sure your Discord app ID and Imgur credentials are set (via environment variables or config, as required by your code).
3. Run the application:
   ```bash
   python3 music_player.py
   ```
4. Follow the on-screen instructions in the terminal interface.

## Development

Run the focused unit tests with:

```bash
python3 -m unittest discover
```

## Available Actions

- **[P]ause**: Pause the current track
- **[R]esume**: Resume playback if paused
- **[N]ext**: Play the next track
- **[B]ack**: Play the previous track
- **[Q]uit**: Exit the application
- **[+] / [-]**: Increase or decrease the volume
- **[C]hange playlist**: Switch to a different music folder/playlist
- **[S]earch**: Search for a track by file name
- **Earphone controls**: Play/Pause, Next, Previous, Volume Up/Down (if supported)

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
