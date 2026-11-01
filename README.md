# 🛍️ ShopSphere

A full-stack e-commerce web application built with **Flask** and **MySQL**. Customers can browse and search products, manage a cart, and pay online through **Razorpay**. Admins get a separate panel to manage the product catalogue, view customers and track orders.

---

## ✨ Features

### 👤 Customer
- Sign up with **email OTP verification** and log in (bcrypt-hashed passwords)
- **Forgot password** flow with OTP and a time-limited reset link
- Browse products by category and **search** by name, description or category
- Product details page with ratings and reviews display
- Shopping cart: add, remove, increase/decrease quantity (including AJAX add-to-cart)
- Checkout and secure payment via **Razorpay**, with server-side payment signature verification

### 🛠️ Admin
- Separate admin login and signup (OTP-verified)
- Dashboard with product management: **add, view, edit, delete** products with image upload
- View all **customers** and **orders**
- Admin pages are protected by a session check

### 🗂️ Product categories
Home Appliances, Grocery, Fashion, Electronics, Toys, Sports

---

## 🛠 Tech Stack

| Layer | Technologies |
|-------|--------------|
| Backend | Python, Flask 3, Flask-Session, Flask-Bcrypt, itsdangerous |
| Database | MySQL (`mysql-connector-python`) |
| Payments | Razorpay |
| Email | Gmail SMTP (OTP delivery) |
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript, Jinja2 |
| Production server | Gunicorn |

---

## 📁 Project Structure

```
Shopsphere/
├── app.py                    # Flask app: routes, DB access, payments
├── cmail.py                  # Email sending (SMTP)
├── otp.py                    # OTP generator
├── stoken.py                 # Signed, expiring tokens for reset links
├── requirements.txt
├── shopsphere_backup.sql     # Database schema + sample products
├── templates/
│   ├── index.html, home.html, login.html, signup.html
│   ├── otp.html, forgot.html, forgototp.html, newpassword.html
│   ├── product_details.html, cart.html, checkout.html
│   └── admin_*.html, admindashboard.html
└── static/images/            # Product images and site icons
```

---

## 🗄️ Database

Eight tables:

| Table | Purpose |
|-------|---------|
| `userdata` | Customer accounts |
| `admindata` | Admin accounts |
| `items` | Products (name, description, price, stock, category, image) |
| `cart` | Items in each user's cart |
| `orders` | Orders with Razorpay IDs, payment status and order status |
| `order_items` | Line items of each order |
| `item_reviews` | Ratings and reviews |
| `review_helpful` | "Helpful" votes on reviews |

Order status: `Placed → Packed → Shipped → Delivered / Cancelled`
Payment status: `Pending / Paid / Failed`

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- MySQL 8+
- A [Razorpay](https://razorpay.com) account (test keys are fine)
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833) for OTP emails

### Installation

```bash
# 1. Clone
git clone https://github.com/jaswanth4387/Shopsphere_ecommerece_website.git
cd Shopsphere_ecommerece_website

# 2. Virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Database

```sql
CREATE DATABASE shopsphere;
```

```bash
mysql -u root -p shopsphere < shopsphere_backup.sql
```

### Environment variables

Create a `.env` file in the project root (it is git-ignored):

```env
SECRET_KEY=change-this-to-a-long-random-string
SESSION_TYPE=filesystem

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=shopsphere

RAZORPAY_KEY_ID=rzp_test_xxxxxxxx
RAZORPAY_KEY_SECRET=your_razorpay_secret

FLASK_DEBUG=True
```

### Run

```bash
python app.py
```

Open http://127.0.0.1:5000/.

For production: `gunicorn app:app`

---

## 🗺️ Main Routes

| Route | Access | Purpose |
|-------|--------|---------|
| `/`, `/home` | Public | Landing page and product listing (`?q=` to search) |
| `/signup/<role>`, `/login/<role>` | Public | `role` is `user` or `admin` |
| `/forgot/<role>` | Public | Password reset via OTP |
| `/product/<id>` | Public | Product details and reviews |
| `/cart`, `/addtocart/<id>`, `/increase/<id>`, `/decrease/<id>`, `/removefromcart/<id>` | Customer | Cart |
| `/checkout`, `/payment-success` | Customer | Razorpay payment and verification |
| `/admin/products`, `/admin/additem` | Admin | Manage products |
| `/editproduct/<id>`, `/deleteproduct/<id>` | Admin | Edit and delete products |
| `/admin/orders`, `/admin/customers` | Admin | Orders and customers |

---

## 🔭 Roadmap

- [ ] Review submission form (reviews are displayed, but there is no route to add one yet)
- [ ] Wishlist
- [ ] Order tracking page for customers
- [ ] Invoice generation and order-confirmation emails
- [ ] Coupons and discounts
- [ ] Sales analytics for admins
- [ ] Product recommendations
- [ ] Customer profile page

---

## 📸 Screenshots

Add screenshots to a `docs/` folder and link them here:

```markdown
![Home](docs/home.png)
```

---

## 👤 Author

**Jakkampudi Jaswanth Krishna**
GitHub: [@jaswanth4387](https://github.com/jaswanth4387)

---


