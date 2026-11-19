"""Menu Manager (admin): add, edit, hide or delete dishes and categories."""
import tkinter as tk
from tkinter import ttk, messagebox

from config import COLORS, FONT, LOW_STOCK_LIMIT
from database import queries
from services import menu_service
from ui.widgets import button, make_tree

ALL = "All categories"


class MenuManager(tk.Frame):
    def __init__(self, parent, dashboard):
        super().__init__(parent, bg=COLORS["bg"])
        self.dashboard = dashboard
        self.rows = {}
        self.selected_id = None
        self.cat_ids = {}

        self.filter_var = tk.StringVar(value=ALL)
        self.search_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.cat_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.stock_var = tk.StringVar(value="100")
        self.avail_var = tk.BooleanVar(value=True)

        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)
        self.build_list(body)
        self.build_form(body)

        self.load_categories()
        self.refresh_table()
        self.search_var.trace_add("write", lambda *a: self.refresh_table())
        self.filter_var.trace_add("write", lambda *a: self.refresh_table())

    # ------------------------------------------------------------ layout
    def build_list(self, body):
        left = tk.Frame(body, bg=COLORS["card"], padx=15, pady=15)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        top = tk.Frame(left, bg=COLORS["card"])
        top.pack(fill="x", pady=(0, 10))
        self.filter_box = ttk.Combobox(top, textvariable=self.filter_var,
                                       state="readonly", width=18,
                                       font=(FONT, 10))
        self.filter_box.pack(side="left")
        tk.Label(top, text="Search:", font=(FONT, 10), bg=COLORS["card"],
                 fg=COLORS["text"]).pack(side="left", padx=(14, 6))
        ttk.Entry(top, textvariable=self.search_var, font=(FONT, 10)
                  ).pack(side="left", fill="x", expand=True)

        self.tree = make_tree(left, [
            ("name", "Item", 190, "w"), ("category", "Category", 100, "w"),
            ("price", "Price", 70, "e"), ("stock", "Stock", 55, "center"),
            ("status", "Status", 70, "center")])
        self.tree.tag_configure("off", foreground="#9CA3AF")
        self.tree.tag_configure("low", foreground=COLORS["danger"])
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select())

    def build_form(self, body):
        right = tk.Frame(body, bg=COLORS["card"], padx=20, pady=15)
        right.grid(row=0, column=1, sticky="nsew")

        self.form_title = tk.Label(right, text="Add a new dish",
                                   font=(FONT, 13, "bold"),
                                   bg=COLORS["card"], fg=COLORS["text"])
        self.form_title.pack(anchor="w", pady=(0, 10))

        def field(label, widget):
            tk.Label(right, text=label, font=(FONT, 10, "bold"),
                     bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
            widget.pack(fill="x", pady=(2, 10), ipady=3)

        field("Name", ttk.Entry(right, textvariable=self.name_var,
                                font=(FONT, 11)))
        self.cat_box = ttk.Combobox(right, textvariable=self.cat_var,
                                    state="readonly", font=(FONT, 11))
        field("Category", self.cat_box)
        field("Price (₹)", ttk.Entry(right, textvariable=self.price_var,
                                     font=(FONT, 11)))
        field("Stock (portions available)",
              ttk.Entry(right, textvariable=self.stock_var, font=(FONT, 11)))
        tk.Checkbutton(right, text="Available on the menu",
                       variable=self.avail_var, bg=COLORS["card"],
                       activebackground=COLORS["card"], font=(FONT, 10)
                       ).pack(anchor="w")

        row1 = tk.Frame(right, bg=COLORS["card"])
        row1.pack(fill="x", pady=(16, 6))
        button(row1, "Add as new", self.add_new, "success"
               ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        button(row1, "Save changes", self.save_changes, "primary"
               ).pack(side="left", fill="x", expand=True, padx=(4, 0))
        row2 = tk.Frame(right, bg=COLORS["card"])
        row2.pack(fill="x")
        button(row2, "Delete", self.delete_item, "danger"
               ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        button(row2, "Clear form", self.clear_form, "light"
               ).pack(side="left", fill="x", expand=True, padx=(4, 0))
        button(right, "Manage categories", self.open_categories, "dark"
               ).pack(fill="x", pady=(16, 0))

    # -------------------------------------------------------------- data
    def load_categories(self):
        cats = queries.get_categories()
        self.cat_ids = {c["name"]: c["id"] for c in cats}
        names = list(self.cat_ids)
        self.filter_box.config(values=[ALL] + names)
        self.cat_box.config(values=names)
        if self.filter_var.get() not in [ALL] + names:
            self.filter_var.set(ALL)
        if self.cat_var.get() not in names:
            self.cat_var.set(names[0] if names else "")

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        cat = self.cat_ids.get(self.filter_var.get())
        self.rows = {}
        for r in queries.get_menu_admin(cat, self.search_var.get().strip()):
            self.rows[str(r["id"])] = r
            tags = ()
            if not r["available"]:
                tags = ("off",)
            elif r["stock"] <= LOW_STOCK_LIMIT:
                tags = ("low",)
            self.tree.insert("", "end", iid=str(r["id"]), tags=tags, values=(
                r["name"], r["category"], f"₹ {r['price']:.2f}", r["stock"],
                "Hidden" if not r["available"] else "Active"))

    def on_select(self):
        sel = self.tree.selection()
        if not sel or sel[0] not in self.rows:
            return
        r = self.rows[sel[0]]
        self.selected_id = r["id"]
        self.form_title.config(text=f"Edit: {r['name']}")
        self.name_var.set(r["name"])
        self.cat_var.set(r["category"])
        self.price_var.set(f"{r['price']:g}")
        self.stock_var.set(str(r["stock"]))
        self.avail_var.set(bool(r["available"]))

    def clear_form(self):
        self.selected_id = None
        self.form_title.config(text="Add a new dish")
        self.name_var.set("")
        self.price_var.set("")
        self.stock_var.set("100")
        self.avail_var.set(True)

    # ----------------------------------------------------------- actions
    def _save(self, item_id):
        ok, message = menu_service.save_item(
            item_id, self.name_var.get(), self.cat_ids.get(self.cat_var.get()),
            self.price_var.get(), self.stock_var.get(), self.avail_var.get())
        if not ok:
            messagebox.showwarning("Menu", message)
            return
        self.refresh_table()
        if item_id is None:
            self.clear_form()
        messagebox.showinfo("Menu", message)

    def add_new(self):
        self._save(None)

    def save_changes(self):
        if self.selected_id is None:
            messagebox.showwarning("Menu", "Select an item in the list first.")
            return
        self._save(self.selected_id)

    def delete_item(self):
        if self.selected_id is None:
            messagebox.showwarning("Menu", "Select an item in the list first.")
            return
        name = self.name_var.get()
        if not messagebox.askyesno("Delete item", f"Delete '{name}'?"):
            return
        result = queries.delete_menu_item(self.selected_id)
        self.clear_form()
        self.refresh_table()
        if result == "hidden":
            messagebox.showinfo(
                "Menu", f"'{name}' appears on past bills, so it was hidden "
                        f"from the menu instead of deleted.")

    def open_categories(self):
        CategoryDialog(self, self.on_categories_changed)

    def on_categories_changed(self):
        self.load_categories()
        self.refresh_table()


class CategoryDialog(tk.Toplevel):
    """Small window to add, rename and delete categories."""

    def __init__(self, parent, on_change):
        super().__init__(parent)
        self.on_change = on_change
        self.ids = {}
        self.title("Manage categories")
        self.configure(bg=COLORS["card"], padx=20, pady=18)
        self.resizable(False, False)

        self.name_var = tk.StringVar()
        self.tree = make_tree(self, [("name", "Category", 260, "w"),
                                     ("count", "Items", 60, "center")])
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select())
        ttk.Entry(self, textvariable=self.name_var, font=(FONT, 11)
                  ).pack(fill="x", pady=(12, 8), ipady=3)
        row = tk.Frame(self, bg=COLORS["card"])
        row.pack(fill="x")
        button(row, "Add", self.add, "success").pack(side="left", padx=(0, 6))
        button(row, "Rename", self.rename, "primary").pack(side="left")
        button(row, "Delete", self.remove, "danger").pack(side="left", padx=6)
        button(row, "Close", self.destroy, "light").pack(side="right")
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.ids = {}
        for c in queries.get_categories():
            self.ids[str(c["id"])] = c["name"]
            self.tree.insert("", "end", iid=str(c["id"]), values=(
                c["name"], queries.count_items_in_category(c["id"])))

    def selected(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def on_select(self):
        cid = self.selected()
        if cid is not None:
            self.name_var.set(self.ids[str(cid)])

    def _done(self, ok, message):
        if ok:
            self.name_var.set("")
            self.refresh()
            self.on_change()
        else:
            messagebox.showwarning("Categories", message, parent=self)

    def add(self):
        self._done(*menu_service.save_category(None, self.name_var.get()))

    def rename(self):
        cid = self.selected()
        if cid is None:
            messagebox.showwarning("Categories", "Select a category first.",
                                   parent=self)
            return
        self._done(*menu_service.save_category(cid, self.name_var.get()))

    def remove(self):
        cid = self.selected()
        if cid is None:
            messagebox.showwarning("Categories", "Select a category first.",
                                   parent=self)
            return
        if messagebox.askyesno("Delete category", "Delete this category?",
                               parent=self):
            self._done(*menu_service.remove_category(cid))
