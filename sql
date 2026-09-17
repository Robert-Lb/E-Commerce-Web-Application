CREATE DATABASE db_online_store;
USE db_online_store;

CREATE TABLE users (
  id int(11) AUTO_INCREMENT PRIMARY KEY,
  username varchar(100) NOT NULL,
  email varchar(100) NOT NULL,
  password varchar(255) NOT NULL,
  is_admin tinyint(1) DEFAULT 0
);

CREATE TABLE products (
  id int(11) AUTO_INCREMENT PRIMARY KEY,
  name varchar(150) NOT NULL,
  description text,
  price decimal(10,2) NOT NULL,
  stock int(11) NOT NULL,
  image_url varchar(255)
);

CREATE TABLE cart (
  id int(11) AUTO_INCREMENT PRIMARY KEY,
  user_id int(11),
  product_id int(11),
  quantity int(11),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE orders (
  id int(11) AUTO_INCREMENT PRIMARY KEY,
  user_id int(11),
  total_price decimal(10,2),
  status varchar(50) DEFAULT 'Processing',
  created_at timestamp NOT NULL DEFAULT current_timestamp(),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

INSERT INTO users (username, email, password, is_admin) VALUES
(admin, admin@mail.com, admin, 1),
(user, user@mail.com, user, 0);

INSERT INTO products (name, description, price, stock, image_url) VALUES
('Casual Shirt', 'MUFTI Men Relaxed Fit Printed Spread Collar Casual Shirt', 1299.00, 8, 'images/casual-shirt.png'),
('Jacket', 'Bomber Jacket Full Sleeves Winter Wear Men Self Design', 1406.00, 19, 'images/jacket.png'),
('Men\'s T-Shirt', 'Walrus Men Solid Polo Neck Polyester Black T-Shirt', 242.00, 28, 'images/tshirt.png'),
('Formal Shirt', 'RED TAPE Men Relaxed Fit Solid Button Down Collar Formal Shirt', 733.00, 13, 'images/formal-shirt.png'),
('Sweatshirt', 'United Colors of Benetton Men Full Sleeve Solid Hooded Sweatshirt', 1349.00, 24, 'images/sweatshirt.png');



