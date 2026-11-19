# Smart Restaurant POS & Billing System

A **Python Tkinter-based desktop application** designed to simplify restaurant operations through an interactive graphical user interface.

The application provides an easy-to-use interface for restaurant staff to manage tables, take orders, generate bills, manage menus and monitor restaurant activities. It uses **MySQL** for backend data storage.

## Student Details

| Field | Details |
|---|---|
| Name | Eshita Biswas |
| Registration Number | RA2511003012357 |
| Project Title | Smart Restaurant POS & Billing System |

---

# 1. Project Overview

The Smart Restaurant POS & Billing System is a desktop GUI application developed using **Python and Tkinter**.

The main objective is to provide a simple, interactive and user-friendly interface through which restaurant staff can perform daily activities without manually managing orders and calculations.

The application uses Tkinter widgets such as buttons, labels, frames, entry fields, tables and dialog boxes to create an interactive restaurant management system.

MySQL is integrated to store user accounts, menu information, orders, bills and other application data.

# 2. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Tkinter | Graphical User Interface (GUI) development |
| ttk | Enhanced GUI widgets and tables |
| MySQL | Backend database management |
| mysql.connector | Python–MySQL connectivity |
| Matplotlib / Tkinter Canvas | Dashboard charts and visualizations |
| HTML | Printable invoice generation |
| CSV | Report export |

# 3. Graphical User Interface Features

The main focus of this project is its interactive Tkinter-based interface.

### Login Screen
- User-friendly login window.
- Admin and Cashier authentication.
- Password-protected access.
- Role-based navigation.

### Dashboard
- Displays restaurant activity and sales information.
- Interactive dashboard cards.
- Sales charts and visual statistics.
- Low-stock notifications.
- Demo data loading option.

### Table Management
- Displays restaurant tables in a visual grid.
- Shows Free, Occupied and Billing status.
- Includes a time-seated timer.
- Allows staff to select tables and manage orders.

### Order Management
- Interactive menu display.
- Category filters and search functionality.
- Add and manage food items.
- Quantity and stock validation.
- Smart food recommendations.

### Billing Screen
- Automatic bill calculation.
- Discount application.
- GST calculation.
- Cash, Card and UPI payment options.
- Automatic round-off and cash change calculation.

### Receipt Window
- Displays generated invoices.
- Printable HTML receipts.
- Option to print or save invoices as PDF.
- Invoice reprinting.

### Menu Management
- Add new food items.
- Edit existing dishes.
- Manage categories.
- Update prices and stock.
- Hide or delete menu items.

### Staff Management
- Create staff accounts.
- Assign Admin and Cashier roles.
- Reset passwords.
- Enable or disable accounts.

### Reports Screen
- Date-range sales reports.
- Daily sales information.
- Best-selling items.
- Payment statistics.
- CSV report export.

# 4. Main Tkinter Components Used

| Tkinter Component | Usage |
|---|---|
| `Tk()` | Creates the main application window |
| `Frame` | Organizes different sections of the interface |
| `Label` | Displays text and headings |
| `Button` | Performs actions when clicked |
| `Entry` | Accepts user input |
| `ttk.Treeview` | Displays tabular information |
| `ttk.Combobox` | Provides dropdown selections |
| `messagebox` | Displays alerts and confirmation messages |
| `Canvas` | Creates graphical dashboard elements |
| `Toplevel` | Creates additional windows and dialogs |

# 5. Application Screens

The application is divided into multiple screens to make navigation and management easier.

1. Login Screen
2. Dashboard
3. Table Management
4. Order Management
5. Billing Screen
6. Receipt Window
7. Menu Manager
8. Staff Management
9. Reports Screen

Each screen is designed for a specific restaurant operation, making the application easier to understand and use.

# 6. Project Structure

```text
smart_pos_mysql/
│
├── main.py
├── config.py
├── check_mysql.py
├── requirements.txt
├── run_app.bat
├── schema.sql
│
├── database/
│   ├── __init__.py
│   ├── db.py
│   └── queries.py
│
├── services/
│   ├── __init__.py
│   ├── auth.py
│   ├── security.py
│   ├── billing.py
│   ├── receipt.py
│   ├── menu_service.py
│   ├── staff_service.py
│   ├── export.py
│   └── demo_data.py
│
└── ui/
    ├── __init__.py
    ├── login_screen.py
    ├── dashboard.py
    ├── tables_screen.py
    ├── order_screen.py
    ├── billing_screen.py
    ├── receipt_window.py
    ├── menu_manager.py
    ├── staff_screen.py
    ├── reports_screen.py
    ├── orders_list.py
    ├── charts.py
    └── widgets.py
```

### Explanation of Directories

- **main.py:** Entry point of the application.
- **config.py:** Stores application settings and configurations.
- **ui/:** Contains Tkinter screens, widgets and GUI components.
- **services/:** Handles application logic such as authentication, billing and menu management.
- **database/:** Handles MySQL connectivity and database queries.

# 7. Backend Database (MySQL)

MySQL is used to store and retrieve application information.

The application uses seven main tables:

| Table | Purpose |
|---|---|
| users | Stores user accounts and roles |
| categories | Stores menu categories |
| menu_items | Stores food items, prices and stock |
| tables | Stores restaurant table information |
| orders | Stores customer orders |
| order_items | Stores individual order details |
| bills | Stores billing and payment information |

The database supports the Tkinter application by maintaining information between operations.

# 8. How to Run the Project

### Requirements
- Python 3.10 or newer.
- MySQL Server.
- Visual Studio Code or another Python IDE.

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure MySQL

Open `config.py` and enter your MySQL credentials:

```python
MYSQL_USER = "root"
MYSQL_PASSWORD = "your password"
```

### Step 3: Check Database Connection

```bash
python check_mysql.py
```

### Step 4: Run the Application

```bash
python main.py
```

Alternatively, double-click `run_app.bat` on Windows.

The database and required tables are initialized automatically when the application starts.

# 9. Demo Login Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Cashier | `cashier` | `cash123` |

These are demonstration credentials. Change them before real-world use.

# 10. Suggested Project Demonstration

1. Open the application and demonstrate the login screen.
2. Log in as Admin and explore the dashboard.
3. Demonstrate restaurant table management.
4. Select a table and add food items through the order screen.
5. Demonstrate Kitchen Order Tickets (KOT).
6. Generate a bill and demonstrate payment options.
7. Display and print the generated receipt.
8. Demonstrate menu and staff management.
9. Open the reports screen and export a CSV report.

# 11. Design and Implementation

- **GUI-based design:** Tkinter is used to develop the application's interactive desktop interface.
- **Modular structure:** Different screens and functionalities are maintained in separate Python files.
- **Event-driven programming:** Buttons, forms and other widgets respond to user actions through event handlers.
- **Backend integration:** MySQL stores and manages application data.
- **Security:** Passwords are protected using salted PBKDF2 hashing.
- **Billing automation:** The application calculates totals, discounts and taxes automatically.

# 12. Future Enhancements

- Improved GUI animations and visual effects.
- Online food ordering integration.
- Cloud-based database connectivity.
- Mobile application support.
- Multi-branch restaurant management.
- Online payment gateway integration.

---

**Developed using Python, Tkinter and MySQL.**