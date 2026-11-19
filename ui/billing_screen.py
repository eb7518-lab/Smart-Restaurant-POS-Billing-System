"""Billing & payment screen: discount, payment mode, change, confirm."""
import tkinter as tk
from tkinter import messagebox

from config import COLORS, FONT, GST_RATE
from database import queries
from services import billing
from ui.receipt_window import show_receipt
from ui.widgets import button, make_tree

MODES = ["Cash", "Card", "UPI"]


class BillingScreen(tk.Frame):
    def __init__(self, parent, dashboard, order_id, table_id):
        super().__init__(parent, bg=COLORS["bg"])
        self.dashboard = dashboard
        self.order_id = order_id
        self.table_id = table_id
        self.table = queries.get_table(table_id)
        self.items = queries.get_order_items(order_id)
        self.lines = [(i["quantity"], i["price"]) for i in self.items]
        self.subtotal = round(sum(q * p for q, p in self.lines), 2)
        self.bill = None
        self.payable = 0.0
        self.mode_buttons = {}

        queries.set_table_status(table_id, "billing")

        self.discount_var = tk.StringVar(value="0")
        self.discount_mode = tk.StringVar(value="percent")
        self.mode_var = tk.StringVar(value="Cash")
        self.received_var = tk.StringVar()

        self.build()
        for var in (self.discount_var, self.discount_mode, self.received_var):
            var.trace_add("write", lambda *a: self.recompute())
        self.set_mode("Cash")
        self.recompute()

    # ------------------------------------------------------------ layout
    def build(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 12))
        button(header, "←  Back to order", self.go_back, "light"
               ).pack(side="left")
        tk.Label(header, text=f"Billing   •   Table {self.table['table_no']}",
                 font=(FONT, 14, "bold"), bg=COLORS["bg"], fg=COLORS["text"]
                 ).pack(side="left", padx=15)

        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # ---- left: bill summary
        left = tk.Frame(body, bg=COLORS["card"], padx=15, pady=15)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        tk.Label(left, text="Bill summary", font=(FONT, 13, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w",
                                                            pady=(0, 8))
        totals = tk.Frame(left, bg=COLORS["card"])
        totals.pack(side="bottom", fill="x", pady=(10, 0))
        totals.columnconfigure(1, weight=1)
        self.sub_var = tk.StringVar()
        self.disc_var = tk.StringVar()
        self.gst_var = tk.StringVar()
        self.round_var = tk.StringVar()
        self.pay_var = tk.StringVar()
        rows = [("Subtotal", self.sub_var, False),
                ("Discount", self.disc_var, False),
                (f"GST ({GST_RATE * 100:g}%)", self.gst_var, False),
                ("Round off", self.round_var, False),
                ("Payable", self.pay_var, True)]
        for i, (label, var, big) in enumerate(rows):
            size, weight = (16, "bold") if big else (10, "normal")
            colour = COLORS["accent"] if big else COLORS["text"]
            tk.Label(totals, text=label, font=(FONT, size, weight),
                     bg=COLORS["card"], fg=COLORS["text"]
                     ).grid(row=i, column=0, sticky="w", pady=2)
            tk.Label(totals, textvariable=var, font=(FONT, size, weight),
                     bg=COLORS["card"], fg=colour
                     ).grid(row=i, column=1, sticky="e", pady=2)

        tree = make_tree(left, [("name", "Item", 170, "w"),
                                ("qty", "Qty", 45, "center"),
                                ("amount", "Amount", 90, "e")])
        for it in self.items:
            tree.insert("", "end", values=(
                it["name"], it["quantity"],
                f"₹ {it['quantity'] * it['price']:.2f}"))

        # ---- right: payment
        right = tk.Frame(body, bg=COLORS["card"], padx=20, pady=15)
        right.grid(row=0, column=1, sticky="nsew")

        confirm = button(right, "CONFIRM PAYMENT", self.confirm, "success")
        confirm.config(font=(FONT, 13, "bold"), pady=12)
        confirm.pack(side="bottom", fill="x", pady=(12, 0))

        tk.Label(right, text="Discount", font=(FONT, 11, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
        drow = tk.Frame(right, bg=COLORS["card"])
        drow.pack(fill="x", pady=(6, 0))
        tk.Entry(drow, textvariable=self.discount_var, width=8,
                 font=(FONT, 12), relief="solid", bd=1
                 ).pack(side="left", ipady=3)
        for text, value in (("%", "percent"), ("₹", "amount")):
            tk.Radiobutton(drow, text=text, variable=self.discount_mode,
                           value=value, bg=COLORS["card"],
                           activebackground=COLORS["card"], font=(FONT, 11)
                           ).pack(side="left", padx=(10, 0))
        for pct in (5, 10, 15):
            tk.Button(drow, text=f"{pct}%", font=(FONT, 9, "bold"),
                      relief="flat", bg="#FFF4E6", fg=COLORS["accent"],
                      cursor="hand2", padx=8,
                      command=lambda p=pct: self.quick_discount(p)
                      ).pack(side="right", padx=(6, 0))
        self.discount_error = tk.Label(right, text="", font=(FONT, 9),
                                       bg=COLORS["card"], fg=COLORS["danger"])
        self.discount_error.pack(anchor="w")

        tk.Label(right, text="Payment method", font=(FONT, 11, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]
                 ).pack(anchor="w", pady=(12, 6))
        mrow = tk.Frame(right, bg=COLORS["card"])
        mrow.pack(fill="x")
        for mode in MODES:
            b = tk.Button(mrow, text=mode, font=(FONT, 12, "bold"),
                          relief="flat", cursor="hand2", pady=10,
                          command=lambda m=mode: self.set_mode(m))
            b.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.mode_buttons[mode] = b

        self.pay_area = tk.Frame(right, bg=COLORS["card"])
        self.pay_area.pack(fill="x", pady=(14, 0))

        # cash widgets
        self.cash_frame = tk.Frame(self.pay_area, bg=COLORS["card"])
        tk.Label(self.cash_frame, text="Amount received",
                 font=(FONT, 10), bg=COLORS["card"], fg=COLORS["muted"]
                 ).pack(anchor="w")
        crow = tk.Frame(self.cash_frame, bg=COLORS["card"])
        crow.pack(fill="x", pady=(4, 0))
        tk.Entry(crow, textvariable=self.received_var, width=10,
                 font=(FONT, 14), relief="solid", bd=1
                 ).pack(side="left", ipady=4)
        button(crow, "Exact", self.exact_cash, "light"
               ).pack(side="left", padx=(10, 4))
        for amount in (500, 1000, 2000):
            button(crow, str(amount),
                   lambda a=amount: self.received_var.set(str(a)), "light"
                   ).pack(side="left", padx=4)
        self.change_label = tk.Label(self.cash_frame, text="",
                                     font=(FONT, 14, "bold"),
                                     bg=COLORS["card"], fg=COLORS["muted"])
        self.change_label.pack(anchor="w", pady=(12, 0))

        # card / UPI widgets
        self.digital_frame = tk.Frame(self.pay_area, bg=COLORS["card"])
        self.digital_label = tk.Label(self.digital_frame, text="",
                                      font=(FONT, 13), bg=COLORS["card"],
                                      fg=COLORS["text"], justify="left",
                                      wraplength=420)
        self.digital_label.pack(anchor="w")

    # ------------------------------------------------------------ logic
    def quick_discount(self, pct):
        self.discount_mode.set("percent")
        self.discount_var.set(str(pct))

    def exact_cash(self):
        self.received_var.set(f"{self.payable:.0f}")

    def set_mode(self, mode):
        self.mode_var.set(mode)
        for m, b in self.mode_buttons.items():
            if m == mode:
                b.config(bg=COLORS["primary"], fg="white")
            else:
                b.config(bg="#E5E7EB", fg=COLORS["text"])
        self.cash_frame.pack_forget()
        self.digital_frame.pack_forget()
        if mode == "Cash":
            self.cash_frame.pack(fill="x")
        else:
            self.digital_frame.pack(fill="x")
        self.recompute()

    def parse_discount(self):
        """Return (discount_amount, error_message_or_None)."""
        raw = self.discount_var.get().strip() or "0"
        try:
            value = float(raw)
        except ValueError:
            return 0.0, "Discount must be a number."
        if value < 0:
            return 0.0, "Discount cannot be negative."
        if self.discount_mode.get() == "percent":
            if value > 100:
                return 0.0, "Discount cannot be more than 100%."
            return round(self.subtotal * value / 100, 2), None
        if value > self.subtotal:
            return 0.0, "Discount cannot be more than the bill amount."
        return value, None

    def recompute(self):
        discount, error = self.parse_discount()
        self.discount_error.config(text=error or "")
        self.bill = billing.calculate_bill(self.lines, discount=discount)
        self.payable, round_off = billing.round_total(self.bill["total"])

        self.sub_var.set(f"₹ {self.bill['subtotal']:,.2f}")
        self.disc_var.set(f"- ₹ {self.bill['discount']:,.2f}")
        self.gst_var.set(f"₹ {self.bill['gst']:,.2f}")
        self.round_var.set(f"{round_off:+.2f}")
        self.pay_var.set(f"₹ {self.payable:,.0f}")

        mode = self.mode_var.get()
        if mode == "Cash":
            try:
                received = float(self.received_var.get() or 0)
            except ValueError:
                self.change_label.config(text="Enter a valid amount",
                                         fg=COLORS["danger"])
                return
            if received <= 0:
                self.change_label.config(text="", fg=COLORS["muted"])
            elif received < self.payable:
                self.change_label.config(
                    text=f"Short by ₹ {self.payable - received:,.2f}",
                    fg=COLORS["danger"])
            else:
                self.change_label.config(
                    text=f"Change to return:  ₹ {received - self.payable:,.2f}",
                    fg=COLORS["success"])
        else:
            self.digital_label.config(
                text=f"Collect ₹ {self.payable:,.0f} by {mode},\n"
                     f"then press Confirm Payment.")

    def confirm(self):
        discount, error = self.parse_discount()
        if error:
            messagebox.showwarning("Discount", error)
            return
        mode = self.mode_var.get()
        change = 0.0
        if mode == "Cash":
            try:
                received = float(self.received_var.get())
            except ValueError:
                messagebox.showwarning("Payment",
                                       "Enter the cash amount received.")
                return
            if received < self.payable:
                messagebox.showwarning(
                    "Payment", f"The guest still owes "
                               f"₹ {self.payable - received:,.2f}.")
                return
            change = round(received - self.payable, 2)

        root = self.winfo_toplevel()
        try:
            bill_id = queries.create_bill(
                self.order_id, self.bill["subtotal"], self.bill["gst"],
                self.bill["discount"], self.payable, mode)
        except ValueError as err:
            messagebox.showerror("Billing", str(err))
            self.dashboard.show_page("tables")
            return

        bill, items = queries.get_bill(bill_id)
        self.dashboard.show_page("tables")
        show_receipt(root, bill, items, change)

    def go_back(self):
        queries.set_table_status(self.table_id, "occupied")
        self.dashboard.open_order(self.table_id)
