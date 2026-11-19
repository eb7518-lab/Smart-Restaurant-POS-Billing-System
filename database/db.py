"""MySQL connection, table creation and sample data.

The rest of the app talks to this small wrapper, which behaves like a simple
database object: conn.execute(sql, params) with ? placeholders, rows that can
be read by column name, and `with conn:` to commit or roll back.
"""
from datetime import date, datetime
from decimal import Decimal

import mysql.connector
from mysql.connector import IntegrityError   # re-exported for queries.py

import config
from services.security import hash_password


def _clean(value):
    """Turn MySQL types into the plain Python types the screens expect."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.decode()
    return value


class Row(dict):
    """A result row: row["name"] or row[0] both work."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class Cursor:
    def __init__(self, cur):
        self._cur = cur
        self.lastrowid = cur.lastrowid
        self.rowcount = cur.rowcount

    def _row(self, raw):
        return None if raw is None else Row((k, _clean(v)) for k, v in raw.items())

    def fetchone(self):
        return self._row(self._cur.fetchone())

    def fetchall(self):
        return [self._row(r) for r in self._cur.fetchall()]

    def __iter__(self):
        return iter(self.fetchall())


class Connection:
    def __init__(self, raw):
        self._raw = raw

    @staticmethod
    def _convert(sql):
        # a literal % must be doubled when parameters are used
        return sql.replace("%", "%%").replace("?", "%s")

    def execute(self, sql, params=()):
        cur = self._raw.cursor(dictionary=True, buffered=True)
        if params:
            cur.execute(self._convert(sql), tuple(params))
        else:
            cur.execute(sql)
        return Cursor(cur)

    def executemany(self, sql, seq):
        rows = [tuple(r) for r in seq]
        cur = self._raw.cursor()
        if rows:
            cur.executemany(self._convert(sql), rows)
        return Cursor(cur)

    def executescript(self, script):
        cur = self._raw.cursor()
        for statement in script.split(";"):
            if statement.strip():
                cur.execute(statement)

    def commit(self):
        self._raw.commit()

    def close(self):
        self._raw.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self._raw.commit()
        else:
            self._raw.rollback()
        return False


def get_connection():
    raw = mysql.connector.connect(
        host=config.MYSQL_HOST, port=config.MYSQL_PORT,
        user=config.MYSQL_USER, password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE, charset="utf8mb4")
    return Connection(raw)


def ensure_database():
    """Create the MySQL database itself if it is missing."""
    raw = mysql.connector.connect(
        host=config.MYSQL_HOST, port=config.MYSQL_PORT,
        user=config.MYSQL_USER, password=config.MYSQL_PASSWORD)
    cur = raw.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DATABASE}` "
                f"CHARACTER SET utf8mb4")
    raw.commit()
    raw.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(60) NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    role VARCHAR(10) NOT NULL,
    active TINYINT NOT NULL DEFAULT 1,
    CHECK (role IN ('admin', 'cashier'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS menu_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(60) NOT NULL,
    category_id INT NOT NULL,
    price DOUBLE NOT NULL,
    available TINYINT NOT NULL DEFAULT 1,
    stock INT NOT NULL DEFAULT 100,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    CHECK (price >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tables (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_no INT NOT NULL UNIQUE,
    capacity INT NOT NULL DEFAULT 4,
    status VARCHAR(10) NOT NULL DEFAULT 'free',
    CHECK (status IN ('free', 'occupied', 'billing'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_id INT NOT NULL,
    user_id INT NOT NULL,
    status VARCHAR(12) NOT NULL DEFAULT 'open',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (table_id) REFERENCES tables(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    CHECK (status IN ('open', 'held', 'billed', 'cancelled'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    price DOUBLE NOT NULL,
    kot_qty INT NOT NULL DEFAULT 0,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES menu_items(id),
    CHECK (quantity > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    invoice_no VARCHAR(40) NOT NULL UNIQUE,
    subtotal DOUBLE NOT NULL,
    gst DOUBLE NOT NULL,
    discount DOUBLE NOT NULL DEFAULT 0,
    total DOUBLE NOT NULL,
    payment_mode VARCHAR(10) NOT NULL,
    paid_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
) ENGINE=InnoDB;
"""

SAMPLE_MENU = {
    "Starters": [("Paneer Tikka", 220), ("Veg Spring Rolls", 160),
                 ("Chicken 65", 240), ("Hara Bhara Kebab", 180)],
    "Main Course": [("Butter Chicken", 320), ("Paneer Butter Masala", 280),
                    ("Dal Tadka", 180), ("Veg Biryani", 230),
                    ("Chicken Biryani", 290), ("Mixed Veg Curry", 200)],
    "Breads": [("Butter Naan", 45), ("Tandoori Roti", 25), ("Garlic Naan", 55)],
    "Drinks": [("Masala Chai", 40), ("Cold Coffee", 110),
               ("Fresh Lime Soda", 70), ("Mango Lassi", 90)],
    "Desserts": [("Gulab Jamun", 80), ("Ice Cream", 90), ("Brownie", 120)],
}


def init_db():
    """Create the database, tables and sample data on the first run."""
    ensure_database()
    conn = get_connection()
    conn.executescript(SCHEMA)


    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO users (username, full_name, password_hash, role) "
            "VALUES (?, ?, ?, ?)",
            ("admin", "Administrator", hash_password("admin123"), "admin"))
        conn.execute(
            "INSERT INTO users (username, full_name, password_hash, role) "
            "VALUES (?, ?, ?, ?)",
            ("cashier", "Front Desk", hash_password("cash123"), "cashier"))

    if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        for cat, items in SAMPLE_MENU.items():
            cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
            for name, price in items:
                conn.execute(
                    "INSERT INTO menu_items (name, category_id, price) "
                    "VALUES (?, ?, ?)", (name, cur.lastrowid, price))

    if conn.execute("SELECT COUNT(*) FROM tables").fetchone()[0] == 0:
        for n in range(1, 13):
            conn.execute("INSERT INTO tables (table_no, capacity) VALUES (?, ?)",
                         (n, 2 if n <= 4 else 4 if n <= 10 else 6))

    conn.commit()
    conn.close()
