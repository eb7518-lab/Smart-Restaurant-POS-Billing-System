"""Sample sales history so charts and suggestions have something to show.

Every demo bill has an invoice number starting with DEMO-, so it can be
removed later without touching real bills.
"""
import random
from datetime import datetime, timedelta

from database.db import get_connection

# Dishes people tend to order together (this is what the "Goes well with"
# suggestion on the order screen learns from).
PAIRS = {
    "Butter Chicken": ["Butter Naan", "Garlic Naan"],
    "Paneer Butter Masala": ["Butter Naan", "Tandoori Roti"],
    "Dal Tadka": ["Tandoori Roti"],
    "Mixed Veg Curry": ["Tandoori Roti"],
    "Chicken Biryani": ["Mango Lassi"],
    "Veg Biryani": ["Fresh Lime Soda"],
    "Paneer Tikka": ["Masala Chai"],
    "Chicken 65": ["Fresh Lime Soda"],
}
POPULARITY = {"Butter Chicken": 6, "Chicken Biryani": 6, "Paneer Butter Masala": 5,
              "Veg Biryani": 3, "Paneer Tikka": 4, "Dal Tadka": 3}
LOW_STOCK = {"Chicken 65": 6, "Brownie": 3, "Fresh Lime Soda": 8}
PAYMENTS = (["UPI"] * 45) + (["Cash"] * 30) + (["Card"] * 25)


def clear_demo():
    conn = get_connection()
    try:
        with conn:
            ids = [r["order_id"] for r in conn.execute(
                "SELECT order_id FROM bills WHERE invoice_no LIKE 'DEMO-%'")]
            conn.execute("DELETE FROM bills WHERE invoice_no LIKE 'DEMO-%'")
            conn.executemany("DELETE FROM orders WHERE id = ?",
                             [(i,) for i in ids])
            conn.executemany("UPDATE menu_items SET stock = 100 WHERE name = ?",
                             [(n,) for n in LOW_STOCK])
    finally:
        conn.close()


def _pick_time(rng, day, now):
    """Random lunch/dinner time on `day`; None if it would be in the future."""
    for _ in range(30):
        if rng.random() < 0.45:
            minutes = rng.randint(12 * 60, 15 * 60)          # lunch
        else:
            minutes = rng.randint(19 * 60, 22 * 60 + 30)     # dinner
        ts = datetime.combine(day, datetime.min.time()) + timedelta(minutes=minutes)
        if ts <= now:
            return ts
    return None


def load_demo(days=14):
    """Replace any earlier demo data with fresh sample bills. Returns count."""
    clear_demo()
    rng = random.Random()
    now = datetime.now()
    conn = get_connection()
    created = 0
    try:
        with conn:
            menu = {r["name"]: r for r in conn.execute(
                "SELECT m.id, m.name, m.price, c.name AS category "
                "FROM menu_items m JOIN categories c ON c.id = m.category_id")}
            tables = [r["id"] for r in conn.execute("SELECT id FROM tables")]
            users = [r["id"] for r in conn.execute("SELECT id FROM users")]
            if not menu or not tables or not users:
                return 0
            mains = [n for n, r in menu.items()
                     if r["category"] in ("Starters", "Main Course")]
            extras = [n for n, r in menu.items()
                      if r["category"] in ("Drinks", "Desserts")]

            for offset in range(days - 1, -1, -1):
                day = (now - timedelta(days=offset)).date()
                count = rng.randint(14, 24) + (8 if day.weekday() >= 4 else 0)
                for n in range(1, count + 1):
                    ts = _pick_time(rng, day, now)
                    if ts is None:
                        continue
                    basket = {}
                    for _ in range(rng.choice([1, 1, 2, 2, 3])):
                        name = rng.choices(
                            mains, [POPULARITY.get(m, 1) for m in mains])[0]
                        basket[name] = basket.get(name, 0) + rng.choice([1, 1, 2])
                        for pair in PAIRS.get(name, []):
                            if pair in menu and rng.random() < 0.7:
                                basket[pair] = basket.get(pair, 0) + rng.choice([1, 2])
                    if extras and rng.random() < 0.5:
                        e = rng.choice(extras)
                        basket[e] = basket.get(e, 0) + 1

                    subtotal = sum(menu[nm]["price"] * q for nm, q in basket.items())
                    discount = round(subtotal * 0.10, 2) if rng.random() < 0.15 else 0.0
                    gst = round((subtotal - discount) * 0.05, 2)
                    total = float(round(subtotal - discount + gst))

                    started = ts - timedelta(minutes=rng.randint(30, 70))
                    cur = conn.execute(
                        "INSERT INTO orders (table_id, user_id, status, created_at)"
                        " VALUES (?, ?, 'billed', ?)",
                        (rng.choice(tables), rng.choice(users),
                         started.strftime("%Y-%m-%d %H:%M:%S")))
                    order_id = cur.lastrowid
                    for nm, q in basket.items():
                        conn.execute(
                            "INSERT INTO order_items (order_id, item_id, quantity,"
                            " price, kot_qty) VALUES (?, ?, ?, ?, ?)",
                            (order_id, menu[nm]["id"], q, menu[nm]["price"], q))
                    conn.execute(
                        "INSERT INTO bills (order_id, invoice_no, subtotal, gst,"
                        " discount, total, payment_mode, paid_at)"
                        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (order_id, f"DEMO-{day:%Y%m%d}-{n:04d}", subtotal, gst,
                         discount, total, rng.choice(PAYMENTS),
                         ts.strftime("%Y-%m-%d %H:%M:%S")))
                    created += 1

            for name, stock in LOW_STOCK.items():
                conn.execute("UPDATE menu_items SET stock = ? WHERE name = ?",
                             (stock, name))
    finally:
        conn.close()
    return created
