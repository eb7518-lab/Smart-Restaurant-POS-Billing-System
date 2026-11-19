"""Rules for adding and managing staff accounts (no UI code here)."""
import re

from database import queries
from services.security import hash_password

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
ROLES = ("admin", "cashier")


def _check_password(password):
    if len(password) < 6:
        return "Password must be at least 6 characters."
    return None


def add_staff(username, full_name, password, role):
    username = username.strip()
    full_name = " ".join(full_name.split())
    if not USERNAME_RE.match(username):
        return False, "Username must be 3-20 letters, digits or underscores."
    if not full_name:
        return False, "Full name is required."
    if role not in ROLES:
        return False, "Choose a role."
    error = _check_password(password)
    if error:
        return False, error
    if queries.username_exists(username):
        return False, f"The username '{username}' is already taken."
    queries.add_user(username, full_name, hash_password(password), role)
    return True, f"Added {full_name} ({role})."


def update_staff(user_id, full_name, role, active, acting_user_id):
    full_name = " ".join(full_name.split())
    if not full_name:
        return False, "Full name is required."
    if role not in ROLES:
        return False, "Choose a role."
    if user_id == acting_user_id and not active:
        return False, "You cannot deactivate your own account."
    users = {u["id"]: u for u in queries.get_users()}
    current = users.get(user_id)
    if current is None:
        return False, "That account no longer exists."
    losing_admin = current["role"] == "admin" and current["active"] and \
        (role != "admin" or not active)
    if losing_admin and queries.count_active_admins(exclude_id=user_id) == 0:
        return False, "There must be at least one active admin."
    queries.update_user(user_id, full_name, role, active)
    return True, "Saved changes."


def reset_password(user_id, password):
    error = _check_password(password)
    if error:
        return False, error
    queries.set_password(user_id, hash_password(password))
    return True, "Password updated."
