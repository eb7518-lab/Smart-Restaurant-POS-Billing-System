-- Smart Restaurant POS: MySQL schema (the app also creates this automatically)
CREATE DATABASE IF NOT EXISTS smart_pos CHARACTER SET utf8mb4;
USE smart_pos;

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
