"""Global settings for the Smart Restaurant POS."""
import os

APP_NAME = "Smart Restaurant POS"
RESTAURANT_NAME = "Spice Garden"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- MySQL connection (change these to match YOUR MySQL) ----
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = ""            # <-- put your MySQL root password here
MYSQL_DATABASE = "smart_pos"   # created automatically if it does not exist

GST_RATE = 0.05
SERVICE_CHARGE_RATE = 0.0

# Colour theme (used by every screen so the app looks consistent)
COLORS = {
    "primary": "#1F2A44",
    "accent": "#E8590C",
    "bg": "#F4F5F7",
    "card": "#FFFFFF",
    "text": "#222222",
    "muted": "#6B7280",
    "success": "#2F9E44",
    "danger": "#E03131",
}

FONT = "Segoe UI"

# ---- Added in Stage 4 ----
BILLS_DIR = os.path.join(BASE_DIR, "bills")     # printable invoices are saved here
LOW_STOCK_LIMIT = 10                            # items at or below this show as "low"
TAGLINE = "Order faster. Bill smarter."
