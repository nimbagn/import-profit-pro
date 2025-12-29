-- scripts/mysql_init.sql
CREATE DATABASE IF NOT EXISTS madargn CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'madar'@'localhost' IDENTIFIED BY 'Satina2025';
GRANT ALL PRIVILEGES ON madargn.* TO 'madar'@'localhost';
FLUSH PRIVILEGES;
