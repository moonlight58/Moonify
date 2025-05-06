import re

def parse_filename(filename):
    """
    Extract artist(s) and title from a file name like:
    '[Artist] - [Title].mp3'
    """
    # Remove file extension
    name = filename.rsplit('.', 1)[0].strip()

    # Split by the first ' - '
    if ' - ' in name:
        artist_part, title_part = name.split(' - ', 1)
    else:
        return "Unknown Artist", name  # fallback

    # Clean artist part
    artists = [a.strip() for a in artist_part.split(',')]
    title = title_part.strip()

    return ', '.join(artists), title
