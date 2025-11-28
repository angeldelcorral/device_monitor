# hid_reader.py
import threading
from datetime import datetime
import time

try:
    import hid  # hidapi
except Exception as e:
    hid = None


class HIDReader(threading.Thread):
    """
    Threaded HID reader that posts events to a queue.
    dinfo is the device info dict returned by hid.enumerate()
    """

    def __init__(self, dinfo, out_queue, logger=print):
        super().__init__(daemon=True)
        self.dinfo = dinfo
        self.out_queue = out_queue
        self._stop = threading.Event()
        self.logger = logger or (lambda *a, **k: None)
        self.device = None

    @staticmethod
    def enumerate_devices():
        if hid is None:
            return []
        return list(hid.enumerate())

    def run(self):
        if hid is None:
            self.logger("hidapi not available. Install 'hidapi' or 'hid' package.")
            return
        vid = self.dinfo.get("vendor_id")
        pid = self.dinfo.get("product_id")
        path = self.dinfo.get("path")
        try:
            # prefer open by path if available
            if path:
                self.device = hid.Device(path=path)
            else:
                self.device = hid.Device(vid=vid, pid=pid)
            self.device.set_nonblocking(True)
            self.logger(f"HID opened: vid={hex(vid)} pid={hex(pid)}")
        except Exception as e:
            self.logger(f"Error opening HID: {e}")
            return

        while not self._stop.is_set():
            try:
                data = self.device.read(64)
                if data:
                    evt = {
                        "timestamp": datetime.now().isoformat(),
                        "type": "HID",
                        "data": bytes(data),
                    }
                    # try to create human readable if possible
                    try:
                        # common: keyboard report - 3rd byte keycode (HID boot)
                        if len(data) >= 3:
                            kc = data[2]
                            evt["human"] = f"Keycode {kc}"
                    except Exception:
                        pass
                    self.out_queue.put(evt)
                else:
                    time.sleep(0.02)
            except Exception as e:
                self.logger(f"HID read error: {e}")
                break

        try:
            self.device.close()
        except Exception:
            pass
        self.logger("HIDReader stopped.")

    def stop(self):
        self._stop.set()
