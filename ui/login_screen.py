"""Login screen: brand panel on the left, sign-in form on the right."""
import tkinter as tk
from tkinter import ttk

from config import COLORS, FONT, RESTAURANT_NAME, APP_NAME, TAGLINE
from services import auth
from ui.charts import draw_gradient, blend


class LoginScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["card"])
        self.app = app

        # ---- left: brand panel
        self.brand = tk.Canvas(self, highlightthickness=0,
                               bg=COLORS["primary"])
        self.brand.place(relx=0, rely=0, relwidth=0.5, relheight=1)
        self.brand.bind("<Configure>", self.draw_brand)

        # ---- right: form
        right = tk.Frame(self, bg=COLORS["card"])
        right.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
        form = tk.Frame(right, bg=COLORS["card"])
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(form, text="Welcome back", font=(FONT, 24, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
        tk.Label(form, text="Sign in to start taking orders",
                 font=(FONT, 11), bg=COLORS["card"], fg=COLORS["muted"]
                 ).pack(anchor="w", pady=(2, 24))

        tk.Label(form, text="Username", font=(FONT, 10, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
        self.username = ttk.Entry(form, width=34, font=(FONT, 12))
        self.username.pack(pady=(3, 14), ipady=5)

        tk.Label(form, text="Password", font=(FONT, 10, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
        self.password = ttk.Entry(form, width=34, font=(FONT, 12), show="•")
        self.password.pack(pady=(3, 6), ipady=5)

        self.show_var = tk.BooleanVar(value=False)
        tk.Checkbutton(form, text="Show password", variable=self.show_var,
                       command=self.toggle_password, bg=COLORS["card"],
                       activebackground=COLORS["card"], font=(FONT, 9),
                       fg=COLORS["muted"]).pack(anchor="w")

        self.error_label = tk.Label(form, text="", font=(FONT, 10),
                                    bg=COLORS["card"], fg=COLORS["danger"])
        self.error_label.pack(pady=(10, 0))

        tk.Button(form, text="SIGN IN", font=(FONT, 12, "bold"),
                  bg=COLORS["accent"], fg="white", activebackground="#C74A08",
                  activeforeground="white", relief="flat", cursor="hand2",
                  command=self.do_login).pack(fill="x", pady=(8, 0), ipady=8)

        tk.Label(form, text="Demo logins:  admin / admin123   •   "
                            "cashier / cash123",
                 font=(FONT, 9), bg=COLORS["card"], fg=COLORS["muted"]
                 ).pack(pady=(22, 0))

        self.username.bind("<Return>", lambda e: self.password.focus())
        self.password.bind("<Return>", lambda e: self.do_login())

    def draw_brand(self, event=None):
        c = self.brand
        c.delete("all")
        w = c.winfo_width() or 550
        h = c.winfo_height() or 650
        draw_gradient(c, w, h, COLORS["primary"], "#8A3A12")

        # soft decorative circles
        for cx, cy, r, t in [(w * 0.9, h * 0.1, 160, 0.10),
                             (w * 0.1, h * 0.95, 210, 0.08),
                             (w * 0.85, h * 0.8, 90, 0.12)]:
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="",
                          fill=blend("#2B3A5E", "#E8590C", t * 4))

        c.create_text(w / 2, h * 0.30, text=RESTAURANT_NAME, fill="white",
                      font=(FONT, 34, "bold"))
        c.create_text(w / 2, h * 0.30 + 46, text=TAGLINE.upper(),
                      fill="#FFD8A8", font=(FONT, 10, "bold"))
        c.create_line(w / 2 - 40, h * 0.30 + 72, w / 2 + 40, h * 0.30 + 72,
                      fill=COLORS["accent"], width=3)
        for i, line in enumerate(["Table-wise ordering & kitchen tickets",
                                  "Instant billing with printable invoices",
                                  "Live sales charts & smart suggestions"]):
            c.create_text(w / 2, h * 0.52 + i * 34, text="✓   " + line,
                          fill="white", font=(FONT, 11))
        c.create_text(w / 2, h - 28, text=APP_NAME, fill="#CBD5E1",
                      font=(FONT, 9))

    def on_show(self):
        """Called by the app every time this screen is displayed."""
        self.username.delete(0, "end")
        self.password.delete(0, "end")
        self.error_label.config(text="")
        self.show_var.set(False)
        self.toggle_password()
        self.username.focus()

    def toggle_password(self):
        self.password.config(show="" if self.show_var.get() else "•")

    def do_login(self):
        ok, message = auth.login(self.username.get(), self.password.get())
        if ok:
            self.app.show("dashboard")
        else:
            self.error_label.config(text=message)
            self.password.delete(0, "end")
