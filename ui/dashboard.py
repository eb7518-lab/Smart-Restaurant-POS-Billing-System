"""Main dashboard: sidebar navigation, live KPI cards and charts."""
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from config import COLORS, FONT, RESTAURANT_NAME, LOW_STOCK_LIMIT
from database import queries
from services import demo_data
from services.auth import Session
from ui.billing_screen import BillingScreen
from ui.charts import BarChart, HBarChart, Donut
from ui.menu_manager import MenuManager
from ui.reports_screen import ReportsScreen
from ui.staff_screen import StaffScreen
from ui.order_screen import OrderScreen
from ui.orders_list import OrdersList
from ui.tables_screen import TablesScreen
from ui.widgets import button

PAY_COLOURS = {"Cash": "#2F9E44", "UPI": "#E8590C", "Card": "#1F2A44"}
TITLES = {"home": "Dashboard", "tables": "Tables", "orders": "Orders",
          "menu": "Menu Manager", "staff": "Staff", "reports": "Reports"}


class Dashboard(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app

        # ---- Sidebar ----
        self.sidebar = tk.Frame(self, bg=COLORS["primary"], width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text=RESTAURANT_NAME, font=(FONT, 16, "bold"),
                 bg=COLORS["primary"], fg="white").pack(pady=(25, 4))
        tk.Frame(self.sidebar, bg=COLORS["accent"], height=3, width=40
                 ).pack(pady=(0, 26))

        self.nav_buttons = {}
        self.nav_area = tk.Frame(self.sidebar, bg=COLORS["primary"])
        self.nav_area.pack(fill="x")

        tk.Button(self.sidebar, text="Logout", font=(FONT, 11),
                  bg=COLORS["danger"], fg="white", relief="flat",
                  cursor="hand2", command=self.logout
                  ).pack(side="bottom", fill="x", padx=15, pady=20, ipady=6)

        # ---- Right side ----
        right = tk.Frame(self, bg=COLORS["bg"])
        right.pack(side="left", fill="both", expand=True)

        self.topbar = tk.Frame(right, bg=COLORS["card"], height=60)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)
        self.page_title = tk.Label(self.topbar, text="", font=(FONT, 16, "bold"),
                                   bg=COLORS["card"], fg=COLORS["text"])
        self.page_title.pack(side="left", padx=25)
        self.user_label = tk.Label(self.topbar, text="", font=(FONT, 10),
                                   bg=COLORS["card"], fg=COLORS["muted"])
        self.user_label.pack(side="right", padx=25)
        self.clock_label = tk.Label(self.topbar, text="", font=(FONT, 10),
                                    bg=COLORS["card"], fg=COLORS["muted"])
        self.clock_label.pack(side="right", padx=10)

        self.content = tk.Frame(right, bg=COLORS["bg"])
        self.content.pack(fill="both", expand=True, padx=25, pady=18)
        self._clock_job = None

    # ---------- called by the app each time the dashboard is shown ----------
    def on_show(self):
        user = Session.user
        self.user_label.config(
            text=f"{user['full_name']}  ({user['role'].title()})")
        self.build_navigation()
        self.show_page("home")
        self.stop_clock()
        self.tick()

    def build_navigation(self):
        for w in self.nav_area.winfo_children():
            w.destroy()
        self.nav_buttons = {}
        items = [("home", "Dashboard"), ("tables", "Tables"),
                 ("orders", "Orders")]
        if Session.is_admin():
            items += [("menu", "Menu Manager"), ("staff", "Staff"),
                      ("reports", "Reports")]
        for key, label in items:
            btn = tk.Button(self.nav_area, text="   " + label, anchor="w",
                            font=(FONT, 11), bg=COLORS["primary"], fg="white",
                            activebackground=COLORS["accent"],
                            activeforeground="white", relief="flat",
                            cursor="hand2",
                            command=lambda k=key: self.show_page(k))
            btn.pack(fill="x", ipady=8)
            self.nav_buttons[key] = btn

    # ---------- page switching ----------
    def _prepare(self, nav_key, title):
        for k, b in self.nav_buttons.items():
            b.config(bg=COLORS["accent"] if k == nav_key else COLORS["primary"])
        for w in self.content.winfo_children():
            w.destroy()
        self.page_title.config(text=title)

    def show_page(self, key):
        self._prepare(key, TITLES[key])
        if key == "home":
            self.build_home()
        elif key == "tables":
            TablesScreen(self.content, self).pack(fill="both", expand=True)
        elif key == "orders":
            OrdersList(self.content, self).pack(fill="both", expand=True)
        elif key == "menu" and Session.is_admin():
            MenuManager(self.content, self).pack(fill="both", expand=True)
        elif key == "staff" and Session.is_admin():
            StaffScreen(self.content, self).pack(fill="both", expand=True)
        elif key == "reports" and Session.is_admin():
            ReportsScreen(self.content, self).pack(fill="both", expand=True)
        else:
            self.build_placeholder("Access denied")

    def open_order(self, table_id):
        self._prepare("tables", "Take Order")
        OrderScreen(self.content, self, table_id).pack(fill="both", expand=True)

    def open_billing(self, order_id, table_id):
        self._prepare("tables", "Billing")
        BillingScreen(self.content, self, order_id, table_id
                      ).pack(fill="both", expand=True)

    # ---------- home page ----------
    def panel(self, parent, row, col, last=False, **kw):
        f = tk.Frame(parent, bg=COLORS["card"], padx=14, pady=10)
        f.grid(row=row, column=col, sticky="nsew",
               padx=(0, 0 if last else 15), **kw)
        return f

    def build_home(self):
        s = queries.today_stats()
        avg = s["sales"] / s["bills"] if s["bills"] else 0

        # --- KPI cards
        row = tk.Frame(self.content, bg=COLORS["bg"])
        row.pack(fill="x")
        cards = [("Today's Sales", f"₹ {s['sales']:,.0f}", COLORS["success"]),
                 ("Bills Today", str(s["bills"]), COLORS["accent"]),
                 ("Average Bill", f"₹ {avg:,.0f}", COLORS["primary"]),
                 ("Tables Occupied", f"{s['occupied']} / {s['tables']}",
                  COLORS["muted"])]
        for i, (title, value, colour) in enumerate(cards):
            card = tk.Frame(row, bg=COLORS["card"], padx=20, pady=14)
            card.grid(row=0, column=i, padx=(0, 15 if i < 3 else 0),
                      sticky="nsew")
            row.columnconfigure(i, weight=1, uniform="kpi")
            tk.Frame(card, bg=colour, height=3).pack(fill="x", pady=(0, 8))
            tk.Label(card, text=title, font=(FONT, 10), bg=COLORS["card"],
                     fg=COLORS["muted"]).pack(anchor="w")
            tk.Label(card, text=value, font=(FONT, 20, "bold"),
                     bg=COLORS["card"], fg=colour).pack(anchor="w")

        # --- charts row
        charts = tk.Frame(self.content, bg=COLORS["bg"])
        charts.pack(fill="both", expand=True, pady=(15, 0))
        charts.columnconfigure(0, weight=3, uniform="c")
        charts.columnconfigure(1, weight=2, uniform="c")
        charts.rowconfigure(0, weight=1)

        week = [("Today" if i == 6 else d.strftime("%a"), v)
                for i, (d, v) in enumerate(queries.sales_by_day(7))]
        BarChart(self.panel(charts, 0, 0), week, "Sales  •  last 7 days"
                 ).pack(fill="both", expand=True)
        top = [(r["name"], r["qty"]) for r in queries.top_items(5, 30)]
        HBarChart(self.panel(charts, 0, 1, last=True), top,
                  "Best sellers  •  last 30 days"
                  ).pack(fill="both", expand=True)

        # --- lower row
        lower = tk.Frame(self.content, bg=COLORS["bg"])
        lower.pack(fill="x", pady=(15, 0))
        for c in range(3):
            lower.columnconfigure(c, weight=1, uniform="l")

        split = queries.payment_split(30)
        total = sum(r["amount"] for r in split)
        Donut(self.panel(lower, 0, 0), [
            (r["payment_mode"], r["amount"],
             PAY_COLOURS.get(r["payment_mode"], COLORS["muted"]))
            for r in split], "Payment modes  •  30 days",
            centre_text=f"₹{total / 1000:.1f}k" if total else "",
            height=150).pack(fill="x")

        self.build_stock_panel(self.panel(lower, 0, 1))
        self.build_tools_panel(self.panel(lower, 0, 2, last=True))

    def build_stock_panel(self, panel):
        tk.Label(panel, text="Low stock", font=(FONT, 11, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
        low = queries.get_low_stock(LOW_STOCK_LIMIT)
        if not low:
            tk.Label(panel, text="✓  All items are well stocked",
                     font=(FONT, 10), bg=COLORS["card"], fg=COLORS["success"]
                     ).pack(anchor="w", pady=(18, 0))
            return
        for item in low[:5]:
            r = tk.Frame(panel, bg=COLORS["card"])
            r.pack(fill="x", pady=2)
            tk.Label(r, text=item["name"], font=(FONT, 10),
                     bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")
            tk.Label(r, text=f"{item['stock']} left",
                     font=(FONT, 10, "bold"), bg=COLORS["card"],
                     fg=COLORS["danger"]).pack(side="right")

    def build_tools_panel(self, panel):
        if Session.is_admin():
            tk.Label(panel, text="Demo data", font=(FONT, 11, "bold"),
                     bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
            tk.Label(panel, text="Add two weeks of sample sales so the charts "
                                 "and smart suggestions have data to show.",
                     font=(FONT, 9), bg=COLORS["card"], fg=COLORS["muted"],
                     wraplength=260, justify="left"
                     ).pack(anchor="w", pady=(4, 8))
            r = tk.Frame(panel, bg=COLORS["card"])
            r.pack(anchor="w")
            button(r, "Load demo data", self.load_demo, "primary"
                   ).pack(side="left")
            button(r, "Clear", self.clear_demo, "light"
                   ).pack(side="left", padx=8)
        else:
            tk.Label(panel, text="Quick tips", font=(FONT, 11, "bold"),
                     bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
            for tip in ["Click a table to start an order",
                        "Double-click a menu item to add it",
                        "Send new items to the kitchen with KOT"]:
                tk.Label(panel, text="•  " + tip, font=(FONT, 10),
                         bg=COLORS["card"], fg=COLORS["muted"]
                         ).pack(anchor="w", pady=2)

    def load_demo(self):
        if messagebox.askyesno(
                "Load demo data",
                "Add about two weeks of sample sales?\n\n"
                "You can remove them again with the Clear button."):
            count = demo_data.load_demo()
            messagebox.showinfo("Demo data", f"Added {count} sample bills.")
            self.show_page("home")

    def clear_demo(self):
        if messagebox.askyesno("Clear demo data",
                               "Remove all demo bills? Real bills are kept."):
            demo_data.clear_demo()
            self.show_page("home")

    def build_placeholder(self, name):
        box = tk.Frame(self.content, bg=COLORS["card"], padx=30, pady=30)
        box.pack(fill="both", expand=True)
        tk.Label(box, text=f"{name} screen", font=(FONT, 18, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(pady=(60, 5))
        tk.Label(box, text="This screen will be built in the next stage.",
                 font=(FONT, 11), bg=COLORS["card"], fg=COLORS["muted"]).pack()

    # ---------- helpers ----------
    def tick(self):
        self.clock_label.config(
            text=datetime.now().strftime("%d %b %Y   %I:%M:%S %p"))
        self._clock_job = self.after(1000, self.tick)

    def stop_clock(self):
        if self._clock_job:
            self.after_cancel(self._clock_job)
            self._clock_job = None

    def logout(self):
        if messagebox.askyesno("Logout", "Do you want to log out?"):
            self.stop_clock()
            Session.logout()
            self.app.show("login")
