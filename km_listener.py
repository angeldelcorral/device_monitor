# km_listener.py
import threading
from datetime import datetime

# these modules capture global events
try:
    import keyboard
except Exception:
    keyboard = None

try:
    import mouse
except Exception:
    mouse = None


class KMListener(threading.Thread):
    def __init__(self, out_queue, logger=print):
        super().__init__(daemon=True)
        self.out_queue = out_queue
        self.logger = logger or (lambda *a, **k: None)
        self._stop = threading.Event()
        self._hooks = []

    def run(self):
        if keyboard is None and mouse is None:
            self.logger("keyboard/mouse modules not installed.")
            return

        self.logger("KMListener running - hooking events.")
        # keyboard
        if keyboard is not None:
            try:
                keyboard.hook(self._on_keyboard_event)
            except Exception as e:
                self.logger(f"keyboard hook error: {e}")
        if mouse is not None:
            try:
                mouse.hook(self._on_mouse_event)
            except Exception as e:
                self.logger(f"mouse hook error: {e}")

        # block until stop
        while not self._stop.is_set():
            self._stop.wait(0.2)

        # unhook
        try:
            if keyboard is not None:
                keyboard.unhook_all()
            if mouse is not None:
                mouse.unhook_all()
        except Exception:
            pass

        self.logger("KMListener stopped.")

    def _on_keyboard_event(self, event):
        # event: keyboard.KeyboardEvent
        try:
            payload = {
                "timestamp": datetime.now().isoformat(),
                "type": "KBD",
                "data": {
                    "name": getattr(event, "name", str(event)),
                    "event_type": getattr(event, "event_type", ""),
                },
            }
            self.out_queue.put(payload)
        except Exception:
            pass

    def _on_mouse_event(self, event):
        # mouse event objects differ; convert generically
        try:
            # mouse event has attributes: event_type, button, x, y, delta
            payload = {
                "timestamp": datetime.now().isoformat(),
                "type": "MOUSE",
                "data": {},
            }
            if hasattr(event, "event_type"):
                payload["data"]["event_type"] = event.event_type
            if hasattr(event, "button"):
                payload["data"]["button"] = event.button
            if hasattr(event, "x") and hasattr(event, "y"):
                payload["data"]["x"] = event.x
                payload["data"]["y"] = event.y
            if hasattr(event, "delta"):
                payload["data"]["delta"] = event.delta
            self.out_queue.put(payload)
        except Exception:
            pass

    def stop(self):
        self._stop.set()
