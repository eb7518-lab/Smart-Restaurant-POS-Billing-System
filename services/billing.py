"""Bill calculations (no UI, no database)."""
import math
from config import GST_RATE, SERVICE_CHARGE_RATE


def calculate_bill(lines, discount=0.0, gst_rate=GST_RATE,
                   service_rate=SERVICE_CHARGE_RATE):
    """lines is an iterable of (quantity, unit_price) pairs.

    Discount is a flat amount taken off the subtotal. GST is charged on the
    discounted amount plus any service charge.
    """
    subtotal = round(sum(q * p for q, p in lines), 2)
    discount = round(max(0.0, min(discount, subtotal)), 2)
    taxable = subtotal - discount
    service = round(taxable * service_rate, 2)
    gst = round((taxable + service) * gst_rate, 2)
    total = round(taxable + service + gst, 2)
    return {"subtotal": subtotal, "discount": discount, "service": service,
            "gst": gst, "total": total}


def round_total(total):
    """Round the payable amount to the nearest rupee.

    Returns (payable, round_off) where round_off is the +/- adjustment.
    """
    payable = float(math.floor(total + 0.5))
    return payable, (round(payable - total, 2) or 0.0)
