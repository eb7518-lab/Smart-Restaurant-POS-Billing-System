"""Charts drawn on a plain tkinter Canvas (no extra libraries needed).

Every chart animates when it first appears and redraws when resized.
"""
import math
import tkinter as tk

from config import COLORS, FONT


def blend(c1, c2, t):
    """Mix two #RRGGBB colours; t=0 gives c1, t=1 gives c2."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def draw_gradient(canvas, w, h, top, bottom):
    for y in range(0, int(h), 3):
        canvas.create_rectangle(0, y, w, y + 3, outline="",
                                fill=blend(top, bottom, y / max(h, 1)))


def short_money(v):
    if v >= 100000:
        return f"{v / 100000:.1f}L"
    if v >= 1000:
        return f"{v / 1000:.1f}k"
    return f"{v:.0f}"


def nice_max(v):
    if v <= 0:
        return 1
    base = 10 ** math.floor(math.log10(v))
    for m in (1, 2, 2.5, 5, 10):
        if v <= m * base:
            return m * base
    return 10 * base


def _ease(t):
    return 1 - (1 - t) ** 3


class AnimatedCanvas(tk.Canvas):
    """Base class: subclasses implement draw(w, h, progress)."""
    default_w = 400

    def __init__(self, parent, title="", height=200):
        super().__init__(parent, height=height, bg=COLORS["card"],
                         highlightthickness=0)
        self.title = title
        self.progress = 0.0
        self.bind("<Configure>", lambda e: self.redraw())
        self.after(60, self.animate)

    def animate(self, step=0, steps=20):
        try:
            self.progress = _ease(step / steps)
            self.redraw()
            if step < steps:
                self.after(16, lambda: self.animate(step + 1, steps))
        except tk.TclError:      # the chart was closed while animating
            pass

    def redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if not w or w < 50:
            w = self.default_w
        if not h or h < 50:
            h = 200
        self.create_text(2, 4, anchor="nw", text=self.title,
                         font=(FONT, 11, "bold"), fill=COLORS["text"])
        self.draw(w, h, self.progress)

    def empty_message(self, w, h, text):
        self.create_text(w / 2, h / 2 + 10, text=text, fill=COLORS["muted"],
                         font=(FONT, 10))


class BarChart(AnimatedCanvas):
    """Vertical bars; the last bar (today) is highlighted."""

    def __init__(self, parent, data, title="", height=200):
        self.data = data
        super().__init__(parent, title, height)

    def draw(self, w, h, p):
        if not self.data or max(v for _, v in self.data) <= 0:
            self.empty_message(w, h, "No sales yet")
            return
        left, right, top, bottom = 46, 10, 36, 26
        plot_w, plot_h = w - left - right, h - top - bottom
        vmax = nice_max(max(v for _, v in self.data))

        for i in range(5):
            y = top + plot_h * (1 - i / 4)
            self.create_line(left, y, w - right, y, fill="#E5E7EB")
            self.create_text(left - 6, y, anchor="e", fill=COLORS["muted"],
                             font=(FONT, 8), text=short_money(vmax * i / 4))

        slot = plot_w / len(self.data)
        light = blend(COLORS["primary"], "#FFFFFF", 0.45)
        for i, (label, value) in enumerate(self.data):
            x0 = left + slot * i + slot * 0.22
            x1 = left + slot * (i + 1) - slot * 0.22
            bar_h = plot_h * (value / vmax) * p
            colour = COLORS["accent"] if i == len(self.data) - 1 else light
            self.create_rectangle(x0, top + plot_h - bar_h, x1, top + plot_h,
                                  fill=colour, outline="")
            if p > 0.98 and value > 0:
                self.create_text((x0 + x1) / 2, top + plot_h - bar_h - 9,
                                 text=short_money(value), fill=COLORS["text"],
                                 font=(FONT, 8, "bold"))
            self.create_text((x0 + x1) / 2, h - 12, text=label,
                             fill=COLORS["muted"], font=(FONT, 9))


class HBarChart(AnimatedCanvas):
    """Horizontal bars, e.g. best-selling dishes."""

    def __init__(self, parent, data, title="", height=200):
        self.data = data
        super().__init__(parent, title, height)

    def draw(self, w, h, p):
        if not self.data:
            self.empty_message(w, h, "No sales yet")
            return
        top = 36
        row_h = (h - top - 6) / len(self.data)
        label_w, value_w = 135, 40
        bar_max = max(w - label_w - value_w - 10, 20)
        vmax = max(v for _, v in self.data) or 1
        palette = [COLORS["accent"], blend(COLORS["accent"], "#FFFFFF", 0.25),
                   blend(COLORS["accent"], "#FFFFFF", 0.45),
                   blend(COLORS["accent"], "#FFFFFF", 0.6),
                   blend(COLORS["accent"], "#FFFFFF", 0.7)]
        for i, (label, value) in enumerate(self.data):
            cy = top + row_h * i + row_h / 2
            name = label if len(label) <= 18 else label[:17] + "…"
            self.create_text(2, cy, anchor="w", text=name,
                             fill=COLORS["text"], font=(FONT, 9))
            length = bar_max * (value / vmax) * p
            self.create_rectangle(label_w, cy - 7, label_w + length, cy + 7,
                                  fill=palette[min(i, 4)], outline="")
            self.create_text(label_w + length + 6, cy, anchor="w",
                             text=str(int(value)), fill=COLORS["muted"],
                             font=(FONT, 9, "bold"))


class Donut(AnimatedCanvas):
    """Donut chart with a legend. data = [(label, value, colour), ...]."""

    def __init__(self, parent, data, title="", centre_text="", height=150):
        self.data = [d for d in data if d[1] > 0]
        self.centre_text = centre_text
        super().__init__(parent, title, height)

    def draw(self, w, h, p):
        total = sum(v for _, v, _ in self.data)
        if total <= 0:
            self.empty_message(w, h, "No payments yet")
            return
        size = min(h - 40, 110)
        cx, cy = 14 + size / 2, 32 + size / 2
        box = (cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2)

        start = 90.0
        for label, value, colour in self.data:
            extent = -min(360.0 * value / total * p, 359.99)
            if extent:
                self.create_arc(*box, start=start, extent=extent,
                                style="pieslice", fill=colour,
                                outline=COLORS["card"], width=2)
            start += extent
        hole = size * 0.30
        self.create_oval(cx - hole, cy - hole, cx + hole, cy + hole,
                         fill=COLORS["card"], outline="")
        self.create_text(cx, cy, text=self.centre_text, fill=COLORS["text"],
                         font=(FONT, 9, "bold"))

        y = 44
        for label, value, colour in self.data:
            self.create_rectangle(cx + size / 2 + 22, y, cx + size / 2 + 34,
                                  y + 12, fill=colour, outline="")
            self.create_text(cx + size / 2 + 42, y + 6, anchor="w",
                             fill=COLORS["text"], font=(FONT, 9),
                             text=f"{label}  {value / total * 100:.0f}%")
            y += 24
