# Moonify (Music Player CLI)

A simple command-line interface (CLI) application that plays music from a selected folder containing `.mp3` files.

---

## Project Structure

```
music-player-cli/
├── player.py                # Main player logic and TUI
├── music/                   # Folder to place your .mp3 files
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
├── Terms of Service.md      # Terms of Service (multi-language)
├── Privacy Policy.md        # Privacy Policy (multi-language)
└── ...                      # Other supporting files/modules
```

---

## Prerequisites

Before using this application, you need to:

1. **Create a Discord Application**  
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications).
   - Click "New Application", give it a name, and save.
   - Copy the `Application ID` (this will be your `DISCORD_CLIENT_ID`).
   - (Optional) Set up Rich Presence assets (images) if you want custom cover art.

2. **Set Up Imgur API Access**  
   - Register for a free account at [Imgur](https://api.imgur.com/oauth2/addclient).
   - Create a new application (select "OAuth 2 authorization without a callback URL").
   - Copy your `Client ID` and `Client Secret` and put it in the `.env`.
   - You can use [Postman](https://www.postman.com/) or any API client to test Imgur API requests.
   - For automated uploads, you may need to generate an access token using your credentials.  
     **!!! See [Imgur API docs](https://apidocs.imgur.com/) for details. !!!**

## And please don't forget to change the `.env.example` file to a `.env` file

---

## Installation

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
   cd music-player-cli
   ```

2. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

---

## Requirements

- Python 3.7+
- [pygame](https://www.pygame.org/) (audio playback)
- [mutagen](https://mutagen.readthedocs.io/) (MP3 metadata)
- [click](https://click.palletsprojects.com/) (CLI)
- [pypresence](https://qwertyquerty.github.io/pypresence/html/index.html) (Discord Rich Presence)
- [requests](https://docs.python-requests.org/) (Imgur API)
- [curses](https://docs.python.org/3/library/curses.html) (TUI, included with most Unix Python installs)

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
   python3 player.py
   ```
4. Follow the on-screen instructions in the terminal interface.

**If the TUI doesn't work well for you, or just not for you. You can run the GUI implemented by following the commands below**
   ```bash
   python3 gui.py
   ```

---

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
