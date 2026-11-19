"""List of all currently open orders."""
import tkinter as tk
from tkinter import messagebox

from config import COLORS, FONT
from database import queries
from ui.widgets import button, make_tree


class OrdersList(tk.Frame):
    def __init__(self, parent, dashboard):
        super().__init__(parent, bg=COLORS["bg"])
        self.dashboard = dashboard

        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", pady=(0, 12))
        tk.Label(top, text="Double-click an order to open it.",
                 font=(FONT, 10), bg=COLORS["bg"], fg=COLORS["muted"]
                 ).pack(side="left")
        button(top, "Refresh", self.refresh, "light").pack(side="right")

        card = tk.Frame(self, bg=COLORS["card"], padx=10, pady=10)
        card.pack(fill="both", expand=True)
        self.tree = make_tree(card, [
            ("order", "Order #", 80, "center"),
            ("table", "Table", 80, "center"),
            ("staff", "Taken by", 160, "w"),
            ("started", "Started", 170, "w"),
            ("items", "Items", 80, "center"),
            ("amount", "Amount", 120, "e"),
        ])
        self.tree.bind("<Double-1>", lambda e: self.open_selected())
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.table_of = {}
        for o in queries.get_open_orders():
            self.table_of[str(o["id"])] = o["table_id"]
            self.tree.insert("", "end", iid=str(o["id"]), values=(
                f"#{o['id']}", o["table_no"], o["full_name"], o["created_at"],
                o["items"], f"₹ {o['amount']:,.2f}"))

    def open_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Orders", "Select an order first.")
            return
        self.dashboard.open_order(self.table_of[sel[0]])
