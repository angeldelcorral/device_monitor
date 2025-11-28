# usb_reader.py
import threading
import time
from datetime import datetime

import usb.core
import usb.util


class USBReader(threading.Thread):
    def __init__(self, dev_info, out_queue, logger=print):
        super().__init__(daemon=True)
        self.dev_info = dev_info  # pyusb device instance
        self.out_queue = out_queue
        self._stop = threading.Event()
        self.logger = logger or (lambda *a, **k: None)

    @staticmethod
    def enumerate_devices():
        try:
            devs = usb.core.find(find_all=True)
            return [d for d in devs]
        except Exception:
            return []

    def run(self):
        dev = self.dev_info
        self.logger(f"USBReader starting for {dev}")
        # try to set configuration (non-destructive)
        try:
            dev.set_configuration()
        except Exception:
            pass

        while not self._stop.is_set():
            # iterate endpoints and attempt reads (best-effort)
            try:
                cfg = dev.get_active_configuration()
                for intf in cfg:
                    for ep in intf:
                        if not ep:
                            continue
                        try:
                            data = dev.read(
                                ep.bEndpointAddress, ep.wMaxPacketSize, timeout=50
                            )
                            if data:
                                evt = {
                                    "timestamp": datetime.now().isoformat(),
                                    "type": "USB",
                                    "data": bytes(data),
                                }
                                self.out_queue.put(evt)
                        except usb.core.USBError:
                            pass
            except Exception:
                # fallback: sleep a bit
                time.sleep(0.1)

        self.logger("USBReader stopped.")

    def stop(self):
        self._stop.set()
