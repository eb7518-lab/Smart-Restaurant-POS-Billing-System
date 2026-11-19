"""Staff screen (admin): create accounts, change roles, reset passwords."""
import tkinter as tk
from tkinter import ttk, messagebox

from config import COLORS, FONT
from database import queries
from services import staff_service
from services.auth import Session
from ui.widgets import button, make_tree


class StaffScreen(tk.Frame):
    def __init__(self, parent, dashboard):
        super().__init__(parent, bg=COLORS["bg"])
        self.dashboard = dashboard
        self.rows = {}
        self.selected_id = None

        self.username_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.role_var = tk.StringVar(value="cashier")
        self.password_var = tk.StringVar()
        self.active_var = tk.BooleanVar(value=True)

        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=COLORS["card"], padx=15, pady=15)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        tk.Label(left, text="Team", font=(FONT, 13, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w",
                                                            pady=(0, 8))
        self.tree = make_tree(left, [
            ("username", "Username", 120, "w"),
            ("name", "Full name", 170, "w"),
            ("role", "Role", 80, "center"),
            ("status", "Status", 80, "center")])
        self.tree.tag_configure("off", foreground="#9CA3AF")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select())

        self.build_form(body)
        self.refresh()

    def build_form(self, body):
        right = tk.Frame(body, bg=COLORS["card"], padx=20, pady=15)
        right.grid(row=0, column=1, sticky="nsew")
        self.form_title = tk.Label(right, text="Add a staff member",
                                   font=(FONT, 13, "bold"),
                                   bg=COLORS["card"], fg=COLORS["text"])
        self.form_title.pack(anchor="w", pady=(0, 10))

        def field(label, widget):
            tk.Label(right, text=label, font=(FONT, 10, "bold"),
                     bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
            widget.pack(fill="x", pady=(2, 10), ipady=3)

        self.username_entry = ttk.Entry(right, textvariable=self.username_var,
                                        font=(FONT, 11))
        field("Username", self.username_entry)
        field("Full name", ttk.Entry(right, textvariable=self.name_var,
                                     font=(FONT, 11)))
        field("Role", ttk.Combobox(right, textvariable=self.role_var,
                                   values=list(staff_service.ROLES),
                                   state="readonly", font=(FONT, 11)))
        field("Password (new account or reset)",
              ttk.Entry(right, textvariable=self.password_var, show="•",
                        font=(FONT, 11)))
        tk.Checkbutton(right, text="Account is active",
                       variable=self.active_var, bg=COLORS["card"],
                       activebackground=COLORS["card"], font=(FONT, 10)
                       ).pack(anchor="w")

        row1 = tk.Frame(right, bg=COLORS["card"])
        row1.pack(fill="x", pady=(16, 6))
        button(row1, "Add staff", self.add, "success"
               ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        button(row1, "Save changes", self.save, "primary"
               ).pack(side="left", fill="x", expand=True, padx=(4, 0))
        row2 = tk.Frame(right, bg=COLORS["card"])
        row2.pack(fill="x")
        button(row2, "Reset password", self.reset, "dark"
               ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        button(row2, "Clear form", self.clear_form, "light"
               ).pack(side="left", fill="x", expand=True, padx=(4, 0))

    # -------------------------------------------------------------- data
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.rows = {}
        for u in queries.get_users():
            self.rows[str(u["id"])] = u
            self.tree.insert("", "end", iid=str(u["id"]),
                             tags=() if u["active"] else ("off",),
                             values=(u["username"], u["full_name"],
                                     u["role"].title(),
                                     "Active" if u["active"] else "Disabled"))

    def on_select(self):
        sel = self.tree.selection()
        if not sel or sel[0] not in self.rows:
            return
        u = self.rows[sel[0]]
        self.selected_id = u["id"]
        self.form_title.config(text=f"Edit: {u['username']}")
        self.username_var.set(u["username"])
        self.username_entry.config(state="disabled")   # usernames never change
        self.name_var.set(u["full_name"])
        self.role_var.set(u["role"])
        self.active_var.set(bool(u["active"]))
        self.password_var.set("")

    def clear_form(self):
        self.selected_id = None
        self.form_title.config(text="Add a staff member")
        self.username_entry.config(state="normal")
        self.username_var.set("")
        self.name_var.set("")
        self.role_var.set("cashier")
        self.password_var.set("")
        self.active_var.set(True)

    # ----------------------------------------------------------- actions
    def add(self):
        if self.selected_id is not None:
            messagebox.showinfo("Staff", "Press 'Clear form' first to add a "
                                         "new person.")
            return
        ok, msg = staff_service.add_staff(
            self.username_var.get(), self.name_var.get(),
            self.password_var.get(), self.role_var.get())
        self._finish(ok, msg, clear=ok)

    def save(self):
        if self.selected_id is None:
            messagebox.showwarning("Staff", "Select a person in the list first.")
            return
        ok, msg = staff_service.update_staff(
            self.selected_id, self.name_var.get(), self.role_var.get(),
            self.active_var.get(), Session.user["id"])
        self._finish(ok, msg)

    def reset(self):
        if self.selected_id is None:
            messagebox.showwarning("Staff", "Select a person in the list first.")
            return
        ok, msg = staff_service.reset_password(self.selected_id,
                                               self.password_var.get())
        self._finish(ok, msg, clear_password=ok)

    def _finish(self, ok, msg, clear=False, clear_password=False):
        if not ok:
            messagebox.showwarning("Staff", msg)
            return
        self.refresh()
        if clear:
            self.clear_form()
        if clear_password:
            self.password_var.set("")
        messagebox.showinfo("Staff", msg)
