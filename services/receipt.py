"""Builds the invoice as plain text (for the screen) and HTML (to print)."""
import os
from datetime import datetime
from html import escape

from config import BILLS_DIR, GST_RATE, RESTAURANT_NAME

WIDTH = 42


def _when(bill):
    try:
        t = datetime.strptime(bill["paid_at"], "%Y-%m-%d %H:%M:%S")
        return t.strftime("%d-%b-%Y %I:%M %p")
    except (TypeError, ValueError):
        return str(bill["paid_at"])


def breakdown(bill):
    """Split the saved bill into the lines shown on the invoice."""
    cgst = round(bill["gst"] / 2, 2)
    sgst = round(bill["gst"] - cgst, 2)
    round_off = round(bill["total"] - (bill["subtotal"] - bill["discount"]
                                       + bill["gst"]), 2)
    return cgst, sgst, round_off


def receipt_text(bill, items):
    cgst, sgst, round_off = breakdown(bill)
    half = f"{GST_RATE * 50:g}%"

    def two(left, right):
        return left + right.rjust(WIDTH - len(left))

    lines = [RESTAURANT_NAME.center(WIDTH), "TAX INVOICE".center(WIDTH),
             "-" * WIDTH,
             f"Invoice : {bill['invoice_no']}",
             f"Date    : {_when(bill)}",
             f"Table   : {bill['table_no']}      Staff: {bill['staff']}",
             "-" * WIDTH,
             f"{'Item':<20}{'Qty':>4}{'Rate':>8}{'Amount':>10}",
             "-" * WIDTH]
    for it in items:
        amount = it["quantity"] * it["price"]
        lines.append(f"{it['name'][:20]:<20}{it['quantity']:>4}"
                     f"{it['price']:>8.2f}{amount:>10.2f}")
    lines.append("-" * WIDTH)
    lines.append(two("Subtotal", f"{bill['subtotal']:.2f}"))
    if bill["discount"] > 0:
        lines.append(two("Discount", f"-{bill['discount']:.2f}"))
    lines.append(two(f"CGST ({half})", f"{cgst:.2f}"))
    lines.append(two(f"SGST ({half})", f"{sgst:.2f}"))
    if round_off:
        lines.append(two("Round off", f"{round_off:+.2f}"))
    lines.append("=" * WIDTH)
    lines.append(two("TOTAL", f"{bill['total']:.2f}"))
    lines.append("=" * WIDTH)
    lines.append(f"Paid by : {bill['payment_mode']}")
    lines.append("")
    lines.append("Thank you! Please visit again.".center(WIDTH))
    return "\n".join(lines)


def receipt_html(bill, items):
    cgst, sgst, round_off = breakdown(bill)
    half = f"{GST_RATE * 50:g}%"
    rows = "".join(
        f"<tr><td>{escape(it['name'])}</td><td class='n'>{it['quantity']}</td>"
        f"<td class='n'>{it['price']:.2f}</td>"
        f"<td class='n'>{it['quantity'] * it['price']:.2f}</td></tr>"
        for it in items)
    extra = ""
    if bill["discount"] > 0:
        extra += f"<tr><td colspan='3'>Discount</td><td class='n'>-{bill['discount']:.2f}</td></tr>"
    extra += f"<tr><td colspan='3'>CGST ({half})</td><td class='n'>{cgst:.2f}</td></tr>"
    extra += f"<tr><td colspan='3'>SGST ({half})</td><td class='n'>{sgst:.2f}</td></tr>"
    if round_off:
        extra += f"<tr><td colspan='3'>Round off</td><td class='n'>{round_off:+.2f}</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{escape(bill['invoice_no'])}</title>
<style>
  body {{ background:#F4F5F7; font-family:'Segoe UI',Arial,sans-serif; margin:0; padding:30px; color:#222; }}
  .bill {{ position:relative; background:#fff; max-width:400px; margin:auto; padding:28px 26px;
           border-radius:12px; box-shadow:0 6px 24px rgba(0,0,0,.12); overflow:hidden; }}
  h1 {{ margin:0; text-align:center; color:#E8590C; font-size:26px; }}
  .sub {{ text-align:center; color:#6B7280; letter-spacing:3px; font-size:12px; margin:4px 0 16px; }}
  .meta {{ font-size:13px; color:#444; line-height:1.7; border-top:2px dashed #ddd; border-bottom:2px dashed #ddd; padding:10px 0; }}
  table {{ width:100%; border-collapse:collapse; margin-top:12px; font-size:14px; }}
  th {{ text-align:left; font-size:12px; color:#6B7280; border-bottom:1px solid #ddd; padding:6px 0; }}
  td {{ padding:6px 0; }} .n, th.n {{ text-align:right; }}
  .total td {{ font-size:18px; font-weight:700; border-top:2px solid #222; padding-top:10px; color:#E8590C; }}
  .thanks {{ text-align:center; margin-top:20px; color:#6B7280; font-size:13px; }}
  .stamp {{ position:absolute; right:18px; top:70px; transform:rotate(-14deg); border:3px solid #2F9E44;
            color:#2F9E44; font-weight:800; padding:4px 12px; border-radius:8px; letter-spacing:2px; opacity:.8; }}
  button {{ display:block; margin:20px auto 0; padding:10px 22px; background:#E8590C; color:#fff; border:0;
            border-radius:8px; font-size:14px; cursor:pointer; }}
  @media print {{ body {{ background:#fff; padding:0; }} .bill {{ box-shadow:none; }} button {{ display:none; }} }}
</style></head><body>
<div class="bill">
  <div class="stamp">PAID &middot; {escape(bill['payment_mode'].upper())}</div>
  <h1>{escape(RESTAURANT_NAME)}</h1>
  <div class="sub">TAX INVOICE</div>
  <div class="meta">Invoice: <b>{escape(bill['invoice_no'])}</b><br>
    Date: {escape(_when(bill))}<br>Table {bill['table_no']} &middot; Served by {escape(bill['staff'])}</div>
  <table>
    <tr><th>Item</th><th class="n">Qty</th><th class="n">Rate</th><th class="n">Amount</th></tr>
    {rows}
    <tr><td colspan="3" style="border-top:1px solid #ddd;padding-top:10px">Subtotal</td>
        <td class="n" style="border-top:1px solid #ddd;padding-top:10px">{bill['subtotal']:.2f}</td></tr>
    {extra}
    <tr class="total"><td colspan="3">TOTAL</td><td class="n">&#8377; {bill['total']:.2f}</td></tr>
  </table>
  <div class="thanks">Thank you! Please visit again.</div>
  <button onclick="window.print()">Print / Save as PDF</button>
</div></body></html>"""


def save_html(bill, items):
    """Write the printable invoice to the bills folder; return its path."""
    os.makedirs(BILLS_DIR, exist_ok=True)
    path = os.path.join(BILLS_DIR, f"{bill['invoice_no']}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(receipt_html(bill, items))
    return path
