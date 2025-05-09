from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image
import io
from imgurpython import ImgurClient
import os

def extract_cover(mp3_path, cover_path):
    try:
        audio = MP3(mp3_path, ID3=ID3)
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                with open(cover_path, 'wb') as img:
                    img.write(tag.data)
                return True
    except Exception as e:
        print(f"Error extracting cover: {e}")
    return False

def upload_to_imgur(image_path):
    client_id = os.getenv("IMGUR_CLIENT_ID")
    client_secret = os.getenv("IMGUR_CLIENT_SECRET")
    client = ImgurClient(client_id, client_secret)
    uploaded_image = client.upload_from_path(image_path, anon=True)
    return uploaded_image['link']