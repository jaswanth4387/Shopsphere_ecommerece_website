# 🛒 ShopSphere

A full-stack e-commerce web application built with **Flask** and **MySQL**. Customers can browse products, manage a cart, pay securely with **Razorpay**, and review what they bought. Admins manage the catalogue, orders and customers from a dedicated panel.

**Live demo:** https://shopsphere-n9kc.onrender.com
*(Hosted on Render's free tier, so the first visit after a period of inactivity can take about a minute to wake up.)*

<!-- Add screenshots here, for example:
![Home page](docs/home.png)
![Product details](docs/product.png)
![Admin dashboard](docs/admin.png)
-->

---

## ✨ Features

### 👤 For customers
- **Secure sign-up with email OTP verification** – accounts are created only after the emailed 6-digit code is confirmed.
- **Login and password reset** – forgot-password flow with an OTP followed by a time-limited reset link.
- **Product browsing and search** – search across product name, description, about text and category.
- **Product details page** – full description, stock, related products from the same category.
- **Ratings and reviews** – average rating, star breakdown, review titles, text and optional photos. Only customers who have **paid for a product** can review it (shown as *Verified Purchase*), one review per product.
- **Shopping cart** – add items, increase or decrease quantity, remove items. Quantities are limited to the available stock.
- **Checkout with Razorpay** – payments in INR with 18% GST included in the total.
- **Reliable order saving** – the payment signature is verified on the server before the order is marked **Paid**, stock is reduced and the cart is cleared.

### 🛠️ For admins
- **Admin dashboard** with quick navigation.
- **Product management** – add, view, edit and delete products with image upload.
- **Product search** inside the admin panel.
- **Order overview** – all paid orders with customer, amount and status.
- **Customer overview** – every customer with their number of orders and total spend.
- **Protected admin registration** – public admin sign-up is switched off by default and enabled only when you need to create an admin.

### 🔐 Security and reliability
- Passwords hashed with **bcrypt**.
- OTPs are **never stored in plain text**; they expire after 5 minutes and allow a limited number of attempts.
- Signed cookie sessions (HTTP-only, SameSite, Secure in production).
- Uploaded images are checked by file content, not just the extension, and limited to 6 MB.
- Payments are verified with Razorpay's signature check, and repeated callbacks do not process an order twice.
- All secrets live in environment variables, never in the code.
- One short-lived database connection per request, with friendly handling when the database is unreachable.

---

## 🧰 Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, Gunicorn |
| Database | MySQL 8 (`mysql-connector-python`) |
| Frontend | Jinja2 templates, HTML, CSS, JavaScript, Bootstrap |
| Payments | Razorpay |
| Email (OTP) | Brevo transactional email API (Gmail SMTP for local use) |
| Image storage | Cloudinary (local folder during development) |
| Security | Flask-Bcrypt, itsdangerous |
| Hosting | Render (web), Aiven (MySQL), Cloudinary (images) |

---

## 📁 Project structure

```
Shopsphere/
├── app.py              # Flask application: routes, database, payments, admin
├── cmail.py            # Email sending (Brevo API / local SMTP fallback)
├── otp.py              # OTP generator
├── stoken.py           # Signed, time-limited tokens for password reset
├── schema.sql          # MySQL table definitions
├── seed_items.json     # Sample products
├── init_db.py          # Creates tables and loads sample products
├── requirements.txt    # Python dependencies
├── render.yaml         # Render deployment blueprint
├── .env.example        # Template for local environment variables
├── DEPLOY.md           # Step-by-step deployment guide
├── templates/          # Jinja2 pages (customer and admin)
└── static/images/      # Logos, background and sample product images
```

---

## 🚀 Run it locally

**Requirements:** Python 3.12+, a MySQL 8 database.

```bash
# 1. Clone the repository
git clone https://github.com/jaswanth4387/Shopsphere_ecommerece_website.git
cd Shopsphere_ecommerece_website

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your environment file and fill in the values
copy .env.example .env         # Windows  (use cp on macOS / Linux)

# 5. Create the tables and add the sample products
python init_db.py --seed

# 6. Start the app
python app.py
```

Open http://localhost:5000.

### Environment variables

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Signs sessions and reset links (use a long random value) |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL connection |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` | Razorpay keys (use test keys while developing) |
| `BREVO_API_KEY`, `MAIL_SENDER` | OTP email through Brevo (sender must be verified in Brevo) |
| `CLOUDINARY_URL` | Image storage in production (leave empty locally) |
| `ALLOW_ADMIN_SIGNUP` | `true` only while creating an admin account |
| `FLASK_DEBUG` | `True` for local development only |

---

## ☁️ Deployment

The project is configured for **Render** using `render.yaml`:

1. Create a free MySQL database on **Aiven** and run `python init_db.py --seed` once against it.
2. Create **Cloudinary** and **Brevo** accounts for images and email.
3. Push the code to GitHub and create a **Blueprint** on Render from the repository.
4. Enter the environment variables in the Render dashboard.
5. Create the first admin by temporarily setting `ALLOW_ADMIN_SIGNUP=true`.

The full walkthrough is in [DEPLOY.md](DEPLOY.md).

> **Why Brevo and Cloudinary?** Render's free tier blocks outbound SMTP and does not keep uploaded files after a restart, so emails go through an HTTPS email API and images are stored in Cloudinary.

---

## 🧪 Testing payments

Use Razorpay **test mode** keys. Test card: `4111 1111 1111 1111`, any future expiry date and any CVV.

---

## 🗺️ Roadmap

- Razorpay webhook so orders are confirmed even if the customer closes the tab after paying
- "My Orders" page and order tracking for customers
- CSRF protection on all state-changing actions
- Wishlist and product categories page
- Admin order status updates (packed, shipped, delivered)

---

## 👨‍💻 Author

**Jakkampudi Jaswanth Krishna**
B.Tech in Computer Science and Engineering (Data Science)
GitHub: [@jaswanth4387](https://github.com/jaswanth4387)
