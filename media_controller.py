import os
import fcntl
import struct
import select
import time
from abc import ABC, abstractmethod
from typing import List
from threading import Thread

# Event structure format for input events
EVENT_FORMAT = 'llHHI'
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)
EV_KEY = 1
KEY_PRESSED = 1

class MediaController(ABC):
    @abstractmethod
    def pop_actions(self) -> List[str]:
        pass

class LinuxMediaController(MediaController):
    def __init__(self, device_path: str):
        self.device_path = device_path
        self.events = []
        self.thread = None
        
        self.mapping = {
            200: "resume",
            201: "pause",
            163: "next",
            165: "previous",
            114: "volume_down",
            115: "volume_up",
        }

        if self.device_path and os.path.exists(self.device_path):
            self.thread = Thread(target=self._listen, daemon=True)
            self.thread.start()

    def _listen(self):
        try:
            with open(self.device_path, 'rb') as device:
                fcntl.fcntl(device, fcntl.F_SETFL, os.O_NONBLOCK)
                while True:
                    r, _, _ = select.select([device], [], [], 0.1)
                    if device in r:
                        try:
                            event_data = device.read(EVENT_SIZE)
                            if event_data:
                                sec, usec, type_id, code, value = struct.unpack(EVENT_FORMAT, event_data)
                                if type_id == EV_KEY and value == KEY_PRESSED:
                                    self.events.append(code)
                        except BlockingIOError:
                            pass
                        except Exception:
                            break
                    time.sleep(0.01)
        except Exception:
            pass

    def pop_actions(self) -> List[str]:
        actions = []
        while self.events:
            code = self.events.pop(0)
            action = self.mapping.get(code)
            if action:
                actions.append(action)
        return actions

class NullMediaController(MediaController):
    def pop_actions(self) -> List[str]:
        return []

def find_media_device():
    earphone_keywords = ["buds", "headphone", "earphone", "avrcp"]
    for i in range(30):
        device_path = f"/dev/input/event{i}"
        if not os.path.exists(device_path):
            continue
        try:
            with open(device_path, "rb") as f:
                buffer = bytearray(256)
                EVIOCGNAME = 0x81004506
                fcntl.ioctl(f, EVIOCGNAME, buffer)
                device_name = buffer.decode('utf-8').rstrip('\0')
                if any(keyword in device_name.lower() for keyword in earphone_keywords):
                    return device_path, device_name
        except:
            continue
    return None, None
