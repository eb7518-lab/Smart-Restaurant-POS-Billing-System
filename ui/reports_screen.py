"""Reports (admin): filter by date, see totals, charts, reprint, export CSV."""
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import ttk, messagebox, filedialog

from config import COLORS, FONT
from database import queries
from services import export
from ui.charts import BarChart, HBarChart
from ui.receipt_window import show_receipt
from ui.widgets import button, make_tree


class ReportsScreen(tk.Frame):
    def __init__(self, parent, dashboard):
        super().__init__(parent, bg=COLORS["bg"])
        self.dashboard = dashboard
        today = date.today()
        self.from_var = tk.StringVar(value=(today - timedelta(days=6)).isoformat())
        self.to_var = tk.StringVar(value=today.isoformat())
        self.mode_var = tk.StringVar(value="All")
        self.kpi_vars = {k: tk.StringVar(value="-") for k in
                         ("sales", "bills", "avg", "discount", "gst")}
        self.bills = []
        self.items = []

        self.build_filters()
        self.build_kpis()
        self.build_tabs()
        self.refresh()

    # ------------------------------------------------------------ layout
    def build_filters(self):
        bar = tk.Frame(self, bg=COLORS["card"], padx=14, pady=10)
        bar.pack(fill="x")

        presets = tk.Frame(bar, bg=COLORS["card"])
        presets.pack(fill="x")
        for text, days in (("Today", 0), ("Last 7 days", 6),
                           ("Last 30 days", 29), ("This month", "month"),
                           ("All time", "all")):
            button(presets, text, lambda d=days: self.preset(d), "light"
                   ).pack(side="left", padx=(0, 6))
        button(presets, "Export bills (CSV)", self.export_bills, "dark"
               ).pack(side="right")
        button(presets, "Export items (CSV)", self.export_items, "dark"
               ).pack(side="right", padx=6)

        row = tk.Frame(bar, bg=COLORS["card"])
        row.pack(fill="x", pady=(10, 0))
        for label, var in (("From", self.from_var), ("To", self.to_var)):
            tk.Label(row, text=label, font=(FONT, 10), bg=COLORS["card"],
                     fg=COLORS["text"]).pack(side="left")
            tk.Entry(row, textvariable=var, width=12, font=(FONT, 10),
                     relief="solid", bd=1).pack(side="left", padx=(6, 14),
                                                ipady=2)
        tk.Label(row, text="Payment", font=(FONT, 10), bg=COLORS["card"],
                 fg=COLORS["text"]).pack(side="left")
        ttk.Combobox(row, textvariable=self.mode_var, width=8,
                     values=["All", "Cash", "Card", "UPI"], state="readonly",
                     font=(FONT, 10)).pack(side="left", padx=(6, 14))
        button(row, "Apply", self.refresh, "primary").pack(side="left")
        tk.Label(row, text="Dates use the format YYYY-MM-DD",
                 font=(FONT, 9), bg=COLORS["card"], fg=COLORS["muted"]
                 ).pack(side="right")

    def build_kpis(self):
        row = tk.Frame(self, bg=COLORS["bg"])
        row.pack(fill="x", pady=12)
        cards = [("Total sales", "sales", COLORS["success"]),
                 ("Bills", "bills", COLORS["accent"]),
                 ("Average bill", "avg", COLORS["primary"]),
                 ("Discounts given", "discount", COLORS["muted"]),
                 ("GST collected", "gst", COLORS["muted"])]
        for i, (title, key, colour) in enumerate(cards):
            card = tk.Frame(row, bg=COLORS["card"], padx=16, pady=10)
            card.grid(row=0, column=i, sticky="nsew",
                      padx=(0, 12 if i < 4 else 0))
            row.columnconfigure(i, weight=1, uniform="k")
            tk.Label(card, text=title, font=(FONT, 9), bg=COLORS["card"],
                     fg=COLORS["muted"]).pack(anchor="w")
            tk.Label(card, textvariable=self.kpi_vars[key],
                     font=(FONT, 15, "bold"), bg=COLORS["card"], fg=colour
                     ).pack(anchor="w")

    def build_tabs(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)

        bills_tab = tk.Frame(self.tabs, bg=COLORS["card"], padx=10, pady=10)
        self.tabs.add(bills_tab, text="  Bills  ")
        top = tk.Frame(bills_tab, bg=COLORS["card"])
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="Double-click a bill to view or reprint it.",
                 font=(FONT, 9), bg=COLORS["card"], fg=COLORS["muted"]
                 ).pack(side="left")
        button(top, "Reprint selected", self.reprint, "primary"
               ).pack(side="right")
        self.bills_tree = make_tree(bills_tab, [
            ("invoice", "Invoice", 150, "w"), ("when", "Date & time", 140, "w"),
            ("table", "Table", 55, "center"), ("staff", "Staff", 120, "w"),
            ("mode", "Payment", 70, "center"),
            ("discount", "Discount", 80, "e"), ("total", "Total", 90, "e")])
        self.bills_tree.bind("<Double-1>", lambda e: self.reprint())

        items_tab = tk.Frame(self.tabs, bg=COLORS["card"], padx=10, pady=10)
        self.tabs.add(items_tab, text="  Items sold  ")
        self.items_tree = make_tree(items_tab, [
            ("name", "Item", 220, "w"), ("category", "Category", 120, "w"),
            ("qty", "Qty sold", 80, "center"), ("revenue", "Revenue", 110, "e")])

        self.daily_tab = tk.Frame(self.tabs, bg=COLORS["card"], padx=12, pady=10)
        self.tabs.add(self.daily_tab, text="  Daily sales  ")
        self.category_tab = tk.Frame(self.tabs, bg=COLORS["card"], padx=12,
                                     pady=10)
        self.tabs.add(self.category_tab, text="  By category  ")

    # -------------------------------------------------------------- logic
    def preset(self, which):
        today = date.today()
        if which == "month":
            start = today.replace(day=1)
        elif which == "all":
            start = date(2000, 1, 1)
        else:
            start = today - timedelta(days=which)
        self.from_var.set(start.isoformat())
        self.to_var.set(today.isoformat())
        self.refresh()

    def read_range(self):
        try:
            d1 = datetime.strptime(self.from_var.get().strip(), "%Y-%m-%d").date()
            d2 = datetime.strptime(self.to_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning("Reports", "Enter dates like 2026-11-15.")
            return None
        if d1 > d2:
            messagebox.showwarning("Reports", "'From' must not be after 'To'.")
            return None
        return d1, d2

    def refresh(self):
        rng = self.read_range()
        if rng is None:
            return
        d1, d2 = rng
        f, t = d1.isoformat(), d2.isoformat()
        mode = None if self.mode_var.get() == "All" else self.mode_var.get()

        s = queries.report_summary(f, t, mode)
        self.kpi_vars["sales"].set(f"₹ {s['sales']:,.0f}")
        self.kpi_vars["bills"].set(str(s["bills"]))
        self.kpi_vars["avg"].set(
            f"₹ {s['sales'] / s['bills']:,.0f}" if s["bills"] else "₹ 0")
        self.kpi_vars["discount"].set(f"₹ {s['discount']:,.0f}")
        self.kpi_vars["gst"].set(f"₹ {s['gst']:,.0f}")

        self.bills = queries.get_bills(f, t, mode)
        self.bills_tree.delete(*self.bills_tree.get_children())
        for b in self.bills:
            self.bills_tree.insert("", "end", iid=str(b["id"]), values=(
                b["invoice_no"], b["paid_at"][:16], b["table_no"], b["staff"],
                b["payment_mode"], f"₹ {b['discount']:,.2f}",
                f"₹ {b['total']:,.2f}"))

        self.items = queries.items_sold(f, t)
        self.items_tree.delete(*self.items_tree.get_children())
        for i, r in enumerate(self.items):
            self.items_tree.insert("", "end", iid=str(i), values=(
                r["name"], r["category"], r["qty"], f"₹ {r['revenue']:,.2f}"))

        self.draw_daily(d1, d2)
        for w in self.category_tab.winfo_children():
            w.destroy()
        HBarChart(self.category_tab,
                  [(r["name"], r["revenue"]) for r in queries.category_sales(f, t)],
                  "Revenue by category (₹)").pack(fill="both", expand=True)

    def draw_daily(self, d1, d2):
        for w in self.daily_tab.winfo_children():
            w.destroy()
        sales = {r["d"]: r["s"] for r in queries.daily_sales(
            d1.isoformat(), d2.isoformat())}
        if (d2 - d1).days < 31:                 # show empty days too
            days = [d1 + timedelta(days=i) for i in range((d2 - d1).days + 1)]
        else:                                   # long range: last 31 days
            days = [d2 - timedelta(days=i) for i in range(30, -1, -1)]
        data = [(d.strftime("%d/%m"), sales.get(d.isoformat(), 0.0))
                for d in days]
        title = "Daily sales (₹)" + ("  •  last 31 days of the range"
                                     if (d2 - d1).days >= 31 else "")
        BarChart(self.daily_tab, data, title).pack(fill="both", expand=True)

    def reprint(self):
        sel = self.bills_tree.selection()
        if not sel:
            messagebox.showwarning("Reports", "Select a bill first.")
            return
        bill, items = queries.get_bill(int(sel[0]))
        show_receipt(self.winfo_toplevel(), bill, items, 0.0,
                     heading="Invoice copy")

    # ------------------------------------------------------------- export
    def export_bills(self):
        if not self.bills:
            messagebox.showinfo("Export", "There are no bills in this range.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV file", "*.csv")],
            initialfile=f"bills_{self.from_var.get()}_to_{self.to_var.get()}.csv")
        if not path:
            return
        n = export.write_csv(
            path, ["Invoice", "Date & time", "Table", "Staff", "Payment",
                   "Subtotal", "Discount", "GST", "Total"],
            [(b["invoice_no"], b["paid_at"], b["table_no"], b["staff"],
              b["payment_mode"], b["subtotal"], b["discount"], b["gst"],
              b["total"]) for b in self.bills])
        messagebox.showinfo("Export", f"Saved {n} bills to:\n{path}")

    def export_items(self):
        if not self.items:
            messagebox.showinfo("Export", "There are no sales in this range.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV file", "*.csv")],
            initialfile=f"items_{self.from_var.get()}_to_{self.to_var.get()}.csv")
        if not path:
            return
        n = export.write_csv(
            path, ["Item", "Category", "Qty sold", "Revenue"],
            [(r["name"], r["category"], r["qty"], r["revenue"])
             for r in self.items])
        messagebox.showinfo("Export", f"Saved {n} items to:\n{path}")
