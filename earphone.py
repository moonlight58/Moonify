import os
import fcntl
import struct
import select
import time

# Event structure format for input events
EVENT_FORMAT = 'llHHI'
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)
EV_KEY = 1
KEY_PRESSED = 1

KEY_MAPPING = {
    200: ord('r'),  # KEY_PLAYCD -> Resume
    201: ord('p'),  # KEY_PAUSECD -> Pause
    163: ord('n'),  # KEY_NEXTSONG -> Next
    165: ord('b'),  # KEY_PREVIOUSSONG -> Back
    114: ord('-'),  # KEY_VOLUMEDOWN -> Volume Down
    115: ord('+'),  # KEY_VOLUMEUP -> Volume Up
}

def find_earphone_device():
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

def listen_for_earphone_events(device_path, event_queue):
    try:
        with open(device_path, 'rb') as device:
            fcntl.fcntl(device, fcntl.F_SETFL, os.O_NONBLOCK)
            while True:
                r, _, _ = select.select([device], [], [], 0.1)
                if device in r:
                    try:
                        event_data = device.read(EVENT_SIZE)
                        if event_data:
                            sec, usec, type_id, code, value = struct.unpack(EVENT_FORMAT, event_data)
                            if type_id == EV_KEY and value == KEY_PRESSED:
                                mapped_key = KEY_MAPPING.get(code, code)
                                event_queue.append((code, mapped_key))
                    except BlockingIOError:
                        pass
                    except Exception:
                        break
                time.sleep(0.01)
    except Exception:
        pass