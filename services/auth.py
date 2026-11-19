"""Login logic and the currently logged-in user."""
from database.db import get_connection
from services.security import verify_password


class Session:
    """Holds the logged-in user for the whole app."""
    user = None

    @classmethod
    def is_admin(cls):
        return cls.user is not None and cls.user["role"] == "admin"

    @classmethod
    def logout(cls):
        cls.user = None


def login(username: str, password: str):
    """Return (True, message) on success, (False, message) otherwise."""
    username = username.strip()
    if not username or not password:
        return False, "Please enter both username and password."

    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND active = 1",
        (username,)).fetchone()
    conn.close()

    if row is None or not verify_password(password, row["password_hash"]):
        return False, "Invalid username or password."

    Session.user = {"id": row["id"], "username": row["username"],
                    "full_name": row["full_name"], "role": row["role"]}
    return True, f"Welcome, {row['full_name']}!"
