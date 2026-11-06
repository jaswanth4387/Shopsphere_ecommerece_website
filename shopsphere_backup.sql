-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: shopsphere
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admindata`
--

DROP TABLE IF EXISTS `admindata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admindata` (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admindata`
--

LOCK TABLES `admindata` WRITE;
/*!40000 ALTER TABLE `admindata` DISABLE KEYS */;
INSERT INTO `admindata` VALUES (_binary '\ˆo\‡5ÇN©°ZÆ{¡Ω≈å','Jakkampudi_Jaswanth_Krishna','jaswanthjakkampudi438@gmail.com',_binary '$2b$12$kjtzsMoRzsXAnHVRZMgJjuobdjPK/S1mQsVVe4KJBkZErym4JgM3u','KUPPENAKUNTLA, PENUBALLI,',NULL,NULL,NULL);
/*!40000 ALTER TABLE `admindata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cart`
--

DROP TABLE IF EXISTS `cart`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cart` (
  `cartid` binary(16) NOT NULL,
  `userid` binary(16) NOT NULL,
  `itemid` binary(16) NOT NULL,
  `quantity` int unsigned DEFAULT '1',
  `added_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`cartid`),
  KEY `userid` (`userid`),
  KEY `itemid` (`itemid`),
  CONSTRAINT `cart_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `userdata` (`userid`),
  CONSTRAINT `cart_ibfk_2` FOREIGN KEY (`itemid`) REFERENCES `items` (`itemid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cart`
--

LOCK TABLES `cart` WRITE;
/*!40000 ALTER TABLE `cart` DISABLE KEYS */;
INSERT INTO `cart` VALUES (_binary 'ô\ƒGnE•O¬±3k∑;\È\÷',_binary '∫\ˆc\È\∆LE\Âè\"\Ï$˙3©\‡',_binary '∑W§´ªG1¥åA%˚{',1,'2026-06-30 16:43:47');
/*!40000 ALTER TABLE `cart` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `item_reviews`
--

DROP TABLE IF EXISTS `item_reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `item_reviews` (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `item_reviews`
--

LOCK TABLES `item_reviews` WRITE;
/*!40000 ALTER TABLE `item_reviews` DISABLE KEYS */;
/*!40000 ALTER TABLE `item_reviews` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `items`
--

DROP TABLE IF EXISTS `items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `items` (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `items`
--

LOCK TABLES `items` WRITE;
/*!40000 ALTER TABLE `items` DISABLE KEYS */;
INSERT INTO `items` VALUES (_binary '(¢\Ò=lJ\ÍÜy¥où\ﬁ\Ò∂','amazon basics Rubber Encased Hex Dumbbell','amazon basics Rubber Encased Hex Dumbbell Weight Set Of 2, 5 Kg,Black','Dumbbell for resistance training‚Äîgreat for arms, chest, back, core, and legs\r\nMild Steel core for reliable strength; will not bend or break after repeated use\r\nHexagon-shaped rubber-encased ends help prevent rolling and promote stay-in-place storage\r\n',5.0000,10,'sports','31fxA4Y5F9L._SY300_SX300_QL70_FMwebp_.webp',NULL,'2026-06-18 12:58:06'),(_binary '=˚N[á¿E/ØÄü? \·ê\¬','Samsung Galaxy Watch6 Classic (Black, 43mm) ','Samsung Galaxy Watch6 Classic (Black, 43mm) | Rotating Bezel | LTE | Monitor BP and ECG | Track Sleep | Track Health | Upto 40hrs Charge with Fast Charging | Galaxy Ecosystem | IP68 Rating','Introducing BP & ECG on Galaxy Watch : Keep a track of your well-being by monitoring and tracking your blood pressure & ECG easily and more conveniently, right on your wrist.\r\nIntroducing Contactless Secure Payments : make payments from your wrist with a simple Tap & Pay feature enabled by Samsung Wallet\r\nFreedom with LTE : Stay connected with your world even when you leave your phone behind. Enjoy seamless access to calls, messages, music streaming & much more on the go.',2.0000,5,'electronics','71sRBqqrOpL._SX522_.jpg',NULL,'2026-06-17 11:53:08'),(_binary 'B\’\n8â\0C“°˚^Ñ6B','iD Peri Peri Parota','iD Peri Peri Parota, 160g\r\n','1. Classic peri-peri notes infused for the rich spicy note 2. Soft & flaky texture 3.No added colours or artificial flavours 4. No preservatives or chemicals\r\nBrand: ID',4.0000,50,'grocery','51QW77FGgOL.jpg',NULL,'2026-06-17 12:12:22'),(_binary 'GÖ|€•`IK∏™\Ô\ÀLO\¬','Lifelong Fit Pro Spin Fitness Bike','Lifelong Fit Pro Spin Fitness Bike with 7Kg Flywheel, Adjustable Resistance & Heart Rate Sensor for Fitness at Home Workouts|Max Weight Capacity: 120 kg (LLSBB50, Black)','Warranty: 1 year\r\nSturdy Flywheel- The 6kg flywheel is designed to maintain momentum smoothly as you cycle on the cardio machine. Heavy flywheels support speed, stability, and consistency across your workout.\r\nFoam Grip Handle with heart rate- FitPro Spin Bike comes with a heart rate sensor to help you measure your heart rate during a heavy workout session. The Handle grip is smooth and made with Foam for easy grip.',5.0000,10,'sports','7181tSL0awL._SX679_.jpg',NULL,'2026-06-18 12:55:37'),(_binary 'o0\⁄bäJ’îI I_çg¶','BULLMER Trendy Printed Cotton','BULLMER Trendy Printed Cotton Blend Crew Neck/Round Neck Half Sleeve Tshirt for Men - Pack of 3','Best Value\r\nBULLMER Trendy Printed Tshirts is the perfect choice for Men\r\nBULLMER premium quality cotton blended Tshirts makes you feel easier',3.0000,50,'fashion','61D2GVIp-RL._SY741_.jpg',NULL,'2026-06-17 12:00:24'),(_binary 'Ç4ë9§6DPü_ì8õ6í','Storio Rechargeable Wireless Mini Portable Bluetooth Karaoke Machine','Storio Rechargeable Wireless Mini Portable Bluetooth Karaoke Machine | Bluetooth Speaker with Microphone & LED Lights - Kids Music Singing Toys for Girl Boy Birthday Gift Ideas','‚ô™„Äê2024 New Karaoke Machine For Kids„Äë- This mini karaoke machine for kids is compact and super lightweight,easy to press buttons,All you need is a make stage to show your kids own karaoke party.Popular kids toys for girls age 5-6,girls toys 8-10,toys for girls 5-7.\r\n‚ô™„ÄêTop Sound Quality & Longer Use Time„Äë- This professional bluetooth karaoke speaker equipped with the best acoustic speaker for high volume and quality sound.Rechargeable battery provide 5-6 hours continuous use to keep your party going.',7.0000,5,'toys','41jtLbueYpL._SY300_SX300_QL70_FMwebp_.webp',NULL,'2026-06-18 13:08:37'),(_binary 'Éß˛…∂êE¨E˛uΩ¯ï','VESCO 24 T Drift Cycle','VESCO 24 T Drift Cycle for Big Kids MTB Mountain Bike | Dual Disk Brake & Front Suspension Single Speed Bicycle for Boys and Girls | 16 inches Frame | Ideal for 9-14 Years (Grey)','üö≤ Assembly Instructions: Vesco cycles Delivered Bicycle in Semi-Assembled Condition (85% Assembled) [Customer Needs to Assemble it Before use Allen Key & Spanner Provided in Box For Installation]\r\nüö≤ Tire Size: 24*2.40 (24 Inch) | Frame Size: 16 Inch | Brake Style: Dual Disk Brake | Speed: Single Speed',2.0000,40,'sports','81KIQbIm6uL._AC_UL480_QL65_.jpg',NULL,'2026-06-18 12:54:17'),(_binary 'äûµîICüûbè\È\‡\’?','TAGDO¬Æ Men\'s Solid Cotton Shorts','TAGDO¬Æ Men\'s Solid Cotton Shorts | Shorts Pant for Men | Shorts for Men (2003)','00% cotton construction for breathability and comfort\r\nBreathable and lightweight material ideal for warm weather\r\nClassic design suitable for casual and sporty outfits',4.0000,7,'fashion','51omwAmZGNL._SY879_.jpg',NULL,'2026-06-17 12:07:50'),(_binary 'ó\ˆâ„ï™M¥°L\¢úL0C','Samsung Galaxy Tab A11+','Samsung Galaxy Tab A11+, 27.82 cm (11 inch) Display, 6 GB RAM, 128 GB Storage, 90Hz Refresh Rate, AI with Google Gemini, Dolby Atmos, Quad Speakers, Wi-Fi + 5G Tablet, Gray','POWERFUL PERFORMANCE FOR MULTI-TASKING: 4nm Processor with 18% higher performance than previous model\r\n\r\nLEAD WITH AI : Experience Google Gemini and Circle to Search on your tab\r\n\r\nENTERTAINMENT POWERHOUSE: 90Hz Display and Quad speaker with Dolby Atmos\r\n',2.0000,10,'electronics','315JykS-kaL._SY300_SX300_QL70_FMwebp_.webp',NULL,'2026-06-17 11:46:45'),(_binary '¨#˝REZ¶cµƒèI£˝','ANNI Designer Women\'s Rayon Viscose','ANNI Designer Women\'s Rayon Viscose Straight fit Printed Embroidered Kurta with Pant & Dupatta | Ethnic Kurta Set for Women | Daily, Office & Festive Traditional','üåø Premium Fabric: Made from soft and breathable rayon viscose fabric that feels smooth on the skin and ensures all-day comfort\r\nüëó Straight Fit Design: Elegant straight-cut kurta with attractive ethnic prints, classic neckline, and 3/4th sleeves for a graceful look',2.0000,4,'fashion','61LTMwBMJ3L._SX569_.jpg',NULL,'2026-06-17 11:57:34'),(_binary '≥0ˇ\Ë\ÕDΩã&∂eŒ™N•','Lay\'s Potato Chips','Lay\'s Potato Chips - India\'s Magic Masala, 58g /52.9[(40g+8g EXTRA)+4.9] (Weight may Vary)','BURSTING FLAVOUR: The Lay‚Äôs India‚Äôs Magic Masala spice blend will excite your tastebuds\r\nQUALITY POTATOES: Made from the highest quality, farm-grown potatoes\r\n100% VEGETARIAN: Lay‚Äôs India‚Äôs Magic Masala is a 100% vegetarian snack\r\nPERFECT FOR ANY OCCASSION: A versatile snack that can be enjoyed in ',4.0000,78,'grocery','51dbQvP3BuL._SY300_SX300_QL70_FMwebp_.webp',NULL,'2026-06-17 12:09:40'),(_binary '∑W§´ªG1¥åA%˚{','HP 15, AMD Ryzen 5 7520U','HP 15, AMD Ryzen 5 7520U (8GB LPDDR5, 512GB SSD) Anti-Glare, FHD,15.6\'\'/39.6 cm, Win 11, Office 21, Silver, 1.59kg, fc0155AU, FHD Camera with Privacy Shutter, Backlit KB Laptop','„ÄêAMD Radeon Graphics„Äëmicro-edge; Full-size, backlit, soft grey keyboard with numeric keypad, HP Imagepad; Wi-Fi 6 (1x1) and Bluetooth 5.3 wireless card; 1 USB Type-C 5Gbps signaling rate (supports data transfer only and does not support charging or external monitors); 2 USB Type-A 5Gbps signaling rate; 1 AC smart pin; 1 HDMI 1.4b; 1 headphone/microphone combo',1.0000,50,'electronics','71hoxBTuKL._SX679_.jpg',NULL,'2026-06-17 11:42:41'),(_binary 'ª\ıX|]\¬A…ó>¨\Ë\Œ\„OÜ','Parle G Gluco','Parle G Gluco\r\n','Country of Origin: India\r\nAs its unique taste expanded over the globe\r\nFilled with goodness of wheat and milk',4.0000,5,'grocery','714PuAiIeeL._SX679_.jpg',NULL,'2026-06-17 12:11:29'),(_binary '\»n0HüB˝ó8îZ\Ûf','Crompton SUREBREEZE SEA SAPPHIRA 1200 mm Ceiling Fan for Home','Crompton SUREBREEZE SEA SAPPHIRA 1200 mm Ceiling Fan for Home | BEE Star Rated Energy Efficient Fan | Superior Air Delivery | HighSpeed | 2 Years Warranty | (Lustre Brown), Pack of 1','TECHNICAL SPECIFICATIONS Sweep 1200 mm | Low Power consumption 46 W | Speed 390 RPM | Air delivery 210 CMM\r\nQUALITY COMPONENTS: Double ball bearings, dynamically balanced blades;\r\nPACKAGE CONTENTS: 1 motor, set of 3 blades, set of 2 canopy, 1 down rod, 1 shackle assembly, 1 Safety Cable, 1 product manual along with warranty card',4.0000,78,'Home_Appliences','41yP3DAJAgL._SX679_.jpg',NULL,'2026-06-18 18:15:39'),(_binary 'Œ©º\ÃQ&Djæ\0ÉL¿oO','ToyTastic Magnetic Educational Chess Board Set','ToyTastic Magnetic Educational Chess Board Set with Folding Chess Board 2 Plyaers Travel Toys for Kids and Adults (10 Inch)','‚ôüÔ∏è Foldable Magnetic Chess Game Board Smart folding design transforms into a compact storage box‚Äîkeeps all pieces organized and safe.\r\nüß† Magnetic Chess Game for Brain Development Enhances strategic thinking, concentration, and problem-solving skills for kids and adults.\r\nüëú Portable Magnetic Chess Game Set Lightweight and travel-friendly‚Äîperfect for trips, school, office, and outdoor play.',4.0000,7,'toys','41NLOxg1EL._SX300_SY300_QL70_FMwebp_.webp',NULL,'2026-06-18 18:13:52'),(_binary '\ÿ^-u\0\ÛMôàÿ≥î&ì^	','Amazon Basics 3.5L Electric Air Fryer','Amazon Basics 3.5L Electric Air Fryer | 1200 W | Temp. Settings Up to 200¬∞C | 7 Pre-set Options | 360¬∞ High Speed Air Circulation | Non-Stick Coated | Touch Control Display | 1 Year Warranty (Green)','Durable and Long-lasting: Made from high-quality food-grade polypropylene, the air fryer is lightweight and corrosion-free.\r\nEasy To Handle: The air fryer has cool touch handles for easy handling and carrying.\r\nNon-Stick Coated: The air fryer has a non-stick coating, letting you cook more efficiently with little to no oil and clean more effortlessly.',8.0000,45,'Home_Appliences','31LoiQN5ezL._SY300_SX300_QL70_FMwebp_.webp',NULL,'2026-06-18 18:19:10'),(_binary '\Ô∫L\"õ°MKñ\‹c\À\ı…ª','Eureka Forbes Quick Clean DX Vacuum Cleaner','Eureka Forbes Quick Clean DX Vacuum Cleaner with 1200 Watts Powerful Suction Control, 3 Free Reusable dust Bag Worth Rs 500, Comes with Multiple Accessories, Dust Bag Full Indicator (Red), Standard','Post Purchase virtual Demo is provided on this product .A dedicated customer service executive is assigned to give live demo of the product over a video call\r\nQuick Clean DX is a canister vaccum cleaner for daily cleaning needs to get rid of deep embedded dirt & dust\r\n1200 Watts powerful suction provides deep cleaning',4.0000,50,'Home_Appliences','31RLop3PYIL._SY300_SX300_QL70_FMwebp_.webp',NULL,'2026-06-18 18:16:51');
/*!40000 ALTER TABLE `items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_items`
--

DROP TABLE IF EXISTS `order_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_items` (
  `orderitemid` binary(16) NOT NULL,
  `orderid` binary(16) DEFAULT NULL,
  `itemid` binary(16) DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`orderitemid`),
  KEY `orderid` (`orderid`),
  KEY `itemid` (`itemid`),
  CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`orderid`) REFERENCES `orders` (`orderid`),
  CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`itemid`) REFERENCES `items` (`itemid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_items`
--

LOCK TABLES `order_items` WRITE;
/*!40000 ALTER TABLE `order_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
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
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `userdata` (`userid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `review_helpful`
--

DROP TABLE IF EXISTS `review_helpful`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `review_helpful` (
  `reviewid` int unsigned NOT NULL,
  `userid` binary(16) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`reviewid`,`userid`),
  KEY `userid` (`userid`),
  CONSTRAINT `review_helpful_ibfk_1` FOREIGN KEY (`reviewid`) REFERENCES `item_reviews` (`reviewid`) ON DELETE CASCADE,
  CONSTRAINT `review_helpful_ibfk_2` FOREIGN KEY (`userid`) REFERENCES `userdata` (`userid`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `review_helpful`
--

LOCK TABLES `review_helpful` WRITE;
/*!40000 ALTER TABLE `review_helpful` DISABLE KEYS */;
/*!40000 ALTER TABLE `review_helpful` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userdata`
--

DROP TABLE IF EXISTS `userdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `userdata` (
  `userid` binary(16) NOT NULL,
  `username` varchar(50) NOT NULL,
  `useremail` varchar(50) NOT NULL,
  `userpassword` varbinary(255) DEFAULT NULL,
  `useraddress` tinytext,
  `usergender` enum('Male','Female','Others') DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `userphone` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`userid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `userdata`
--

LOCK TABLES `userdata` WRITE;
/*!40000 ALTER TABLE `userdata` DISABLE KEYS */;
INSERT INTO `userdata` VALUES (_binary '∫\ˆc\È\∆LE\Âè\"\Ï$˙3©\‡','jayanthkrishna','jakkampudi04@gmail.com',_binary '$2b$12$O8VLrdzWPTM7Y9pO4VlE3.I8PmOm3k.rbn2cyZEdJKFS0M9wZjYBi','KUPPENAKUNTLA, PENUBALLI,',NULL,'2026-06-29 09:48:48',NULL);
/*!40000 ALTER TABLE `userdata` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-30 18:09:05
