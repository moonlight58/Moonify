from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image
import io
from imgurpython import ImgurClient
import os

def extract_cover(mp3_path, output_path):
    audio = MP3(mp3_path, ID3=ID3)
    for tag in audio.tags.values():
        if isinstance(tag, APIC):
            img = Image.open(io.BytesIO(tag.data))
            img.save(output_path)
            return output_path
    return None

def upload_to_imgur(image_path):
    client_id = os.getenv("IMGUR_CLIENT_ID")
    client_secret = os.getenv("IMGUR_CLIENT_SECRET")
    client = ImgurClient(client_id, client_secret)
    uploaded_image = client.upload_from_path(image_path, anon=True)
    return uploaded_image['link']