"""Validation + saving for the Menu Manager (no UI code here)."""
from database import queries


def save_item(item_id, name, category_id, price_text, stock_text, available):
    """Add (item_id is None) or update an item. Returns (ok, message)."""
    name = " ".join(name.split())
    if not name:
        return False, "Item name is required."
    if len(name) > 40:
        return False, "Item name must be 40 characters or fewer."
    if category_id is None:
        return False, "Choose a category."
    try:
        price = round(float(price_text), 2)
    except ValueError:
        return False, "Price must be a number."
    if not 0 < price <= 100000:
        return False, "Price must be more than 0 and at most 1,00,000."
    try:
        stock = int(stock_text)
    except ValueError:
        return False, "Stock must be a whole number."
    if not 0 <= stock <= 100000:
        return False, "Stock must be between 0 and 1,00,000."
    if queries.menu_name_exists(name, item_id):
        return False, f"'{name}' is already on the menu."

    if item_id is None:
        queries.add_menu_item(name, category_id, price, stock)
        return True, f"Added '{name}'."
    queries.update_menu_item(item_id, name, category_id, price, stock, available)
    return True, f"Saved changes to '{name}'."


def save_category(category_id, name):
    """Add (category_id None) or rename a category. Returns (ok, message)."""
    name = " ".join(name.split())
    if not name:
        return False, "Category name is required."
    if len(name) > 30:
        return False, "Category name must be 30 characters or fewer."
    try:
        if category_id is None:
            queries.add_category(name)
            return True, f"Added category '{name}'."
        queries.rename_category(category_id, name)
        return True, f"Renamed to '{name}'."
    except Exception:           # UNIQUE constraint: name already used
        return False, f"A category called '{name}' already exists."


def remove_category(category_id):
    if queries.count_items_in_category(category_id) > 0:
        return False, "Move or delete the items in this category first."
    queries.delete_category(category_id)
    return True, "Category deleted."
