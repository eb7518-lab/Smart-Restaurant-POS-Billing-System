"""Grid of tables, coloured by status, with a live "time seated" timer."""
import tkinter as tk
from datetime import datetime

from config import COLORS, FONT
from database import queries
from ui.widgets import button

STATUS_COLOURS = {"free": COLORS["success"],
                  "occupied": COLORS["accent"],
                  "billing": COLORS["primary"]}
COLUMNS = 4
AUTO_REFRESH_MS = 30_000


def elapsed(created_at):
    """'23 min' or '1h 05m' since the order started."""
    try:
        started = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return ""
    mins = max(int((datetime.now() - started).total_seconds() // 60), 0)
    return f"{mins} min" if mins < 60 else f"{mins // 60}h {mins % 60:02d}m"


class TablesScreen(tk.Frame):
    def __init__(self, parent, dashboard):
        super().__init__(parent, bg=COLORS["bg"])
        self.dashboard = dashboard

        legend = tk.Frame(self, bg=COLORS["bg"])
        legend.pack(fill="x", pady=(0, 15))
        for text, key in [("Free", "free"), ("Occupied", "occupied"),
                          ("Billing", "billing")]:
            tk.Label(legend, text="    ", bg=STATUS_COLOURS[key]
                     ).pack(side="left")
            tk.Label(legend, text=text, font=(FONT, 10), bg=COLORS["bg"],
                     fg=COLORS["text"]).pack(side="left", padx=(6, 20))
        button(legend, "Refresh", self.refresh, "light").pack(side="right")
        tk.Label(legend, text="Updates every 30 seconds", font=(FONT, 9),
                 bg=COLORS["bg"], fg=COLORS["muted"]
                 ).pack(side="right", padx=12)

        self.grid_frame = tk.Frame(self, bg=COLORS["bg"])
        self.grid_frame.pack(fill="both", expand=True)
        self.refresh()
        self.after(AUTO_REFRESH_MS, self.auto_refresh)

    def auto_refresh(self):
        try:
            self.refresh()
            self.after(AUTO_REFRESH_MS, self.auto_refresh)
        except tk.TclError:          # screen was closed
            pass

    def refresh(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        for i, t in enumerate(queries.get_tables()):
            r, c = divmod(i, COLUMNS)
            colour = STATUS_COLOURS.get(t["status"], COLORS["muted"])
            card = tk.Frame(self.grid_frame, bg=colour, cursor="hand2")
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            self.grid_frame.columnconfigure(c, weight=1, uniform="col")
            self.grid_frame.rowconfigure(r, weight=1, uniform="row")

            labels = [
                tk.Label(card, text=f"Table {t['table_no']}",
                         font=(FONT, 16, "bold"), bg=colour, fg="white"),
                tk.Label(card, text=f"{t['capacity']} seats",
                         font=(FONT, 10), bg=colour, fg="white"),
            ]
            if t["status"] == "free":
                labels.append(tk.Label(card, text="Available",
                                       font=(FONT, 11, "bold"),
                                       bg=colour, fg="white"))
            else:
                labels.append(tk.Label(card, text=f"₹ {t['amount']:,.2f}",
                                       font=(FONT, 11, "bold"),
                                       bg=colour, fg="white"))
                labels.append(tk.Label(card, text=elapsed(t["created_at"]),
                                       font=(FONT, 9), bg=colour,
                                       fg="#FFE8CC"))
            for lbl in labels:
                lbl.pack(pady=2, expand=True)

            for widget in [card] + labels:
                widget.bind("<Button-1>",
                            lambda e, tid=t["id"]: self.dashboard.open_order(tid))
