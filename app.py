"""ShopSphere - Flask + MySQL e-commerce app, ready to deploy on Render."""
import hashlib
import hmac
import os
import re
import time
import uuid
from decimal import ROUND_HALF_UP, Decimal
from functools import wraps

import mysql.connector
import razorpay
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_bcrypt import Bcrypt
from mysql.connector import Error as MySQLError
from mysql.connector import IntegrityError
from werkzeug.middleware.proxy_fix import ProxyFix

from cmail import MailError, sendmail
from otp import genotp
from stoken import dndata, endata

load_dotenv()

# =====================================================================
# Configuration
# =====================================================================
IS_PROD = bool(os.getenv("RENDER"))  # Render sets RENDER=true automatically

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
LOCAL_IMAGE_DIRS = {"products": "images", "reviews": "review_images"}

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
CATEGORIES = ["electronics", "fashion", "grocery", "sports", "toys", "Home_Appliences"]
TAX_RATE = Decimal("0.18")  # the cart/checkout pages show 18% GST

OTP_TTL_SECONDS = 300
OTP_MAX_ATTEMPTS = 5

USE_CLOUDINARY = bool(os.getenv("CLOUDINARY_URL"))
if USE_CLOUDINARY:
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(secure=True)  # reads CLOUDINARY_URL from the environment

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    if IS_PROD:
        raise RuntimeError("SECRET_KEY environment variable must be set in production")
    secret_key = "dev-only-secret-change-me"

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config.update(
    SECRET_KEY=secret_key,
    MAX_CONTENT_LENGTH=6 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=IS_PROD,
)
bcrypt = Bcrypt(app)


# =====================================================================
# Database (one connection per request, closed automatically)
# =====================================================================
def get_db():
    if "db" not in g:
        options = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
            "charset": "utf8mb4",
            "connection_timeout": 10,
            "autocommit": False,
        }
        if os.getenv("DB_SSL_DISABLED", "false").lower() == "true":
            options["ssl_disabled"] = True
        elif os.getenv("DB_SSL_CA"):
            options["ssl_ca"] = os.getenv("DB_SSL_CA")
        g.db = mysql.connector.connect(**options)
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is None:
        return
    try:
        if error is not None:
            db.rollback()
    except MySQLError:
        pass
    try:
        db.close()
    except MySQLError:
        pass


def fetchall(sql, params=(), dictionary=False):
    cursor = get_db().cursor(buffered=True, dictionary=dictionary)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()


def fetchone(sql, params=(), dictionary=False):
    cursor = get_db().cursor(buffered=True, dictionary=dictionary)
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()


def execute(sql, params=()):
    """Run one write statement and commit. Returns the affected row count."""
    db = get_db()
    cursor = db.cursor(buffered=True)
    try:
        cursor.execute(sql, params)
        db.commit()
        return cursor.rowcount
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


# =====================================================================
# Small helpers
# =====================================================================
def parse_uuid(value):
    """uuid string (with or without dashes) -> 16 raw bytes. Raises ValueError."""
    return uuid.UUID(value).bytes


def uuid_str(raw):
    return str(uuid.UUID(bytes=bytes(raw)))


def like_pattern(term):
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def current_user_id():
    return bytes.fromhex(session["userid"])


def current_admin_id():
    value = session.get("adminid")
    return bytes.fromhex(value) if value else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "userid" not in session:
            flash("Please login first.")
            return redirect(url_for("login", role="user"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "admin" not in session:
            flash("Please login as administrator.")
            return redirect(url_for("login", role="admin"))
        return view(*args, **kwargs)

    return wrapped


def razorpay_client():
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        raise RuntimeError("Razorpay keys are not configured")
    return razorpay.Client(auth=(key_id, key_secret))


# ---- OTP (the session cookie is readable by the browser, so only a keyed hash is stored)
def _otp_digest(purpose, email, otp):
    key = app.config["SECRET_KEY"].encode()
    message = f"{purpose}|{email}|{otp}".encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def start_otp(purpose, email, subject):
    """Create an OTP, remember its hash in the session and email it. Returns True if sent."""
    otp = genotp()
    session[f"{purpose}_otp"] = {
        "digest": _otp_digest(purpose, email, otp),
        "email": email,
        "ts": time.time(),
        "tries": 0,
    }
    try:
        sendmail(to=email, subject=subject, body=f"Your ShopSphere OTP is {otp}. It is valid for 5 minutes.")
    except MailError:
        app.logger.exception("Could not send OTP email")
        if app.debug:
            app.logger.warning("DEV ONLY - OTP for %s is %s", email, otp)
            return True
        session.pop(f"{purpose}_otp", None)
        return False
    return True


def check_otp(purpose, submitted):
    """Returns (ok, message, email)."""
    key = f"{purpose}_otp"
    record = session.get(key)
    if not record:
        return False, "Session expired. Please request a new OTP.", None
    if time.time() - record["ts"] > OTP_TTL_SECONDS:
        session.pop(key, None)
        return False, "OTP has expired. Please request a new one.", None
    if record["tries"] >= OTP_MAX_ATTEMPTS:
        session.pop(key, None)
        return False, "Too many wrong attempts. Please request a new OTP.", None

    record["tries"] += 1
    session[key] = record  # reassign so Flask saves the change

    expected = _otp_digest(purpose, record["email"], submitted)
    if hmac.compare_digest(record["digest"], expected):
        session.pop(key, None)
        return True, "", record["email"]
    return False, "Invalid OTP.", None


# ---- Images (Cloudinary in production, local folder for development)
def _looks_like_image(stream):
    head = stream.read(12)
    stream.seek(0)
    return (
        head.startswith(b"\xff\xd8\xff")
        or head.startswith(b"\x89PNG\r\n\x1a\n")
        or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")
    )


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file, kind):
    """Store an uploaded image and return the value to keep in the database
    (a Cloudinary URL, or a local file name in development)."""
    if not allowed_file(file.filename):
        raise ValueError("Only JPG, JPEG, PNG and WEBP images are allowed.")
    if not _looks_like_image(file.stream):
        raise ValueError("The uploaded file is not a valid image.")

    if USE_CLOUDINARY:
        result = cloudinary.uploader.upload(
            file.stream, folder=f"shopsphere/{kind}", resource_type="image"
        )
        return result["secure_url"]

    extension = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4()}.{extension}"
    folder = os.path.join(STATIC_DIR, LOCAL_IMAGE_DIRS[kind])
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, filename))
    return filename


def delete_image(stored, kind):
    if not stored:
        return
    try:
        if stored.startswith("http"):
            if USE_CLOUDINARY:
                match = re.search(r"/upload/(?:v\d+/)?(.+)\.[A-Za-z0-9]+$", stored)
                if match:
                    cloudinary.uploader.destroy(match.group(1))
            return
        path = os.path.join(STATIC_DIR, LOCAL_IMAGE_DIRS[kind], os.path.basename(stored))
        if os.path.isfile(path):
            os.remove(path)
    except Exception:  # never fail a request because an old image could not be removed
        app.logger.exception("Could not delete image %s", stored)


@app.context_processor
def static_url_for_remote_images():
    """Templates build image URLs as url_for('static', filename='images/' + name).
    When `name` is a full Cloudinary URL, return it as is."""

    def smart_url_for(endpoint, **values):
        if endpoint == "static":
            filename = values.get("filename", "")
            if "/" in filename and filename.split("/", 1)[1].startswith("http"):
                return filename.split("/", 1)[1]
        return url_for(endpoint, **values)

    return {"url_for": smart_url_for}


PRODUCT_COLUMNS = (
    "itemid, item_name, item_description, item_about, item_price, "
    "item_quantity, item_category, item_filename, added_by, created_at"
)

CART_SQL = """
    SELECT
        c.cartid,
        i.itemid,
        i.item_name,
        ROUND(i.item_price, 2),
        i.item_filename,
        c.quantity,
        ROUND(i.item_price * c.quantity, 2),
        i.item_quantity
    FROM cart AS c
    JOIN items AS i ON c.itemid = i.itemid
    WHERE c.userid = %s
    ORDER BY c.added_at
"""


# =====================================================================
# Error handlers / health
# =====================================================================
@app.route("/healthz")
def healthz():
    return "ok"


@app.errorhandler(413)
def file_too_large(error):
    flash("The uploaded file is too large (maximum 6 MB).")
    return redirect(request.referrer or url_for("home"))


@app.errorhandler(404)
def not_found(error):
    return "Page not found", 404


@app.errorhandler(MySQLError)
def database_error(error):
    app.logger.exception("Database error")
    return "The database is temporarily unavailable. Please try again in a moment.", 503


# =====================================================================
# Public pages
# =====================================================================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home")
def home():
    search = request.args.get("q", "").strip()

    if search:
        pattern = like_pattern(search)
        products = fetchall(
            f"""
            SELECT {PRODUCT_COLUMNS}
            FROM items
            WHERE item_name LIKE %s
               OR item_description LIKE %s
               OR item_about LIKE %s
               OR item_category LIKE %s
            ORDER BY created_at DESC
            """,
            (pattern, pattern, pattern, pattern),
        )
    else:
        products = fetchall(f"SELECT {PRODUCT_COLUMNS} FROM items ORDER BY created_at DESC")

    cart_count = 0
    if "userid" in session:
        cart_count = fetchone(
            "SELECT COUNT(*) FROM cart WHERE userid=%s", (current_user_id(),)
        )[0]

    return render_template("home.html", products=products, search=search, cart_count=cart_count)


@app.route("/product/<itemid>")
def productdetails(itemid):
    try:
        item_bytes = parse_uuid(itemid)
    except ValueError:
        flash("Invalid product.")
        return redirect(url_for("home"))

    product = fetchone(
        f"SELECT {PRODUCT_COLUMNS} FROM items WHERE itemid=%s", (item_bytes,), dictionary=True
    )
    if not product:
        flash("Product not found.")
        return redirect(url_for("home"))

    reviews = fetchall(
        """
        SELECT ir.*, u.username
        FROM item_reviews AS ir
        JOIN userdata AS u ON ir.userid = u.userid
        WHERE ir.itemid = %s
        ORDER BY ir.created_at DESC
        """,
        (item_bytes,),
        dictionary=True,
    )

    summary = fetchone(
        "SELECT AVG(rating) AS average_rating, COUNT(*) AS total_reviews "
        "FROM item_reviews WHERE itemid=%s",
        (item_bytes,),
        dictionary=True,
    )
    avg_rating = float(summary["average_rating"] or 0)
    review_count = summary["total_reviews"] or 0

    rating_rows = fetchall(
        "SELECT rating, COUNT(*) AS total FROM item_reviews WHERE itemid=%s GROUP BY rating",
        (item_bytes,),
        dictionary=True,
    )
    rating_percentage = {star: 0 for star in range(1, 6)}
    if review_count:
        for row in rating_rows:
            rating_percentage[row["rating"]] = round(row["total"] / review_count * 100)

    related_products = fetchall(
        """
        SELECT itemid, item_name, item_price, item_filename, item_category
        FROM items
        WHERE item_category = %s AND itemid != %s
        ORDER BY RAND()
        LIMIT 4
        """,
        (product["item_category"], item_bytes),
        dictionary=True,
    )

    can_review = False
    if "userid" in session:
        uid = current_user_id()
        purchased = fetchone(
            """
            SELECT 1
            FROM order_items AS oi
            JOIN orders AS o ON oi.orderid = o.orderid
            WHERE o.userid=%s AND oi.itemid=%s AND o.payment_status='Paid'
            LIMIT 1
            """,
            (uid, item_bytes),
        )
        if purchased:
            already = fetchone(
                "SELECT 1 FROM item_reviews WHERE userid=%s AND itemid=%s LIMIT 1",
                (uid, item_bytes),
            )
            can_review = already is None

    return render_template(
        "product_details.html",
        product=product,
        reviews=reviews,
        avg_rating=round(avg_rating, 1),
        review_count=review_count,
        rating_percentage=rating_percentage,
        related_products=related_products,
        can_review=can_review,
    )


@app.route("/product/<itemid>/review", methods=["POST"])
@login_required
def add_review(itemid):
    try:
        item_bytes = parse_uuid(itemid)
    except ValueError:
        flash("Invalid product.")
        return redirect(url_for("home"))

    back = redirect(url_for("productdetails", itemid=itemid) + "#reviews")
    uid = current_user_id()

    purchased = fetchone(
        """
        SELECT 1
        FROM order_items AS oi
        JOIN orders AS o ON oi.orderid = o.orderid
        WHERE o.userid=%s AND oi.itemid=%s AND o.payment_status='Paid'
        LIMIT 1
        """,
        (uid, item_bytes),
    )
    if not purchased:
        flash("You can review this product only after purchasing it.")
        return back

    try:
        rating = int(request.form.get("rating", ""))
        if not 1 <= rating <= 5:
            raise ValueError
    except ValueError:
        flash("Please choose a rating between 1 and 5.")
        return back

    review_title = request.form.get("review_title", "").strip()[:100]
    review_text = request.form.get("review_text", "").strip()
    if not review_text or len(review_text) > 5000:
        flash("Please write a review (up to 5000 characters).")
        return back

    review_image = None
    image = request.files.get("review_image")
    if image and image.filename:
        try:
            review_image = save_image(image, "reviews")
        except ValueError as exc:
            flash(str(exc))
            return back

    try:
        execute(
            """
            INSERT INTO item_reviews
                (userid, itemid, rating, review_title, review_text, review_image, verified_purchase)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
            """,
            (uid, item_bytes, rating, review_title or None, review_text, review_image),
        )
    except IntegrityError:
        delete_image(review_image, "reviews")
        flash("You have already reviewed this product.")
        return back

    flash("Thanks! Your review has been posted.")
    return back


# =====================================================================
# Authentication
# =====================================================================
@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if role not in ("user", "admin"):
        return "Invalid role", 404

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if role == "user":
            row = fetchone(
                "SELECT userid, username, userpassword FROM userdata WHERE useremail=%s",
                (email,),
            )
        else:
            row = fetchone(
                "SELECT adminid, admin_username, admin_password FROM admindata "
                "WHERE admin_useremail=%s",
                (email,),
            )

        if row and row[2] and bcrypt.check_password_hash(bytes(row[2]), password):
            session.clear()  # new session on login
            if role == "user":
                session["userid"] = bytes(row[0]).hex()
                session["user"] = row[1]
                return redirect(url_for("home"))
            session["adminid"] = bytes(row[0]).hex()
            session["admin"] = row[1]
            return redirect(url_for("admindashboard"))

        flash("Invalid email or password")

    return render_template("login.html", role=role)


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("home"))


@app.route("/admin/logout")
def adminlogout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("login", role="admin"))


def admin_signup_allowed():
    return os.getenv("ALLOW_ADMIN_SIGNUP", "false").lower() == "true"


@app.route("/signup/<role>", methods=["GET", "POST"])
def signup(role):
    if role not in ("user", "admin"):
        return "Invalid role", 404

    if role == "admin" and not admin_signup_allowed():
        flash("Admin registration is disabled.")
        return redirect(url_for("login", role="admin"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "")

        if not all([name, email, address, password]):
            flash("All fields are required.")
            return redirect(url_for("signup", role=role))
        if len(name) > 50 or len(email) > 50 or len(address) > 255:
            flash("Name and email can be at most 50 characters, address at most 255.")
            return redirect(url_for("signup", role=role))
        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("signup", role=role))

        if role == "user":
            exists = fetchone("SELECT 1 FROM userdata WHERE useremail=%s", (email,))
        else:
            exists = fetchone("SELECT 1 FROM admindata WHERE admin_useremail=%s", (email,))
        if exists:
            flash("Email already registered.")
            return redirect(url_for("signup", role=role))

        session["signup_role"] = role
        session["signup_data"] = {
            "name": name,
            "email": email,
            "address": address,
            "password": bcrypt.generate_password_hash(password).decode("utf-8"),
        }

        if not start_otp("signup", email, "ShopSphere Email Verification"):
            session.pop("signup_data", None)
            flash("We could not send the verification email. Please try again later.")
            return redirect(url_for("signup", role=role))

        flash("OTP sent to your email.")
        return redirect(url_for("signupotp", role=role))

    return render_template("signup.html", role=role)


@app.route("/signupotp/<role>", methods=["GET", "POST"])
def signupotp(role):
    if role not in ("user", "admin"):
        return "Invalid role", 404

    if role == "admin" and not admin_signup_allowed():
        flash("Admin registration is disabled.")
        return redirect(url_for("login", role="admin"))

    if request.method == "POST":
        submitted = request.form.get("otp", "").strip()
        if not submitted:
            flash("Please enter the OTP.")
            return redirect(url_for("signupotp", role=role))

        data = session.get("signup_data")
        if not data or session.get("signup_role") != role:
            flash("Session expired. Please sign up again.")
            return redirect(url_for("signup", role=role))

        ok, message, email = check_otp("signup", submitted)
        if not ok:
            flash(message)
            if "request a new" in message:
                return redirect(url_for("signup", role=role))
            return redirect(url_for("signupotp", role=role))

        try:
            if role == "user":
                execute(
                    """
                    INSERT INTO userdata (userid, username, useremail, useraddress, userpassword)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (uuid.uuid4().bytes, data["name"], email, data["address"], data["password"]),
                )
            else:
                execute(
                    """
                    INSERT INTO admindata
                        (adminid, admin_username, admin_useremail, admin_address, admin_password)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (uuid.uuid4().bytes, data["name"], email, data["address"], data["password"]),
                )
        except IntegrityError:
            session.pop("signup_data", None)
            session.pop("signup_role", None)
            flash("That email or name is already registered.")
            return redirect(url_for("signup", role=role))

        session.pop("signup_data", None)
        session.pop("signup_role", None)
        flash("Account created successfully.")
        return redirect(url_for("login", role=role))

    return render_template("otp.html", role=role)


@app.route("/forgot/<role>", methods=["GET", "POST"])
def forgot(role):
    if role not in ("user", "admin"):
        return "Invalid role", 404

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            flash("Email is required.")
            return redirect(url_for("forgot", role=role))

        if role == "user":
            exists = fetchone("SELECT 1 FROM userdata WHERE useremail=%s", (email,))
        else:
            exists = fetchone("SELECT 1 FROM admindata WHERE admin_useremail=%s", (email,))

        if not exists:
            flash("Email not registered.")
            return render_template("forgot.html", role=role)

        if not start_otp("reset", email, "ShopSphere Password Reset OTP"):
            flash("We could not send the email. Please try again later.")
            return redirect(url_for("forgot", role=role))

        flash("OTP sent to your email.")
        return redirect(url_for("forgototp", role=role))

    return render_template("forgot.html", role=role)


@app.route("/forgototp/<role>", methods=["GET", "POST"])
def forgototp(role):
    if role not in ("user", "admin"):
        return "Invalid role", 404

    if request.method == "POST":
        submitted = request.form.get("otp", "").strip()
        if not submitted:
            flash("Please enter the OTP.")
            return redirect(url_for("forgototp", role=role))

        ok, message, email = check_otp("reset", submitted)
        if not ok:
            flash(message)
            if "request a new" in message:
                return redirect(url_for("forgot", role=role))
            return redirect(url_for("forgototp", role=role))

        token = endata({"email": email, "role": role})
        return redirect(url_for("newpassword", role=role, data=token))

    return render_template("forgototp.html", role=role)


@app.route("/newpassword/<role>/<data>", methods=["GET", "POST"])
def newpassword(role, data):
    if role not in ("user", "admin"):
        return "Invalid role", 404

    try:
        payload = dndata(data, max_age=900)
        if payload.get("role") != role:
            raise ValueError("role mismatch")
        email = payload["email"]
    except Exception:
        flash("Invalid or expired password reset link.")
        return redirect(url_for("forgot", role=role))

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("newpassword", role=role, data=data))

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        if role == "user":
            execute("UPDATE userdata SET userpassword=%s WHERE useremail=%s", (hashed, email))
        else:
            execute(
                "UPDATE admindata SET admin_password=%s WHERE admin_useremail=%s", (hashed, email)
            )

        flash("Password updated successfully.")
        return redirect(url_for("login", role=role))

    return render_template("newpassword.html", role=role, data=data)


# =====================================================================
# Admin
# =====================================================================
@app.route("/admin/dashboard")
@admin_required
def admindashboard():
    return render_template("admindashboard.html")


@app.route("/admin/additem", methods=["GET", "POST"])
@admin_required
def additem():
    if request.method == "POST":
        item_name = request.form.get("item_name", "").strip()
        item_description = request.form.get("item_description", "").strip()
        item_about = request.form.get("item_about", "").strip()
        item_price = request.form.get("item_price", "").strip()
        item_quantity = request.form.get("item_quantity", "").strip()
        item_category = request.form.get("item_category", "").strip()

        if not all([item_name, item_description, item_about, item_price, item_quantity, item_category]):
            flash("All fields are required.")
            return redirect(url_for("additem"))
        if item_category not in CATEGORIES:
            flash("Please choose a valid category.")
            return redirect(url_for("additem"))

        try:
            price = Decimal(item_price)
            quantity = int(item_quantity)
            if price <= 0 or quantity < 0:
                raise ValueError
        except (ValueError, ArithmeticError):
            flash("Invalid product details.")
            return redirect(url_for("additem"))

        image = request.files.get("image")
        if not image or not image.filename:
            flash("Please select an image.")
            return redirect(url_for("additem"))

        try:
            stored = save_image(image, "products")
        except ValueError as exc:
            flash(str(exc))
            return redirect(url_for("additem"))
        except Exception:
            app.logger.exception("Image upload failed")
            flash("Image upload failed. Please try again.")
            return redirect(url_for("additem"))

        try:
            execute(
                """
                INSERT INTO items
                    (itemid, item_name, item_description, item_about, item_price,
                     item_quantity, item_category, item_filename, added_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    uuid.uuid4().bytes,
                    item_name,
                    item_description,
                    item_about,
                    price,
                    quantity,
                    item_category,
                    stored,
                    current_admin_id(),
                ),
            )
        except Exception:
            delete_image(stored, "products")
            raise

        flash("Product added successfully.")
        return redirect(url_for("viewallitems"))

    return render_template("admin_addproduct.html")


@app.route("/admin/products")
@admin_required
def viewallitems():
    search = request.args.get("search", "").strip()
    columns = (
        "itemid, item_name, item_description, item_about, item_price, "
        "item_quantity, item_category, item_filename, created_at"
    )
    if search:
        rows = fetchall(
            f"SELECT {columns} FROM items WHERE item_name LIKE %s ORDER BY created_at DESC",
            (like_pattern(search),),
        )
    else:
        rows = fetchall(f"SELECT {columns} FROM items ORDER BY created_at DESC")

    products = []
    for row in rows:
        row = list(row)
        row[0] = uuid_str(row[0])
        products.append(row)

    return render_template("admin_viewallitems.html", products=products, search=search)


def _load_product_row(item_bytes):
    row = fetchone(f"SELECT {PRODUCT_COLUMNS} FROM items WHERE itemid=%s", (item_bytes,))
    if row:
        row = list(row)
        row[0] = uuid_str(row[0])
    return row


@app.route("/viewproduct/<itemid>")
@admin_required
def viewproduct(itemid):
    try:
        item_bytes = parse_uuid(itemid)
    except ValueError:
        flash("Invalid product.")
        return redirect(url_for("viewallitems"))

    product = _load_product_row(item_bytes)
    if not product:
        flash("Product not found.")
        return redirect(url_for("viewallitems"))

    return render_template("admin_viewproduct.html", product=product)


@app.route("/editproduct/<itemid>", methods=["GET", "POST"])
@admin_required
def editproduct(itemid):
    try:
        item_bytes = parse_uuid(itemid)
    except ValueError:
        flash("Invalid product.")
        return redirect(url_for("viewallitems"))

    product = _load_product_row(item_bytes)
    if not product:
        flash("Product not found.")
        return redirect(url_for("viewallitems"))

    if request.method == "POST":
        item_name = request.form.get("item_name", "").strip()
        item_description = request.form.get("item_description", "").strip()
        item_about = request.form.get("item_about", "").strip()
        item_price = request.form.get("item_price", "").strip()
        item_quantity = request.form.get("item_quantity", "").strip()
        item_category = request.form.get("item_category", "").strip()

        if not all([item_name, item_description, item_about, item_price, item_quantity, item_category]):
            flash("All fields are required.")
            return redirect(request.url)
        if item_category not in CATEGORIES:
            flash("Please choose a valid category.")
            return redirect(request.url)

        try:
            price = Decimal(item_price)
            quantity = int(item_quantity)
            if price <= 0 or quantity < 0:
                raise ValueError
        except (ValueError, ArithmeticError):
            flash("Invalid product price or quantity.")
            return redirect(request.url)

        old_filename = product[7]
        filename = old_filename
        new_image = None

        image = request.files.get("image")
        if image and image.filename:
            try:
                new_image = save_image(image, "products")
            except ValueError as exc:
                flash(str(exc))
                return redirect(request.url)
            filename = new_image

        try:
            execute(
                """
                UPDATE items
                SET item_name=%s, item_description=%s, item_about=%s, item_price=%s,
                    item_quantity=%s, item_category=%s, item_filename=%s
                WHERE itemid=%s
                """,
                (item_name, item_description, item_about, price, quantity,
                 item_category, filename, item_bytes),
            )
        except Exception:
            delete_image(new_image, "products")
            raise

        if new_image:
            delete_image(old_filename, "products")

        flash("Product updated successfully.")
        return redirect(url_for("viewallitems"))

    return render_template("admin_editproduct.html", product=product)


@app.route("/deleteproduct/<itemid>")
@admin_required
def deleteproduct(itemid):
    try:
        item_bytes = parse_uuid(itemid)
    except ValueError:
        flash("Invalid product.")
        return redirect(url_for("viewallitems"))

    row = fetchone("SELECT item_filename FROM items WHERE itemid=%s", (item_bytes,))
    if not row:
        flash("Product not found.")
        return redirect(url_for("viewallitems"))

    db = get_db()
    cursor = db.cursor(buffered=True)
    try:
        cursor.execute("DELETE FROM cart WHERE itemid=%s", (item_bytes,))
        cursor.execute("DELETE FROM items WHERE itemid=%s", (item_bytes,))
        db.commit()
    except IntegrityError:
        db.rollback()
        flash("This product is part of existing orders or reviews and cannot be deleted. "
              "Set its stock to 0 instead.")
        return redirect(url_for("viewallitems"))
    finally:
        cursor.close()

    delete_image(row[0], "products")
    flash("Product deleted successfully.")
    return redirect(url_for("viewallitems"))


@app.route("/admin/orders")
@admin_required
def adminorders():
    rows = fetchall(
        """
        SELECT o.orderid, u.username, o.total_amount, o.order_status, o.created_at
        FROM orders AS o
        JOIN userdata AS u ON o.userid = u.userid
        WHERE o.payment_status = 'Paid'
        ORDER BY o.created_at DESC
        """
    )
    orders = []
    for row in rows:
        row = list(row)
        row[0] = "#" + bytes(row[0]).hex()[:8].upper()
        orders.append(row)

    return render_template("admin_orders.html", orders=orders)


@app.route("/admin/customers")
@admin_required
def admincustomers():
    customers = fetchall(
        """
        SELECT
            u.userid,
            u.username,
            COALESCE(u.userphone, '-'),
            COUNT(o.orderid) AS total_orders,
            COALESCE(SUM(o.total_amount), 0) AS total_spent
        FROM userdata AS u
        LEFT JOIN orders AS o
            ON u.userid = o.userid AND o.payment_status = 'Paid'
        GROUP BY u.userid, u.username, u.userphone
        ORDER BY total_orders DESC
        """
    )
    return render_template("admin_customers.html", customers=customers)


# =====================================================================
# Cart
# =====================================================================
def _add_to_cart(uid, item_bytes):
    """Returns one of: ok, notfound, outofstock, maxstock."""
    db = get_db()
    cursor = db.cursor(buffered=True)
    try:
        cursor.execute("SELECT item_quantity FROM items WHERE itemid=%s", (item_bytes,))
        row = cursor.fetchone()
        if not row:
            return "notfound"
        stock = row[0] or 0
        if stock <= 0:
            return "outofstock"

        cursor.execute(
            "SELECT quantity FROM cart WHERE userid=%s AND itemid=%s", (uid, item_bytes)
        )
        existing = cursor.fetchone()

        if existing:
            if existing[0] >= stock:
                return "maxstock"
            cursor.execute(
                "UPDATE cart SET quantity = quantity + 1 WHERE userid=%s AND itemid=%s",
                (uid, item_bytes),
            )
        else:
            cursor.execute(
                "INSERT INTO cart (cartid, userid, itemid, quantity) VALUES (%s, %s, %s, 1)",
                (uuid.uuid4().bytes, uid, item_bytes),
            )
        db.commit()
        return "ok"
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


CART_MESSAGES = {
    "notfound": "Product not found.",
    "outofstock": "Sorry, this product is out of stock.",
    "maxstock": "Maximum available stock reached.",
}


@app.route("/addtocart/<itemid>")
@login_required
def addtocart(itemid):
    try:
        item_bytes = parse_uuid(itemid)
    except ValueError:
        flash("Invalid product.")
        return redirect(url_for("home"))

    status = _add_to_cart(current_user_id(), item_bytes)
    flash("Product added to cart." if status == "ok" else CART_MESSAGES[status])
    return redirect(request.referrer or url_for("home"))


@app.route("/addtocartajax/<itemid>", methods=["POST"])
def addtocartajax(itemid):
    if "userid" not in session:
        return {"status": "login"}

    try:
        item_bytes = parse_uuid(itemid)
    except ValueError:
        return {"status": "error", "message": "Invalid product."}, 400

    uid = current_user_id()
    status = _add_to_cart(uid, item_bytes)
    if status != "ok":
        return {"status": "error", "message": CART_MESSAGES[status]}, 400

    count = fetchone("SELECT COUNT(*) FROM cart WHERE userid=%s", (uid,))[0]
    return {"status": "success", "cart_count": count}


@app.route("/cart")
@login_required
def cart():
    cart_items = fetchall(CART_SQL, (current_user_id(),))
    grand_total = float(sum((row[6] for row in cart_items), Decimal("0")))
    return render_template("cart.html", cart_items=cart_items, grand_total=grand_total)


@app.route("/removefromcart/<cartid>")
@login_required
def removefromcart(cartid):
    try:
        cart_bytes = parse_uuid(cartid)
    except ValueError:
        flash("Invalid cart item.")
        return redirect(url_for("cart"))

    removed = execute(
        "DELETE FROM cart WHERE cartid=%s AND userid=%s", (cart_bytes, current_user_id())
    )
    flash("Product removed from cart." if removed else "Cart item not found.")
    return redirect(url_for("cart"))


@app.route("/increase/<cartid>")
@login_required
def increase(cartid):
    try:
        cart_bytes = parse_uuid(cartid)
    except ValueError:
        flash("Invalid cart item.")
        return redirect(url_for("cart"))

    uid = current_user_id()
    row = fetchone(
        """
        SELECT c.quantity, i.item_quantity
        FROM cart AS c JOIN items AS i ON c.itemid = i.itemid
        WHERE c.cartid=%s AND c.userid=%s
        """,
        (cart_bytes, uid),
    )
    if not row:
        flash("Cart item not found.")
    elif row[0] >= (row[1] or 0):
        flash("Maximum available stock reached.")
    else:
        execute(
            "UPDATE cart SET quantity = quantity + 1 WHERE cartid=%s AND userid=%s",
            (cart_bytes, uid),
        )
    return redirect(url_for("cart"))


@app.route("/decrease/<cartid>")
@login_required
def decrease(cartid):
    try:
        cart_bytes = parse_uuid(cartid)
    except ValueError:
        flash("Invalid cart item.")
        return redirect(url_for("cart"))

    execute(
        "UPDATE cart SET quantity = quantity - 1 WHERE cartid=%s AND userid=%s AND quantity > 1",
        (cart_bytes, current_user_id()),
    )
    return redirect(url_for("cart"))


# =====================================================================
# Checkout and payment
# =====================================================================
@app.route("/checkout")
@login_required
def checkout():
    uid = current_user_id()
    cart_items = fetchall(CART_SQL, (uid,))

    if not cart_items:
        flash("Your cart is empty.")
        return redirect(url_for("cart"))

    for row in cart_items:
        if row[5] > (row[7] or 0):
            flash(f"Only {row[7] or 0} unit(s) of '{row[2]}' are in stock. Please update your cart.")
            return redirect(url_for("cart"))

    subtotal = sum((row[6] for row in cart_items), Decimal("0"))
    total = (subtotal * (1 + TAX_RATE)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    paise = int(total * 100)

    order_bytes = uuid.uuid4().bytes
    try:
        razor_order = razorpay_client().order.create(
            {
                "amount": paise,
                "currency": "INR",
                "receipt": order_bytes.hex(),
                "payment_capture": 1,
            }
        )
    except Exception:
        app.logger.exception("Could not create Razorpay order")
        flash("Payment service is unavailable right now. Please try again shortly.")
        return redirect(url_for("cart"))

    db = get_db()
    cursor = db.cursor(buffered=True)
    try:
        # Replace any earlier unpaid attempt (order_items are removed by ON DELETE CASCADE).
        cursor.execute("DELETE FROM orders WHERE userid=%s AND payment_status='Pending'", (uid,))
        cursor.execute(
            """
            INSERT INTO orders
                (orderid, userid, razorpay_order_id, total_amount, payment_status, order_status)
            VALUES (%s, %s, %s, %s, 'Pending', 'Placed')
            """,
            (order_bytes, uid, razor_order["id"], total),
        )
        cursor.executemany(
            "INSERT INTO order_items (orderitemid, orderid, itemid, quantity, price) "
            "VALUES (%s, %s, %s, %s, %s)",
            [(uuid.uuid4().bytes, order_bytes, row[1], row[5], row[3]) for row in cart_items],
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        grand_total=float(subtotal),
        razor_order=razor_order,
        razor_key=os.getenv("RAZORPAY_KEY_ID"),
    )


@app.route("/payment-success")
@login_required
def payment_success():
    payment_id = request.args.get("payment_id", "")
    order_id = request.args.get("order_id", "")
    signature = request.args.get("signature", "")

    if not all([payment_id, order_id, signature]):
        flash("Invalid payment request.")
        return redirect(url_for("cart"))

    try:
        razorpay_client().utility.verify_payment_signature(
            {
                "razorpay_payment_id": payment_id,
                "razorpay_order_id": order_id,
                "razorpay_signature": signature,
            }
        )
    except Exception:
        app.logger.warning("Razorpay signature verification failed for order %s", order_id)
        flash("Payment verification failed.")
        return redirect(url_for("cart"))

    uid = current_user_id()
    db = get_db()
    cursor = db.cursor(buffered=True)
    try:
        cursor.execute(
            "SELECT orderid, payment_status FROM orders "
            "WHERE razorpay_order_id=%s AND userid=%s FOR UPDATE",
            (order_id, uid),
        )
        order = cursor.fetchone()
        if not order:
            db.rollback()
            flash("We could not find that order.")
            return redirect(url_for("cart"))

        if order[1] == "Paid":  # page refreshed / link opened twice
            db.rollback()
            flash("Payment successful. Your order is confirmed.")
            return redirect(url_for("home"))

        cursor.execute("SELECT itemid, quantity FROM order_items WHERE orderid=%s", (order[0],))
        for itemid, quantity in cursor.fetchall():
            cursor.execute(
                "UPDATE items SET item_quantity = GREATEST(item_quantity - %s, 0) WHERE itemid=%s",
                (quantity, itemid),
            )

        cursor.execute(
            "UPDATE orders SET payment_status='Paid', order_status='Placed', "
            "razorpay_payment_id=%s WHERE orderid=%s",
            (payment_id, order[0]),
        )
        cursor.execute("DELETE FROM cart WHERE userid=%s", (uid,))
        db.commit()
    except Exception:
        db.rollback()
        app.logger.exception("Could not finalise paid order %s", order_id)
        flash(f"Your payment was received but we could not save the order. "
              f"Please contact support with payment id {payment_id}.")
        return redirect(url_for("home"))
    finally:
        cursor.close()

    flash("Payment successful. Your order is confirmed.")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "False") == "True",
    )