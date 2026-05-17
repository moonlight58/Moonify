# Domain Glossary: Moonify

- **Track**: A single audio entity. Represents an audio file on disk and its associated metadata (artist, title, duration).
- **Library**: The collection of tracks available in a specific folder.
- **Playback Queue**: A stateful sequence of tracks being played or scheduled to play.
- **Player**: The central orchestrator that manages playback state, volume, and coordinates with external services.
- **TUI**: The Terminal User Interface for interacting with Moonify.
- **Media Controller**: An interface for external hardware (like earphone buttons) to control playback.
- **Presence**: The module responsible for broadcasting the current playback status to external services like Discord.
- **Playback Engine**: The low-level audio driver responsible for loading and playing audio files (currently implemented via `pygame.mixer`).
