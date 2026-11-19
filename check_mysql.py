"""Run this first:  python check_mysql.py
It tells you whether Python can reach your MySQL server."""
import config

try:
    import mysql.connector
except ImportError:
    print("The MySQL connector is not installed.")
    print("Fix:  pip install mysql-connector-python")
    raise SystemExit

try:
    conn = mysql.connector.connect(
        host=config.MYSQL_HOST, port=config.MYSQL_PORT,
        user=config.MYSQL_USER, password=config.MYSQL_PASSWORD)
    print("Connected to MySQL server version", conn.get_server_info())
    print("Good! Now run:  python main.py")
    conn.close()
except Exception as err:
    print("Could not connect to MySQL:", err)
    print("Check that MySQL is running and that MYSQL_USER / MYSQL_PASSWORD")
    print("in config.py are the same ones you use in MySQL Workbench.")
