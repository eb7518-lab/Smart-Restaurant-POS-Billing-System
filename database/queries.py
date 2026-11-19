"""All SQL used by the screens lives here (UI files never write SQL)."""
import uuid
from datetime import datetime, timedelta

from database.db import get_connection, IntegrityError


def _rows(sql, params=()):
    conn = get_connection()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def _row(sql, params=()):
    conn = get_connection()
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


# ---------------------------------------------------------------- tables
def get_tables():
    """Every table with its open order id and running amount (if any)."""
    return _rows("""
        SELECT t.id, t.table_no, t.capacity, t.status,
               o.id AS order_id, o.created_at,
               COALESCE((SELECT SUM(quantity * price) FROM order_items
                         WHERE order_id = o.id), 0) AS amount
        FROM tables t
        LEFT JOIN orders o ON o.table_id = t.id AND o.status = 'open'
        ORDER BY t.table_no""")


def get_table(table_id):
    return _row("SELECT * FROM tables WHERE id = ?", (table_id,))


# ------------------------------------------------------------------ menu
def get_categories():
    return _rows("SELECT id, name FROM categories ORDER BY id")


def search_menu(category_id=None, text=""):
    """Available items, best sellers first, then alphabetical."""
    sql = """
        SELECT m.id, m.name, m.price, m.stock, c.name AS category,
               COALESCE((SELECT SUM(oi.quantity) FROM order_items oi
                         JOIN orders o ON o.id = oi.order_id
                         WHERE oi.item_id = m.id AND o.status = 'billed'),
                        0) AS sold
        FROM menu_items m
        JOIN categories c ON c.id = m.category_id
        WHERE m.available = 1"""
    params = []
    if category_id is not None:
        sql += " AND m.category_id = ?"
        params.append(category_id)
    if text:
        sql += " AND m.name LIKE ?"
        params.append(f"%{text}%")
    sql += " ORDER BY sold DESC, m.name"
    return _rows(sql, params)


# ---------------------------------------------------------------- orders
def get_open_order(table_id):
    return _row("SELECT * FROM orders WHERE table_id = ? AND status = 'open'",
                (table_id,))


def get_or_create_order(table_id, user_id):
    """Return the table's open order, creating it (and occupying the table)."""
    conn = get_connection()
    try:
        with conn:
            row = conn.execute(
                "SELECT id FROM orders WHERE table_id = ? AND status = 'open'",
                (table_id,)).fetchone()
            if row:
                return row["id"]
            cur = conn.execute(
                "INSERT INTO orders (table_id, user_id) VALUES (?, ?)",
                (table_id, user_id))
            conn.execute("UPDATE tables SET status = 'occupied' WHERE id = ?",
                         (table_id,))
            return cur.lastrowid
    finally:
        conn.close()


def get_order_items(order_id):
    return _rows("""
        SELECT oi.id, oi.item_id, m.name, oi.quantity, oi.price, oi.kot_qty
        FROM order_items oi JOIN menu_items m ON m.id = oi.item_id
        WHERE oi.order_id = ? ORDER BY oi.id""", (order_id,))


def add_item(order_id, item_id, qty):
    """Add an item; if it is already on the order, increase its quantity."""
    conn = get_connection()
    try:
        with conn:
            existing = conn.execute(
                "SELECT id FROM order_items WHERE order_id = ? AND item_id = ?",
                (order_id, item_id)).fetchone()
            if existing:
                conn.execute("UPDATE order_items SET quantity = quantity + ? "
                             "WHERE id = ?", (qty, existing["id"]))
            else:
                price = conn.execute("SELECT price FROM menu_items WHERE id = ?",
                                     (item_id,)).fetchone()["price"]
                conn.execute(
                    "INSERT INTO order_items (order_id, item_id, quantity, price)"
                    " VALUES (?, ?, ?, ?)", (order_id, item_id, qty, price))
    finally:
        conn.close()


def change_quantity(order_item_id, delta):
    """Change quantity by delta (row deleted at zero).

    Returns False (and changes nothing) if it would exceed the stock.
    """
    conn = get_connection()
    try:
        with conn:
            row = conn.execute(
                "SELECT oi.quantity, m.stock FROM order_items oi "
                "JOIN menu_items m ON m.id = oi.item_id WHERE oi.id = ?",
                (order_item_id,)).fetchone()
            if row is None:
                return True
            new_qty = row["quantity"] + delta
            if delta > 0 and new_qty > row["stock"]:
                return False
            if new_qty <= 0:
                conn.execute("DELETE FROM order_items WHERE id = ?",
                             (order_item_id,))
            else:
                conn.execute(
                    "UPDATE order_items SET quantity = ?, "
                    "kot_qty = LEAST(kot_qty, ?) WHERE id = ?",
                    (new_qty, new_qty, order_item_id))
            return True
    finally:
        conn.close()


def remove_item(order_item_id):
    conn = get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM order_items WHERE id = ?",
                         (order_item_id,))
    finally:
        conn.close()


def count_order_items(order_id):
    return _row("SELECT COUNT(*) AS n FROM order_items WHERE order_id = ?",
                (order_id,))["n"]


def cancel_order(order_id):
    """Cancel an order and free its table."""
    conn = get_connection()
    try:
        with conn:
            row = conn.execute("SELECT table_id FROM orders WHERE id = ?",
                               (order_id,)).fetchone()
            conn.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?",
                         (order_id,))
            if row:
                conn.execute("UPDATE tables SET status = 'free' WHERE id = ?",
                             (row["table_id"],))
    finally:
        conn.close()


def get_open_orders():
    return _rows("""
        SELECT o.id, o.table_id, t.table_no, u.full_name, o.created_at,
               COALESCE((SELECT SUM(quantity) FROM order_items
                         WHERE order_id = o.id), 0) AS items,
               COALESCE((SELECT SUM(quantity * price) FROM order_items
                         WHERE order_id = o.id), 0) AS amount
        FROM orders o
        JOIN tables t ON t.id = o.table_id
        JOIN users u ON u.id = o.user_id
        WHERE o.status = 'open'
        ORDER BY o.created_at""")


# --------------------------------------------------------------- kitchen
def get_kot_items(order_id):
    """Items (and quantities) not yet sent to the kitchen."""
    return _rows("""
        SELECT m.name, oi.quantity - oi.kot_qty AS pending
        FROM order_items oi JOIN menu_items m ON m.id = oi.item_id
        WHERE oi.order_id = ? AND oi.quantity > oi.kot_qty
        ORDER BY oi.id""", (order_id,))


def mark_kot_sent(order_id):
    conn = get_connection()
    try:
        with conn:
            conn.execute("UPDATE order_items SET kot_qty = quantity "
                         "WHERE order_id = ?", (order_id,))
    finally:
        conn.close()


# ----------------------------------------------------------------- stock
def get_stock(item_id):
    row = _row("SELECT stock FROM menu_items WHERE id = ?", (item_id,))
    return row["stock"] if row else 0


def qty_in_order(order_id, item_id):
    row = _row("SELECT COALESCE(SUM(quantity), 0) AS n FROM order_items "
               "WHERE order_id = ? AND item_id = ?", (order_id, item_id))
    return row["n"]


def get_low_stock(limit_value):
    return _rows("SELECT name, stock FROM menu_items "
                 "WHERE available = 1 AND stock <= ? ORDER BY stock, name",
                 (limit_value,))


# --------------------------------------------------------------- billing
def set_table_status(table_id, status):
    conn = get_connection()
    try:
        with conn:
            conn.execute("UPDATE tables SET status = ? WHERE id = ?",
                         (status, table_id))
    finally:
        conn.close()


def create_bill(order_id, subtotal, gst, discount, total, payment_mode):
    """Save the bill, close the order, free the table, reduce stock.

    Everything happens in ONE transaction: it either all works or none of it.
    Returns the new bill id.
    """
    conn = get_connection()
    try:
        with conn:
            order = conn.execute(
                "SELECT table_id, status FROM orders WHERE id = ?",
                (order_id,)).fetchone()
            if order is None or order["status"] != "open":
                raise ValueError("This order is no longer open.")

            cur = conn.execute(
                "INSERT INTO bills (order_id, invoice_no, subtotal, gst, "
                "discount, total, payment_mode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (order_id, "TMP-" + uuid.uuid4().hex, subtotal, gst, discount,
                 total, payment_mode))
            bill_id = cur.lastrowid
            conn.execute("UPDATE bills SET invoice_no = ? WHERE id = ?",
                         (f"INV-{datetime.now():%Y%m%d}-{bill_id:04d}", bill_id))

            conn.execute("UPDATE orders SET status = 'billed' WHERE id = ?",
                         (order_id,))
            conn.execute("UPDATE tables SET status = 'free' WHERE id = ?",
                         (order["table_id"],))
            conn.execute("""
                UPDATE menu_items SET stock = GREATEST(0, stock - COALESCE(
                    (SELECT SUM(quantity) FROM order_items
                     WHERE order_id = ? AND item_id = menu_items.id), 0))
                WHERE id IN (SELECT item_id FROM order_items
                             WHERE order_id = ?)""", (order_id, order_id))
            return bill_id
    finally:
        conn.close()


def get_bill(bill_id):
    """Return (bill_row, item_rows) for printing."""
    bill = _row("""
        SELECT b.*, o.table_id, t.table_no, u.full_name AS staff
        FROM bills b
        JOIN orders o ON o.id = b.order_id
        JOIN tables t ON t.id = o.table_id
        JOIN users u ON u.id = o.user_id
        WHERE b.id = ?""", (bill_id,))
    items = _rows("""
        SELECT m.name, oi.quantity, oi.price
        FROM order_items oi JOIN menu_items m ON m.id = oi.item_id
        WHERE oi.order_id = ? ORDER BY oi.id""", (bill["order_id"],))
    return bill, items


# ------------------------------------------------------------- analytics
def today_stats():
    b = _row("SELECT COALESCE(SUM(total), 0) AS sales, COUNT(*) AS bills "
             "FROM bills WHERE DATE(paid_at) = CURDATE()")
    t = _row("SELECT COUNT(*) AS tables, "
             "COALESCE(SUM(status != 'free'), 0) AS occupied FROM tables")
    return {"sales": b["sales"], "bills": b["bills"],
            "tables": t["tables"], "occupied": t["occupied"]}


def sales_by_day(days=7):
    """[(date, total), ...] oldest first, missing days filled with 0."""
    rows = _rows("SELECT date(paid_at) AS d, SUM(total) AS s FROM bills "
                 "WHERE date(paid_at) >= DATE_SUB(CURDATE(), INTERVAL ? DAY) "
                 "GROUP BY d", (days - 1,))
    data = {r["d"]: r["s"] for r in rows}
    today = datetime.now().date()
    out = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        out.append((d, data.get(d.isoformat(), 0.0)))
    return out


def top_items(limit=5, days=30):
    return _rows("""
        SELECT m.name, SUM(oi.quantity) AS qty
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        JOIN bills b ON b.order_id = o.id
        JOIN menu_items m ON m.id = oi.item_id
        WHERE o.status = 'billed'
          AND date(b.paid_at) >= DATE_SUB(CURDATE(), INTERVAL ? DAY)
        GROUP BY m.id, m.name ORDER BY qty DESC, m.name LIMIT ?""",
                 (days - 1, limit))


def payment_split(days=30):
    return _rows("""
        SELECT payment_mode, SUM(total) AS amount, COUNT(*) AS n
        FROM bills WHERE date(paid_at) >= DATE_SUB(CURDATE(), INTERVAL ? DAY)
        GROUP BY payment_mode ORDER BY amount DESC""", (days - 1,))


def suggestions(item_ids, limit=2):
    """Items most often ordered together with the ones already on the order."""
    if not item_ids:
        return []
    marks = ",".join("?" * len(item_ids))
    return _rows(f"""
        SELECT m.id, m.name, m.price, COUNT(*) AS freq
        FROM order_items a
        JOIN order_items b ON b.order_id = a.order_id AND b.item_id != a.item_id
        JOIN orders o ON o.id = a.order_id AND o.status = 'billed'
        JOIN menu_items m ON m.id = b.item_id
        WHERE a.item_id IN ({marks}) AND b.item_id NOT IN ({marks})
          AND m.available = 1 AND m.stock > 0
        GROUP BY m.id, m.name, m.price ORDER BY freq DESC, m.name LIMIT ?""",
                 list(item_ids) + list(item_ids) + [limit])


# ------------------------------------------------------ menu management
def get_menu_admin(category_id=None, text=""):
    """Every item (hidden ones too) for the Menu Manager."""
    sql = """SELECT m.id, m.name, m.category_id, c.name AS category,
                    m.price, m.stock, m.available
             FROM menu_items m JOIN categories c ON c.id = m.category_id
             WHERE 1 = 1"""
    params = []
    if category_id is not None:
        sql += " AND m.category_id = ?"
        params.append(category_id)
    if text:
        sql += " AND m.name LIKE ?"
        params.append(f"%{text}%")
    return _rows(sql + " ORDER BY c.id, m.name", params)


def menu_name_exists(name, exclude_id=None):
    row = _row("SELECT id FROM menu_items WHERE LOWER(name) = LOWER(?) "
               "AND id != ?", (name, exclude_id if exclude_id else -1))
    return row is not None


def add_menu_item(name, category_id, price, stock):
    conn = get_connection()
    try:
        with conn:
            return conn.execute(
                "INSERT INTO menu_items (name, category_id, price, stock) "
                "VALUES (?, ?, ?, ?)", (name, category_id, price, stock)
            ).lastrowid
    finally:
        conn.close()


def update_menu_item(item_id, name, category_id, price, stock, available):
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE menu_items SET name = ?, category_id = ?, price = ?, "
                "stock = ?, available = ? WHERE id = ?",
                (name, category_id, price, stock, int(available), item_id))
    finally:
        conn.close()


def delete_menu_item(item_id):
    """Delete an item. If it appears on old bills it is hidden instead.

    Returns 'deleted' or 'hidden'.
    """
    conn = get_connection()
    try:
        with conn:
            try:
                conn.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
                return "deleted"
            except IntegrityError:
                conn.execute("UPDATE menu_items SET available = 0 "
                             "WHERE id = ?", (item_id,))
                return "hidden"
    finally:
        conn.close()


def add_category(name):
    conn = get_connection()
    try:
        with conn:
            return conn.execute("INSERT INTO categories (name) VALUES (?)",
                                (name,)).lastrowid
    finally:
        conn.close()


def rename_category(category_id, name):
    conn = get_connection()
    try:
        with conn:
            conn.execute("UPDATE categories SET name = ? WHERE id = ?",
                         (name, category_id))
    finally:
        conn.close()


def count_items_in_category(category_id):
    return _row("SELECT COUNT(*) AS n FROM menu_items WHERE category_id = ?",
                (category_id,))["n"]


def delete_category(category_id):
    conn = get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    finally:
        conn.close()


# ------------------------------------------------------------------ staff
def get_users():
    return _rows("SELECT id, username, full_name, role, active FROM users "
                 "ORDER BY role, username")


def username_exists(username):
    return _row("SELECT id FROM users WHERE LOWER(username) = LOWER(?)",
                (username,)) is not None


def add_user(username, full_name, password_hash, role):
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO users (username, full_name, password_hash, role) "
                "VALUES (?, ?, ?, ?)", (username, full_name, password_hash, role))
    finally:
        conn.close()


def update_user(user_id, full_name, role, active):
    conn = get_connection()
    try:
        with conn:
            conn.execute("UPDATE users SET full_name = ?, role = ?, active = ? "
                         "WHERE id = ?", (full_name, role, int(active), user_id))
    finally:
        conn.close()


def set_password(user_id, password_hash):
    conn = get_connection()
    try:
        with conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                         (password_hash, user_id))
    finally:
        conn.close()


def count_active_admins(exclude_id=None):
    return _row("SELECT COUNT(*) AS n FROM users WHERE role = 'admin' "
                "AND active = 1 AND id != ?",
                (exclude_id if exclude_id else -1,))["n"]


# ---------------------------------------------------------------- reports
def get_bills(date_from, date_to, mode=None):
    sql = """
        SELECT b.id, b.invoice_no, b.paid_at, t.table_no,
               u.full_name AS staff, b.payment_mode,
               b.subtotal, b.discount, b.gst, b.total
        FROM bills b
        JOIN orders o ON o.id = b.order_id
        JOIN tables t ON t.id = o.table_id
        JOIN users u ON u.id = o.user_id
        WHERE date(b.paid_at) BETWEEN ? AND ?"""
    params = [date_from, date_to]
    if mode:
        sql += " AND b.payment_mode = ?"
        params.append(mode)
    return _rows(sql + " ORDER BY b.paid_at DESC, b.id DESC", params)


def report_summary(date_from, date_to, mode=None):
    sql = ("SELECT COALESCE(SUM(total), 0) AS sales, COUNT(*) AS bills, "
           "COALESCE(SUM(discount), 0) AS discount, "
           "COALESCE(SUM(gst), 0) AS gst FROM bills "
           "WHERE date(paid_at) BETWEEN ? AND ?")
    params = [date_from, date_to]
    if mode:
        sql += " AND payment_mode = ?"
        params.append(mode)
    return _row(sql, params)


def items_sold(date_from, date_to):
    return _rows("""
        SELECT m.name, c.name AS category, SUM(oi.quantity) AS qty,
               SUM(oi.quantity * oi.price) AS revenue
        FROM order_items oi
        JOIN bills b ON b.order_id = oi.order_id
        JOIN menu_items m ON m.id = oi.item_id
        JOIN categories c ON c.id = m.category_id
        WHERE date(b.paid_at) BETWEEN ? AND ?
        GROUP BY m.id, m.name, c.name ORDER BY qty DESC, m.name""", (date_from, date_to))


def category_sales(date_from, date_to):
    return _rows("""
        SELECT c.name, SUM(oi.quantity * oi.price) AS revenue
        FROM order_items oi
        JOIN bills b ON b.order_id = oi.order_id
        JOIN menu_items m ON m.id = oi.item_id
        JOIN categories c ON c.id = m.category_id
        WHERE date(b.paid_at) BETWEEN ? AND ?
        GROUP BY c.id ORDER BY revenue DESC""", (date_from, date_to))


def daily_sales(date_from, date_to):
    return _rows("SELECT date(paid_at) AS d, SUM(total) AS s, COUNT(*) AS n "
                 "FROM bills WHERE date(paid_at) BETWEEN ? AND ? "
                 "GROUP BY d ORDER BY d", (date_from, date_to))
