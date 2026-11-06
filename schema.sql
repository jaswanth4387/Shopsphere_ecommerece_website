-- ShopSphere schema (MySQL 8). Safe to run more than once.
-- Run with:  python init_db.py        (uses the DB_* values from .env / environment)

CREATE TABLE IF NOT EXISTS `userdata` (
  `userid` binary(16) NOT NULL,
  `username` varchar(50) NOT NULL,
  `useremail` varchar(50) NOT NULL,
  `userpassword` varbinary(255) DEFAULT NULL,
  `useraddress` tinytext,
  `usergender` enum('Male','Female','Others') DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `userphone` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`userid`),
  UNIQUE KEY `useremail` (`useremail`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `admindata` (
  `adminid` binary(16) NOT NULL,
  `admin_username` varchar(50) NOT NULL,
  `admin_useremail` varchar(50) NOT NULL,
  `admin_password` varbinary(255) DEFAULT NULL,
  `admin_address` tinytext,
  `admin_agree` enum('on','off') DEFAULT NULL,
  `admin_phone` varchar(10) DEFAULT NULL,
  `adminimg` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`adminid`),
  UNIQUE KEY `admin_username` (`admin_username`),
  UNIQUE KEY `admin_useremail` (`admin_useremail`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `items` (
  `itemid` binary(16) NOT NULL,
  `item_name` varchar(255) DEFAULT NULL,
  `item_description` longtext,
  `item_about` longtext,
  `item_price` decimal(10,4) DEFAULT NULL,
  `item_quantity` int unsigned DEFAULT NULL,
  `item_category` enum('Home_Appliences','grocery','fashion','electronics','toys','sports') DEFAULT NULL,
  `item_filename` varchar(255) DEFAULT NULL,
  `added_by` binary(16) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`itemid`),
  UNIQUE KEY `item_filename` (`item_filename`),
  KEY `added_by` (`added_by`),
  CONSTRAINT `items_ibfk_1` FOREIGN KEY (`added_by`) REFERENCES `admindata` (`adminid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `cart` (
  `cartid` binary(16) NOT NULL,
  `userid` binary(16) NOT NULL,
  `itemid` binary(16) NOT NULL,
  `quantity` int unsigned DEFAULT '1',
  `added_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`cartid`),
  UNIQUE KEY `user_item` (`userid`,`itemid`),
  KEY `itemid` (`itemid`),
  CONSTRAINT `cart_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `userdata` (`userid`),
  CONSTRAINT `cart_ibfk_2` FOREIGN KEY (`itemid`) REFERENCES `items` (`itemid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `orders` (
  `orderid` binary(16) NOT NULL,
  `userid` binary(16) NOT NULL,
  `razorpay_order_id` varchar(100) DEFAULT NULL,
  `razorpay_payment_id` varchar(100) DEFAULT NULL,
  `total_amount` decimal(10,2) DEFAULT NULL,
  `payment_status` enum('Pending','Paid','Failed') DEFAULT 'Pending',
  `order_status` enum('Placed','Packed','Shipped','Delivered','Cancelled') DEFAULT 'Placed',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`orderid`),
  KEY `userid` (`userid`),
  KEY `razorpay_order_id` (`razorpay_order_id`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `userdata` (`userid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `order_items` (
  `orderitemid` binary(16) NOT NULL,
  `orderid` binary(16) DEFAULT NULL,
  `itemid` binary(16) DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`orderitemid`),
  KEY `orderid` (`orderid`),
  KEY `itemid` (`itemid`),
  CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`orderid`) REFERENCES `orders` (`orderid`) ON DELETE CASCADE,
  CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`itemid`) REFERENCES `items` (`itemid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `item_reviews` (
  `reviewid` int unsigned NOT NULL AUTO_INCREMENT,
  `review_text` longtext,
  `review_image` varchar(255) DEFAULT NULL,
  `verified_purchase` tinyint(1) DEFAULT '0',
  `helpful_count` int unsigned DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `rating` tinyint unsigned NOT NULL,
  `review_title` varchar(100) DEFAULT NULL,
  `itemid` binary(16) DEFAULT NULL,
  `userid` binary(16) DEFAULT NULL,
  PRIMARY KEY (`reviewid`),
  UNIQUE KEY `unique_review` (`userid`,`itemid`),
  KEY `itemid` (`itemid`),
  CONSTRAINT `item_reviews_ibfk_1` FOREIGN KEY (`itemid`) REFERENCES `items` (`itemid`),
  CONSTRAINT `item_reviews_ibfk_2` FOREIGN KEY (`userid`) REFERENCES `userdata` (`userid`),
  CONSTRAINT `chk_rating` CHECK ((`rating` between 1 and 5))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `review_helpful` (
  `reviewid` int unsigned NOT NULL,
  `userid` binary(16) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`reviewid`,`userid`),
  KEY `userid` (`userid`),
  CONSTRAINT `review_helpful_ibfk_1` FOREIGN KEY (`reviewid`) REFERENCES `item_reviews` (`reviewid`) ON DELETE CASCADE,
  CONSTRAINT `review_helpful_ibfk_2` FOREIGN KEY (`userid`) REFERENCES `userdata` (`userid`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
