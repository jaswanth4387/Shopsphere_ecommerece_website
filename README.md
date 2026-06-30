# 🛒 ShopSphere

ShopSphere is a modern full-stack e-commerce web application developed using **Python, Flask, MySQL, HTML, CSS, Bootstrap, and JavaScript**.

The project provides a complete shopping experience where users can browse products, search items, add products to a cart, place orders, and make payments through Razorpay. It also includes an admin panel for managing products and orders.

---

# Features

## User

- User Registration
- User Login
- Forgot Password (OTP)
- Browse Products
- Search Products
- View Product Details
- Add to Cart
- Checkout
- Razorpay Payment
- Responsive UI

## Admin

- Admin Login
- Add Products
- Edit Products
- Delete Products
- View Products
- View Customer Orders

---

# Technology Stack

## Backend

- Python
- Flask
- Flask Session
- Flask Bcrypt

## Frontend

- HTML5
- CSS3
- Bootstrap 5
- JavaScript
- Jinja2

## Database

- MySQL

## Payment Gateway

- Razorpay

---

# Project Structure

```
ShopSphere/

│── app.py                 # Main Flask application

│── requirements.txt       # Python dependencies

│── templates/             # HTML templates

│── static/

│     ├── css/

│     ├── js/

│     └── images/

│── cmail.py               # Email configuration

│── otp.py                 # OTP generation

│── stoken.py              # Token generation

│── README.md

│── .gitignore
```

---

# Database

The project uses **MySQL**.

Main tables:

```
userdata
admindata
items
cart
orders
order_items
item_reviews
review_helpful
```

Import the provided SQL file before running the project.

---

# Installation

## 1 Clone Repository

```bash
git clone https://github.com/<your-username>/ShopSphere.git

cd ShopSphere
```

---

## 2 Create Virtual Environment

Windows

```bash
python -m venv venv

venv\Scripts\activate
```

Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## 3 Install Packages

```bash
pip install -r requirements.txt
```

---

## 4 Configure Database

Create a MySQL database.

```
shopsphere
```

Import the SQL backup.

Update your database credentials in **app.py**.

Example:

```python
host="localhost"

user="root"

password="your_password"

database="shopsphere"
```

---

## 5 Configure Razorpay

Replace the test credentials with your own.

```python
RAZORPAY_KEY_ID="YOUR_KEY"

RAZORPAY_SECRET="YOUR_SECRET"
```

---

## 6 Run the Application

```bash
python app.py
```

Open your browser.

```
http://127.0.0.1:5000
```

---

# Images

Product images are stored in

```
static/images/
```

The database stores only the filename.

---

# Authentication

The project supports two types of users.

### Customer

- Register
- Login
- Purchase products

### Admin

- Login
- Manage products
- View orders

---

# Current Status

✅ User Authentication

✅ Admin Dashboard

✅ Product Management

✅ Shopping Cart

✅ Search

✅ Product Details

✅ Razorpay Payment

✅ Order Management

🚧 Reviews Backend (In Progress)

🚧 Wishlist

🚧 Order Tracking

---

# Future Improvements

- Product Recommendations

- Wishlist

- Invoice Generation

- Email Notifications

- Sales Analytics

- Coupons & Discounts

- Order Tracking

- Customer Profile

---

# Author

**J. Jaswanth Krishna**

Python Full Stack Developer

GitHub: https://github.com/<your-username>

LinkedIn: <your-linkedin>

---

# License

This project is developed for learning and portfolio purposes.
