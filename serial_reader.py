# serial_reader.py
import threading
import time
from datetime import datetime

import serial
import serial.tools.list_ports


class SerialReader(threading.Thread):
    def __init__(self, port, out_queue, logger=print, baud=115200):
        super().__init__(daemon=True)
        self.port = port
        self.baud = baud
        self.out_queue = out_queue
        self._stop = threading.Event()
        self.logger = logger or (lambda *a, **k: None)
        self.ser = None

    @staticmethod
    def list_ports():
        return [p.device for p in serial.tools.list_ports.comports()]

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.5)
            self.logger(f"Opened serial {self.port} @ {self.baud}")
        except Exception as e:
            self.logger(f"Error opening serial {self.port}: {e}")
            return

        while not self._stop.is_set():
            try:
                line = self.ser.readline()
                if line:
                    try:
                        text = line.decode(errors="replace").strip()
                    except Exception:
                        text = repr(line)
                    evt = {
                        "timestamp": datetime.now().isoformat(),
                        "type": "SERIAL",
                        "data": text,
                    }
                    self.out_queue.put(evt)
                else:
                    time.sleep(0.02)
            except Exception as e:
                self.logger(f"Serial read error: {e}")
                break

        try:
            self.ser.close()
        except Exception:
            pass
        self.logger("SerialReader stopped.")

    def stop(self):
        self._stop.set()
