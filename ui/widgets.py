"""Small reusable UI helpers so every screen looks the same."""
import tkinter as tk
from tkinter import ttk

from config import COLORS, FONT

_BUTTONS = {
    "primary": (COLORS["accent"], "#C74A08", "white"),
    "dark": (COLORS["primary"], "#2B3A5E", "white"),
    "success": (COLORS["success"], "#237A36", "white"),
    "danger": (COLORS["danger"], "#B52626", "white"),
    "light": ("#E5E7EB", "#D1D5DB", COLORS["text"]),
}


def button(parent, text, command, kind="primary", **kwargs):
    bg, active, fg = _BUTTONS[kind]
    return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                     activebackground=active, activeforeground=fg,
                     relief="flat", cursor="hand2", font=(FONT, 10, "bold"),
                     padx=12, pady=6, **kwargs)


def make_tree(parent, columns):
    """columns = [(key, heading, width, anchor), ...]. Returns the Treeview."""
    wrap = tk.Frame(parent, bg=COLORS["card"])
    wrap.pack(fill="both", expand=True)
    tree = ttk.Treeview(wrap, columns=[c[0] for c in columns],
                        show="headings", selectmode="browse")
    for key, heading, width, anchor in columns:
        tree.heading(key, text=heading)
        tree.column(key, width=width, anchor=anchor)
    scroll = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)
    return tree


def apply_styles(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Treeview", rowheight=30, font=(FONT, 10),
                    background=COLORS["card"], fieldbackground=COLORS["card"],
                    foreground=COLORS["text"], borderwidth=0)
    style.configure("Treeview.Heading", font=(FONT, 10, "bold"),
                    background=COLORS["primary"], foreground="white",
                    relief="flat", padding=6)
    style.map("Treeview.Heading",
              background=[("active", COLORS["primary"])])
    style.map("Treeview",
              background=[("selected", COLORS["accent"])],
              foreground=[("selected", "white")])
