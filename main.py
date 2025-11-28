# main.py
import os
import threading
import queue
import csv
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from ttkbootstrap import Style
from ttkbootstrap.constants import *
import ttkbootstrap as ttk

from hid_reader import HIDReader
from serial_reader import SerialReader
from usb_reader import USBReader
from km_listener import KMListener
from plotter import EventPlotter
from utils import ensure_dir

# central queue to receive events from workers
EVENT_QUEUE = queue.Queue()

APP_TITLE = "Device Monitor - Tk (ttkbootstrap) - Safe Use Only"


class DeviceMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1100x720")

        self.style = Style(theme="cosmo")  # modern theme
        self.style.configure("TLabel", font=("Inter", 11))
        self.style.configure("TButton", font=("Inter", 10))
        self.style.configure("TEntry", font=("Inter", 10))

        # Workers
        self.hid_worker = None
        self.serial_worker = None
        self.usb_worker = None
        self.km_worker = None

        # internal state
        self.device_index_map = []  # list of tuples (type, info)
        self.current_selection = None
        self.running = False
        self.log_file = None
        self.log_dir = ensure_dir("logs")
        self.event_log = []  # in-memory events for CSV/export

        # plotting
        self.plotter = EventPlotter(self.root, event_queue=EVENT_QUEUE)

        # UI
        self._build_ui()

        # start queue poller
        self.root.after(200, self._poll_events)

    def _build_ui(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side=TOP, fill=X, padx=10, pady=8)

        # Filter
        ttk.Label(top_frame, text="Filter:").pack(side=LEFT, padx=(0, 6))
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(top_frame, textvariable=self.filter_var, width=30)
        self.filter_entry.pack(side=LEFT)
        self.filter_entry.bind("<KeyRelease>", lambda e: self.refresh_devices())

        ttk.Button(
            top_frame, text="Refresh Devices", command=self.refresh_devices
        ).pack(side=LEFT, padx=8)
        ttk.Button(top_frame, text="Save Log...", command=self.save_log_dialog).pack(
            side=LEFT, padx=8
        )
        ttk.Button(top_frame, text="Export CSV", command=self.export_csv).pack(
            side=LEFT, padx=8
        )

        # Left: device list & controls
        left = ttk.Frame(self.root)
        left.pack(side=LEFT, fill=Y, padx=10, pady=6)

        ttk.Label(left, text="Detected devices:").pack(anchor=W)
        self.tree = ttk.Treeview(
            left, columns=("type", "name"), show="headings", height=20
        )
        self.tree.heading("type", text="Type")
        self.tree.heading("name", text="Name")
        self.tree.pack(fill=Y, expand=False)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=X, pady=6)
        self.btn_start = ttk.Button(
            btn_frame,
            text="Start Monitor",
            bootstyle="success",
            command=self.start_monitor,
            state=NORMAL,
        )
        self.btn_start.pack(side=LEFT, padx=4)
        self.btn_stop = ttk.Button(
            btn_frame,
            text="Stop Monitor",
            bootstyle="danger",
            command=self.stop_monitor,
            state=DISABLED,
        )
        self.btn_stop.pack(side=LEFT, padx=4)

        ttk.Separator(left, orient=HORIZONTAL).pack(fill=X, pady=6)
        ttk.Label(left, text="Options:").pack(anchor=W)
        self.km_global_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            left,
            text="Enable global keyboard/mouse capture",
            variable=self.km_global_var,
        ).pack(anchor=W)
        ttk.Label(
            left, text="(Requires privileges; use responsibly)", foreground="#a00"
        ).pack(anchor=W)

        # Right: info, live text, and plots
        right = ttk.Frame(self.root)
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=6)

        # Info & live text
        info_frame = ttk.Frame(right)
        info_frame.pack(fill=X)
        ttk.Label(info_frame, text="Device Info / Live Log:").pack(anchor=W)
        self.log_text = tk.Text(info_frame, height=12, wrap="none")
        self.log_text.pack(fill=X, expand=False)

        # small controls
        control_frame = ttk.Frame(info_frame)
        control_frame.pack(fill=X, pady=6)
        ttk.Button(
            control_frame,
            text="Clear Log",
            command=lambda: self.log_text.delete("1.0", END),
        ).pack(side=LEFT)
        ttk.Button(
            control_frame,
            text="Open log folder",
            command=lambda: (
                os.startfile(self.log_dir)
                if os.name == "nt"
                else os.system(f'xdg-open "{self.log_dir}"')
            ),
        ).pack(side=LEFT, padx=6)

        # Plots area handled by EventPlotter
        plot_frame = ttk.Frame(right)
        plot_frame.pack(fill=BOTH, expand=True, pady=(8, 0))
        self.plotter.attach(plot_frame)

        # initial device enumerate
        self.refresh_devices()

    def log(self, text, level="INFO"):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {text}"
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        # append to memory log
        self.event_log.append({"timestamp": ts, "level": level, "text": text})

    def refresh_devices(self):
        # enumerate devices using helper modules
        self.tree.delete(*self.tree.get_children())
        self.device_index_map.clear()
        filter_text = self.filter_var.get().lower().strip()

        # HID devices
        hid_list = HIDReader.enumerate_devices()
        for info in hid_list:
            name = (
                info.get("product_string")
                or f"HID {hex(info.get('vendor_id',0))}:{hex(info.get('product_id',0))}"
            )
            if filter_text and filter_text not in name.lower():
                continue
            idx = self.tree.insert("", "end", values=("HID", name))
            self.device_index_map.append(("HID", info))

        # USB devices (raw)
        usb_list = USBReader.enumerate_devices()
        for info in usb_list:
            name = f"USB {hex(info['idVendor'])}:{hex(info['idProduct'])}"
            if filter_text and filter_text not in name.lower():
                continue
            idx = self.tree.insert("", "end", values=("USB", name))
            self.device_index_map.append(("USB", info))

        # COM ports
        com_list = SerialReader.list_ports()
        for p in com_list:
            if filter_text and filter_text not in p.lower():
                continue
            idx = self.tree.insert("", "end", values=("COM", p))
            self.device_index_map.append(("COM", p))

        self.log(
            f"Devices refreshed. HID:{len(hid_list)} USB:{len(usb_list)} COM:{len(com_list)}"
        )

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        line = f"[{ts}] [{level}] {text}"
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        # append to memory log
        self.event_log.append({"timestamp": ts, "level": level, "text": text})

    def refresh_devices(self):
        # enumerate devices using helper modules
        self.tree.delete(*self.tree.get_children())
        self.device_index_map.clear()
        filter_text = self.filter_var.get().lower().strip()

        # HID devices
        hid_list = HIDReader.enumerate_devices()
        for info in hid_list:
            name = (
                info.get("product_string")
                or f"HID {hex(info.get('vendor_id',0))}:{hex(info.get('product_id',0))}"
            )
            if filter_text and filter_text not in name.lower():
                continue
            idx = self.tree.insert("", "end", values=("HID", name))
            self.device_index_map.append(("HID", info))

        # USB devices (raw)
        usb_list = USBReader.enumerate_devices()
        for info in usb_list:
            name = f"USB {hex(info['idVendor'])}:{hex(info['idProduct'])}"
            if filter_text and filter_text not in name.lower():
                continue
            idx = self.tree.insert("", "end", values=("USB", name))
            self.device_index_map.append(("USB", info))

        # COM ports
        com_list = SerialReader.list_ports()
        for p in com_list:
            if filter_text and filter_text not in p.lower():
                continue
            idx = self.tree.insert("", "end", values=("COM", p))
            self.device_index_map.append(("COM", p))

        self.log(
            f"Devices refreshed. HID:{len(hid_list)} USB:{len(usb_list)} COM:{len(com_list)}"
        )

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        self.current_selection = self.device_index_map[idx]
        self.log(
            f"Selected {self.current_selection[0]} -> {str(self.current_selection[1])}"
        )

    def start_monitor(self):
        if not self.current_selection:
            messagebox.showwarning(
                "Select device", "Please select a device from the list to monitor."
            )
            return

        if self.running:
            self.log("Already running.")
            return

        dtype, dinfo = self.current_selection
        self.running = True
        self.btn_start.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)

        # start according to type
        if dtype == "HID":
            self.hid_worker = HIDReader(dinfo, EVENT_QUEUE, logger=self.log)
            self.hid_worker.start()
            self.log("HID worker started.")
        elif dtype == "COM":
            self.serial_worker = SerialReader(dinfo, EVENT_QUEUE, logger=self.log)
            self.serial_worker.start()
            self.log("Serial worker started.")
        elif dtype == "USB":
            self.usb_worker = USBReader(dinfo, EVENT_QUEUE, logger=self.log)
            self.usb_worker.start()
            self.log("USB raw worker started.")

        # optional global keyboard/mouse
        if self.km_global_var.get():
            self.km_worker = KMListener(EVENT_QUEUE, logger=self.log)
            self.km_worker.start()
            self.log("Keyboard/Mouse global listener started (use responsibly).")

    def stop_monitor(self):
        self.running = False
        self.btn_start.config(state=NORMAL)
        self.btn_stop.config(state=DISABLED)
        # stop workers
        if self.hid_worker:
            self.hid_worker.stop()
            self.hid_worker = None
        if self.serial_worker:
            self.serial_worker.stop()
            self.serial_worker = None
        if self.usb_worker:
            self.usb_worker.stop()
            self.usb_worker = None
        if self.km_worker:
            self.km_worker.stop()
            self.km_worker = None
        self.log("All workers stopped.")

    def save_log_dialog(self):
        default = os.path.join(
            self.log_dir, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        file = filedialog.asksaveasfilename(
            defaultextension=".txt", initialfile=os.path.basename(default)
        )
        if not file:
            return
        with open(file, "w", encoding="utf-8") as f:
            f.write(self.log_text.get("1.0", "end"))
        messagebox.showinfo("Saved", f"Log saved to {file}")

    def export_csv(self):
        if not self.event_log:
            messagebox.showinfo("No events", "No events to export yet.")
            return
        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not file:
            return
        keys = ["timestamp", "level", "text"]
        with open(file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, keys)
            writer.writeheader()
            writer.writerows(self.event_log)
        messagebox.showinfo("Exported", f"CSV exported to {file}")

    def _poll_events(self):
        # retrieve events from queue and update UI + plots
        try:
            while True:
                evt = EVENT_QUEUE.get_nowait()
                # evt expected to be dict: {"type": "...", "data": ..., "timestamp": "...", ...}
                ts = evt.get("timestamp", datetime.now().isoformat())
                etype = evt.get("type", "EVENT")
                data = evt.get("data", "")
                self.log(f"[{etype}] {data}")
                # forward to plotter
                self.plotter.push_event(evt)
        except queue.Empty:
            pass
        finally:
            self.root.after(150, self._poll_events)


def main():
    root = tk.Tk()
    app = DeviceMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
    