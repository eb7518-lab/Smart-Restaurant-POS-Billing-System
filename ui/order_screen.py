"""Order screen: pick items from the menu, build the order for one table."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from config import (COLORS, FONT, GST_RATE, SERVICE_CHARGE_RATE,
                    LOW_STOCK_LIMIT)
from database import queries
from services import billing
from services.auth import Session
from ui.widgets import button, make_tree


class OrderScreen(tk.Frame):
    def __init__(self, parent, dashboard, table_id):
        super().__init__(parent, bg=COLORS["bg"])
        self.dashboard = dashboard
        order = queries.get_open_order(table_id)
        status = queries.get_table(table_id)["status"]
        if order and status == "billing":          # came back from billing
            queries.set_table_status(table_id, "occupied")
        elif not order and status != "free":       # stale status, nothing open
            queries.set_table_status(table_id, "free")
        self.table = queries.get_table(table_id)
        self.order_id = order["id"] if order else None
        self.category_id = None          # None = "All"
        self.cat_buttons = {}

        self.build_header()
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)
        self.build_menu_panel(body)
        self.build_order_panel(body)

        self.highlight_category()
        self.load_menu()
        self.load_order()

    # ------------------------------------------------------------ layout
    def build_header(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 12))
        button(header, "←  Tables", self.go_back, "light").pack(side="left")
        tk.Label(header,
                 text=f"Table {self.table['table_no']}   •   "
                      f"{self.table['capacity']} seats",
                 font=(FONT, 14, "bold"), bg=COLORS["bg"], fg=COLORS["text"]
                 ).pack(side="left", padx=15)
        self.order_label = tk.Label(header, text="", font=(FONT, 10),
                                    bg=COLORS["bg"], fg=COLORS["muted"])
        self.order_label.pack(side="right")

    def build_menu_panel(self, body):
        left = tk.Frame(body, bg=COLORS["card"], padx=15, pady=15)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        # search
        search_row = tk.Frame(left, bg=COLORS["card"])
        search_row.pack(fill="x")
        tk.Label(search_row, text="Search:", font=(FONT, 10),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.load_menu())
        ttk.Entry(search_row, textvariable=self.search_var, font=(FONT, 10)
                  ).pack(side="left", fill="x", expand=True, padx=(8, 0))

        # categories
        cat_row = tk.Frame(left, bg=COLORS["card"])
        cat_row.pack(fill="x", pady=10)
        self.add_category_button(cat_row, None, "All")
        for c in queries.get_categories():
            self.add_category_button(cat_row, c["id"], c["name"])

        # quantity + add (packed at the bottom first so it never disappears)
        bottom = tk.Frame(left, bg=COLORS["card"])
        bottom.pack(side="bottom", fill="x", pady=(10, 0))
        tk.Label(bottom, text="Qty:", font=(FONT, 10), bg=COLORS["card"],
                 fg=COLORS["text"]).pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        ttk.Spinbox(bottom, from_=1, to=50, width=5, textvariable=self.qty_var,
                    font=(FONT, 11)).pack(side="left", padx=8)
        button(bottom, "Add to Order  ➜", self.add_selected, "primary"
               ).pack(side="right")

        self.menu_tree = make_tree(left, [
            ("name", "Item", 200, "w"),
            ("category", "Category", 100, "w"),
            ("price", "Price", 70, "e"),
            ("stock", "Left", 50, "center"),
        ])
        self.menu_tree.tag_configure("low", foreground=COLORS["danger"])
        self.menu_tree.bind("<Double-1>", lambda e: self.add_selected())

    def build_order_panel(self, body):
        right = tk.Frame(body, bg=COLORS["card"], padx=15, pady=15)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(right, text="Current Order", font=(FONT, 13, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w",
                                                            pady=(0, 8))

        # bottom parts are packed first (lowest one first)
        actions = tk.Frame(right, bg=COLORS["card"])
        actions.pack(side="bottom", fill="x", pady=(10, 0))
        button(actions, "Send to Kitchen (KOT)", self.send_to_kitchen, "dark"
               ).pack(fill="x", pady=(0, 6))
        row = tk.Frame(actions, bg=COLORS["card"])
        row.pack(fill="x")
        button(row, "Generate Bill", self.generate_bill, "success"
               ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        button(row, "Cancel Order", self.cancel_order, "danger"
               ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        totals = tk.Frame(right, bg=COLORS["card"])
        totals.pack(side="bottom", fill="x", pady=(10, 0))
        totals.columnconfigure(1, weight=1)
        self.subtotal_var = tk.StringVar()
        self.service_var = tk.StringVar()
        self.gst_var = tk.StringVar()
        self.total_var = tk.StringVar()
        rows = [("Subtotal", self.subtotal_var, False)]
        if SERVICE_CHARGE_RATE > 0:
            rows.append((f"Service ({SERVICE_CHARGE_RATE * 100:g}%)",
                         self.service_var, False))
        rows += [(f"GST ({GST_RATE * 100:g}%)", self.gst_var, False),
                 ("Total", self.total_var, True)]
        for i, (label, var, big) in enumerate(rows):
            size = 14 if big else 10
            colour = COLORS["accent"] if big else COLORS["text"]
            weight = "bold" if big else "normal"
            tk.Label(totals, text=label, font=(FONT, size, weight),
                     bg=COLORS["card"], fg=COLORS["text"]
                     ).grid(row=i, column=0, sticky="w", pady=2)
            tk.Label(totals, textvariable=var, font=(FONT, size, weight),
                     bg=COLORS["card"], fg=colour
                     ).grid(row=i, column=1, sticky="e", pady=2)

        self.sugg_frame = tk.Frame(right, bg=COLORS["card"])
        self.sugg_frame.pack(side="bottom", fill="x", pady=(8, 0))

        qty_row = tk.Frame(right, bg=COLORS["card"])
        qty_row.pack(side="bottom", fill="x", pady=(8, 0))
        button(qty_row, "  +  ", lambda: self.change_qty(1), "light"
               ).pack(side="left")
        button(qty_row, "  −  ", lambda: self.change_qty(-1), "light"
               ).pack(side="left", padx=6)
        button(qty_row, "Remove", self.remove_selected, "light"
               ).pack(side="left")

        self.order_tree = make_tree(right, [
            ("name", "Item", 150, "w"),
            ("qty", "Qty", 45, "center"),
            ("amount", "Amount", 80, "e"),
            ("kitchen", "Kitchen", 70, "center"),
        ])

    def add_category_button(self, parent, cat_id, name):
        btn = tk.Button(parent, text=name, font=(FONT, 9, "bold"),
                        relief="flat", cursor="hand2", padx=10, pady=4,
                        command=lambda: self.set_category(cat_id))
        btn.pack(side="left", padx=(0, 6))
        self.cat_buttons[cat_id] = btn

    # ------------------------------------------------------------- menu
    def set_category(self, cat_id):
        self.category_id = cat_id
        self.highlight_category()
        self.load_menu()

    def highlight_category(self):
        for cat_id, btn in self.cat_buttons.items():
            if cat_id == self.category_id:
                btn.config(bg=COLORS["primary"], fg="white")
            else:
                btn.config(bg="#E5E7EB", fg=COLORS["text"])

    def load_menu(self):
        self.menu_tree.delete(*self.menu_tree.get_children())
        for m in queries.search_menu(self.category_id,
                                     self.search_var.get().strip()):
            low = ("low",) if m["stock"] <= LOW_STOCK_LIMIT else ()
            self.menu_tree.insert("", "end", iid=str(m["id"]), tags=low,
                                  values=(m["name"], m["category"],
                                          f"₹ {m['price']:.2f}", m["stock"]))

    def add_selected(self):
        sel = self.menu_tree.selection()
        if not sel:
            messagebox.showwarning("Add item", "Select a menu item first.")
            return
        try:
            qty = int(self.qty_var.get())
        except ValueError:
            qty = 0
        if not 1 <= qty <= 50:
            messagebox.showwarning("Add item",
                                   "Quantity must be a whole number from 1 to 50.")
            return
        if self.add_item(int(sel[0]), qty):
            self.qty_var.set("1")

    def add_item(self, item_id, qty):
        """Add to the order (creating it on the first item). True if added."""
        stock = queries.get_stock(item_id)
        already = (queries.qty_in_order(self.order_id, item_id)
                   if self.order_id else 0)
        if already + qty > stock:
            messagebox.showwarning(
                "Not enough stock",
                f"Only {stock} left in stock"
                + (f" ({already} already on this order)." if already else "."))
            return False
        if self.order_id is None:        # first item creates the order
            self.order_id = queries.get_or_create_order(
                self.table["id"], Session.user["id"])
        queries.add_item(self.order_id, item_id, qty)
        self.load_order()
        return True

    # ------------------------------------------------------------ order
    def load_order(self):
        selected = self.order_tree.selection()
        self.order_tree.delete(*self.order_tree.get_children())
        items = queries.get_order_items(self.order_id) if self.order_id else []

        for it in items:
            if it["kot_qty"] >= it["quantity"]:
                kitchen = "✓ Sent"
            elif it["kot_qty"] == 0:
                kitchen = "New"
            else:
                kitchen = f"+{it['quantity'] - it['kot_qty']} new"
            self.order_tree.insert("", "end", iid=str(it["id"]), values=(
                it["name"], it["quantity"],
                f"₹ {it['quantity'] * it['price']:.2f}", kitchen))
        if selected and self.order_tree.exists(selected[0]):
            self.order_tree.selection_set(selected[0])

        bill = billing.calculate_bill(
            [(it["quantity"], it["price"]) for it in items])
        self.subtotal_var.set(f"₹ {bill['subtotal']:,.2f}")
        self.service_var.set(f"₹ {bill['service']:,.2f}")
        self.gst_var.set(f"₹ {bill['gst']:,.2f}")
        self.total_var.set(f"₹ {bill['total']:,.2f}")
        self.order_label.config(
            text=f"Order #{self.order_id}" if self.order_id else "New order")
        self.refresh_suggestions(items)

    def refresh_suggestions(self, items):
        """'Goes well with' chips learned from past bills."""
        for w in self.sugg_frame.winfo_children():
            w.destroy()
        if not items:
            return
        found = queries.suggestions([it["item_id"] for it in items], limit=2)
        if not found:
            return
        tk.Label(self.sugg_frame, text="Goes well with:", font=(FONT, 9),
                 bg=COLORS["card"], fg=COLORS["muted"]).pack(anchor="w")
        row = tk.Frame(self.sugg_frame, bg=COLORS["card"])
        row.pack(fill="x")
        for sug in found:
            name = sug["name"] if len(sug["name"]) <= 16 else sug["name"][:15] + "…"
            tk.Button(row, text=f"+ {name}  ₹{sug['price']:.0f}",
                      font=(FONT, 9, "bold"), bg="#FFF4E6",
                      fg=COLORS["accent"], activebackground="#FFE8CC",
                      relief="flat", cursor="hand2", padx=8, pady=3,
                      command=lambda i=sug["id"]: self.add_item(i, 1)
                      ).pack(side="left", padx=(0, 6), pady=3)

    def selected_order_item(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("Order", "Select an item in the order first.")
            return None
        return int(sel[0])

    def after_item_change(self):
        """If the last item was removed, cancel the empty order."""
        if self.order_id and queries.count_order_items(self.order_id) == 0:
            queries.cancel_order(self.order_id)
            self.order_id = None
        self.load_order()

    def change_qty(self, delta):
        item_id = self.selected_order_item()
        if item_id is None:
            return
        if not queries.change_quantity(item_id, delta):
            messagebox.showwarning("Not enough stock",
                                   "There is no more stock of this item.")
            return
        self.after_item_change()

    def remove_selected(self):
        item_id = self.selected_order_item()
        if item_id is None:
            return
        if messagebox.askyesno("Remove item", "Remove the selected item?"):
            queries.remove_item(item_id)
            self.after_item_change()

    def cancel_order(self):
        if self.order_id is None:
            messagebox.showinfo("Cancel order", "There is no active order.")
            return
        if messagebox.askyesno("Cancel order",
                               "Cancel this whole order and free the table?"):
            queries.cancel_order(self.order_id)
            self.order_id = None
            self.go_back()

    def generate_bill(self):
        if self.order_id is None:
            messagebox.showwarning("Bill", "Add items to the order first.")
            return
        self.dashboard.open_billing(self.order_id, self.table["id"])

    def go_back(self):
        self.dashboard.show_page("tables")

    # ---------------------------------------------------------- kitchen
    def send_to_kitchen(self):
        if self.order_id is None:
            messagebox.showwarning("Kitchen", "Add items to the order first.")
            return
        pending = queries.get_kot_items(self.order_id)
        if not pending:
            messagebox.showinfo("Kitchen", "Everything is already sent to "
                                           "the kitchen.")
            return

        width = 34
        lines = ["KITCHEN ORDER TICKET".center(width), "=" * width,
                 f"Table : {self.table['table_no']}",
                 f"Order : #{self.order_id}",
                 f"Time  : {datetime.now():%d-%b-%Y %I:%M %p}",
                 f"Staff : {Session.user['full_name']}", "-" * width]
        for p in pending:
            lines.append(f"{p['name'][:26]:<26}{'x' + str(p['pending']):>8}")
        lines.append("=" * width)

        win = tk.Toplevel(self)
        win.title("Kitchen Order Ticket")
        win.configure(bg=COLORS["card"])
        win.resizable(False, False)
        text = tk.Text(win, width=width + 2, height=len(lines) + 1,
                       font=("Consolas", 11), relief="flat", bg="#FFFBEB")
        text.insert("1.0", "\n".join(lines))
        text.config(state="disabled")
        text.pack(padx=20, pady=(20, 10))
        button(win, "Close", win.destroy, "dark").pack(pady=(0, 20))
        win.transient(self.winfo_toplevel())
        try:
            win.grab_set()
        except tk.TclError:
            pass

        queries.mark_kot_sent(self.order_id)
        self.load_order()
