# plotter.py
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from datetime import datetime
import matplotlib.dates as mdates
import queue


class EventPlotter:
    def __init__(self, parent_root, event_queue: queue.Queue):
        self.parent = parent_root
        self.event_queue = event_queue
        # internal buffer for plotting
        self.kbd_times = []
        self.mouse_times = []
        self.mouse_positions = []  # list of (x,y,ts)
        self.fig = Figure(figsize=(6, 3), dpi=100)
        self.ax_timeline = self.fig.add_subplot(121)
        self.ax_mouse = self.fig.add_subplot(122)
        self.canvas = None
        self.ani = None

    def attach(self, tk_parent_frame):
        # create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=tk_parent_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ax_timeline.set_title("Events timeline")
        self.ax_mouse.set_title("Mouse trace")
        self.ax_timeline.xaxis_date()
        self.ax_timeline.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))

        # start animation
        self.ani = animation.FuncAnimation(self.fig, self._update_plot, interval=500)
        self.canvas.draw()

    def push_event(self, evt):
        # push events from outside UI poller as well
        etype = evt.get("type")
        ts = evt.get("timestamp")
        try:
            t = datetime.fromisoformat(ts)
        except Exception:
            t = datetime.now()
        if etype in ("KBD", "HID"):
            self.kbd_times.append(t)
        if etype in ("MOUSE",):
            self.mouse_times.append(t)
            data = evt.get("data", {})
            x = data.get("x")
            y = data.get("y")
            if x is not None and y is not None:
                self.mouse_positions.append((x, y, t))

    def _drain_queue(self):
        drained = []
        try:
            while True:
                evt = self.event_queue.get_nowait()
                drained.append(evt)
        except Exception:
            pass
        return drained

    def _update_plot(self, frame):
        # drain queue first
        try:
            while True:
                evt = self.event_queue.get_nowait()
                self._process_event(evt)
        except Exception:
            pass

        # timeline: show counts per time window
        self.ax_timeline.clear()
        self.ax_mouse.clear()
        if self.kbd_times:
            self.ax_timeline.plot(
                self.kbd_times,
                [1] * len(self.kbd_times),
                marker="o",
                linestyle="None",
                label="kbd",
            )
        if self.mouse_times:
            self.ax_timeline.plot(
                self.mouse_times,
                [0.5] * len(self.mouse_times),
                marker="x",
                linestyle="None",
                label="mouse",
            )
        self.ax_timeline.legend(loc="upper left")
        self.ax_timeline.set_ylim(0, 1.5)

        # mouse trace
        if self.mouse_positions:
            xs = [p[0] for p in self.mouse_positions[-200:]]
            ys = [p[1] for p in self.mouse_positions[-200:]]
            self.ax_mouse.plot(xs, ys, "-o", markersize=3)
            self.ax_mouse.invert_yaxis()

        self.fig.tight_layout()
        if self.canvas:
            self.canvas.draw()

    def _process_event(self, evt):
        etype = evt.get("type")
        ts = evt.get("timestamp")
        try:
            t = datetime.fromisoformat(ts)
        except Exception:
            t = datetime.now()
        if etype in ("KBD", "HID"):
            self.kbd_times.append(t)
        if etype == "MOUSE":
            self.mouse_times.append(t)
            d = evt.get("data", {})
            if "x" in d and "y" in d:
                self.mouse_positions.append((d["x"], d["y"], t))
