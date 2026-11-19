"""Pop-up shown after a successful payment."""
import tkinter as tk
import webbrowser
from pathlib import Path

from config import COLORS, FONT
from services import receipt
from ui.widgets import button


def show_receipt(parent, bill, items, change=0.0,
                 heading="Payment successful"):
    text_body = receipt.receipt_text(bill, items)

    win = tk.Toplevel(parent)
    win.title(f"Invoice {bill['invoice_no']}")
    win.configure(bg=COLORS["card"])
    win.resizable(False, False)

    tk.Label(win, text=heading, font=(FONT, 15, "bold"),
             bg=COLORS["card"], fg=COLORS["success"]).pack(pady=(18, 2))
    if change > 0:
        tk.Label(win, text=f"Return change:  ₹ {change:,.2f}",
                 font=(FONT, 12, "bold"), bg=COLORS["card"],
                 fg=COLORS["accent"]).pack()

    box = tk.Text(win, width=WIDTH_CHARS, height=text_body.count("\n") + 2,
                  font=("Consolas", 10), relief="flat", bg="#FFFBEB")
    box.insert("1.0", text_body)
    box.config(state="disabled")
    box.pack(padx=22, pady=14)

    def open_printable():
        path = receipt.save_html(bill, items)
        webbrowser.open(Path(path).as_uri())

    row = tk.Frame(win, bg=COLORS["card"])
    row.pack(pady=(0, 18))
    button(row, "Open Printable Bill", open_printable, "primary"
           ).pack(side="left", padx=6)
    button(row, "Close", win.destroy, "dark").pack(side="left", padx=6)

    win.transient(parent)
    try:
        win.grab_set()
    except tk.TclError:
        pass


WIDTH_CHARS = receipt.WIDTH + 2
