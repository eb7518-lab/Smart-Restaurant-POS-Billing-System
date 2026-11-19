"""Smart Restaurant POS & Billing System - entry point.

Run with:  python main.py
"""
import tkinter as tk
from tkinter import messagebox

from config import APP_NAME, COLORS
from database.db import init_db
from ui.login_screen import LoginScreen
from ui.dashboard import Dashboard
from ui.widgets import apply_styles


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1200x720")
        self.minsize(1050, 680)
        self.configure(bg=COLORS["bg"])
        apply_styles(self)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.screens = {
            "login": LoginScreen(container, self),
            "dashboard": Dashboard(container, self),
        }
        for screen in self.screens.values():
            screen.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show("login")

    def show(self, name):
        screen = self.screens[name]
        screen.tkraise()
        if hasattr(screen, "on_show"):
            screen.on_show()


def start():
    try:
        init_db()
    except Exception as err:          # MySQL stopped, wrong password, etc.
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Cannot connect to MySQL",
            "The app could not open its MySQL database.\n\n"
            "1. Make sure MySQL is running.\n"
            "2. Check the MYSQL_ settings in config.py (user, password).\n"
            "3. Install the connector:  pip install mysql-connector-python\n\n"
            f"Details: {err}")
        return
    App().mainloop()


if __name__ == "__main__":
    start()
