from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template,
    session,
    flash,
)

from flask_session import Session
from flask_bcrypt import Bcrypt
import otp
from werkzeug.utils import secure_filename
from mysql.connector import connection
from dotenv import load_dotenv

from otp import genotp
from stoken import endata, dndata
from cmail import sendmail

import os
import time
import uuid
import razorpay

from mysql.connector import Error

def get_db():
    cursor = None

    try:
        return connection.MySQLConnection(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
    except Error as e:
        print(f"Database connection failed: {e}")
        raise


mydb = get_db()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

MAX_CONTENT_LENGTH = 6 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)

app = Flask(__name__)

bcrypt = Bcrypt(app)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = os.getenv("SESSION_TYPE")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

Session(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():

    search = request.args.get("q", "").strip()

    cursor = mydb.cursor(dictionary=True)

    userid = session.get("userid")

    # SEARCH PRODUCTS
    if search:

        cursor.execute(
            """
            SELECT
                itemid,
                item_name,
                item_price,
                item_filename,
                item_category,
                created_at
            FROM items
            WHERE
                item_name LIKE %s
                OR item_description LIKE %s
                OR item_about LIKE %s
                OR item_category LIKE %s
            ORDER BY created_at DESC
            """,
            (
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
                f"%{search}%"
            )
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM items
            ORDER BY created_at DESC
            """
        )

    cursor.close()

    # DEFAULT CART COUNT
    cart_count = 0

    # IF USER LOGGED IN
    userid = session.get("userid")

    if userid:

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM cart
            WHERE userid=%s
            """,
            (session['userid'],)
        )

        cart_count = cursor.fetchone()[0]

    return render_template(
        'home.html',
        products=products,
        search=search,
        cart_count=cart_count
    )

@app.route('/login/<role>', methods=['GET','POST'])
def login(role):

    if role not in ("user", "admin"):
        return "Invalid role", 404

    if request.method == 'POST':

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        cursor = mydb.cursor()

        if role == 'user':

            cursor.execute(
            """
            SELECT userid,
                   username,
                   userpassword
            FROM userdata
        
            WHERE useremail=%s
            """,
            [email]
            )        

        else:

            cursor.execute(
                """
                SELECT
                  adminid,
                  admin_username,
                  admin_password

                FROM admindata

                WHERE admin_useremail=%s
                """,

                [email]
            )

        data = cursor.fetchone()

        if data:

            userid = data[0]

            username = data[1]
            
            dbpassword = data[2]

            if bcrypt.check_password_hash(
                dbpassword,
                password
            ):

                if role == 'user':

                    session['userid'] = userid

                    session['user'] = username

                    return redirect(
                        url_for('home')
                    )

                else:

                    session['admin'] = username

                    return redirect(
                        url_for(
                            'admindashboard'
                        )
                    )

        flash("Invalid email or password")

    return render_template(
        'login.html',
        role=role
    )

@app.route("/signup/<role>", methods=["GET", "POST"])
def signup(role):

    if role not in ("user", "admin"):
        return "Invalid role", 404

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "")

        if not all([name, email, address, password]):
            flash("All fields are required.")
            return redirect(url_for("signup", role=role))

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("signup", role=role))

        cursor = mydb.cursor(dictionary=True)

        if role == "user":
            cursor.execute(
                """
                SELECT useremail
                FROM userdata
                WHERE useremail=%s
                """,
                (email,)
            )
        else:
            cursor.execute(
                """
                SELECT admin_useremail
                FROM admindata
                WHERE admin_useremail=%s
                """,
                (email,)
            )

        exists = cursor.fetchone()
        cursor.close()

        if exists:
            flash("Email already registered.")
            return redirect(url_for("signup", role=role))

        otp = genotp()

        session["signup_otp"] = otp
        session["signup_otp_time"] = time.time()
        session["signup_role"] = role

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        session["signup_data"] = {
            "name": name,
            "email": email,
            "address": address,
            "password": hashed_password,
        }

        sendmail(
            to=email,
            subject="ShopSphere Email Verification",
            body=f"Your OTP is {otp}",
        )

        flash("OTP sent to your email.")
        return redirect(url_for("signupotp", role=role))

    return render_template("signup.html", role=role)

@app.route("/forgot/<role>", methods=["GET", "POST"])
def forgot(role):

    if role not in ("user", "admin"):
        return "Invalid role", 404

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        if not email:
            flash("Email is required.")
            return redirect(url_for("forgot", role=role))

        cursor = mydb.cursor(dictionary=True)

        if role == "user":
            cursor.execute(
                """
                SELECT useremail
                FROM userdata
                WHERE useremail=%s
                """,
                (email,)
            )
        else:
            cursor.execute(
                """
                SELECT admin_useremail
                FROM admindata
                WHERE admin_useremail=%s
                """,
                (email,)
            )

        data = cursor.fetchone()
        cursor.close()

        if data:

            otp = genotp()

            session["otp"] = otp
            session["otp_time"] = time.time()
            session["email"] = email

            sendmail(
                to=email,
                subject="ShopSphere Password Reset OTP",
                body=f"Your OTP is {otp}",
            )

            flash("OTP sent to your email.")
            return redirect(url_for("forgototp", role=role))

        flash("Email not registered.")

    return render_template("forgot.html", role=role)



@app.route("/forgototp/<role>", methods=["GET", "POST"])
def forgototp(role):

    if role not in ("user", "admin"):
        return "Invalid role", 404

    if request.method == "POST":

        userotp = request.form.get("otp", "").strip()

        if not userotp:
            flash("Please enter the OTP.")
            return redirect(url_for("forgototp", role=role))

        if "otp" not in session or "email" not in session:
            flash("Session expired. Please request a new OTP.")
            return redirect(url_for("forgot", role=role))

        if time.time() - session.get("otp_time", 0) > 300:
            flash("OTP has expired.")
            return redirect(url_for("forgot", role=role))

        stored_otp = str(session.get("otp"))

        if userotp == stored_otp:

            email = session.pop("email")

            session.pop("otp", None)
            session.pop("otp_time", None)

            token = endata(email)

            return redirect(
                url_for(
                    "newpassword",
                    role=role,
                    data=token
                )
            )

        flash("Invalid OTP")

    return render_template(
        "forgototp.html",
        role=role
    )


@app.route("/signupotp/<role>", methods=["GET", "POST"])
def signupotp(role):

    if role not in ("user", "admin"):
        return "Invalid role", 404

    if request.method == "POST":

        otp = request.form.get("otp", "").strip()

        if not otp:
            flash("Please enter the OTP.")
            return redirect(url_for("signupotp", role=role))

        if (
            "signup_data" not in session or
            "signup_otp" not in session
        ):
            flash("Session expired.")
            return redirect(url_for("signup", role=role))

        if time.time() - session.get("signup_otp_time", 0) > 300:
            flash("OTP expired.")
            return redirect(url_for("signup", role=role))

        if otp == str(session["signup_otp"]):

            data = session["signup_data"]

            hashed = data["password"]     # Already hashed

            cursor = mydb.cursor()

            if role == "user":

                userid = uuid.uuid4().bytes

                cursor.execute(
                    """
                    INSERT INTO userdata
                    (
                        userid,
                        username,
                        useremail,
                        useraddress,
                        userpassword
                    )
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    (
                        userid,
                        data["name"],
                        data["email"],
                        data["address"],
                        hashed,
                    ),
                )

            else:

                adminid = uuid.uuid4().bytes

                cursor.execute(
                    """
                    INSERT INTO admindata
                    (
                        adminid,
                        admin_username,
                        admin_useremail,
                        admin_address,
                        admin_password
                    )
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    (
                        adminid,
                        data["name"],
                        data["email"],
                        data["address"],
                        hashed,
                    ),
                )

            mydb.commit()
            cursor.close()

            session.pop("signup_data", None)
            session.pop("signup_otp", None)
            session.pop("signup_otp_time", None)
            session.pop("signup_role", None)

            flash("Account created successfully.")

            return redirect(url_for("login", role=role))

        flash("Invalid OTP.")

    return render_template("otp.html", role=role)

@app.route("/newpassword/<role>/<data>", methods=["GET", "POST"])
def newpassword(role, data):

    if role not in ("user", "admin"):
        return "Invalid role", 404

    try:
        email = dndata(data)
    except Exception:
        flash("Invalid or expired password reset link.")
        return redirect(url_for("forgot", role=role))

    if request.method == "POST":

        password = request.form.get("password", "").strip()

        if not password:
            flash("Password is required.")
            return redirect(url_for("newpassword", role=role, data=data))

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("newpassword", role=role, data=data))

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        cursor = mydb.cursor()

        if role == "user":

            cursor.execute(
                """
                UPDATE userdata
                SET userpassword=%s
                WHERE useremail=%s
                """,
                (hashed, email),
            )

        else:

            cursor.execute(
                """
                UPDATE admindata
                SET admin_password=%s
                WHERE admin_useremail=%s
                """,
                (hashed, email),
            )

        mydb.commit()
        cursor.close()

        session.pop("otp", None)
        session.pop("otp_time", None)
        session.pop("email", None)

        flash("Password updated successfully.")

        return redirect(url_for("login", role=role))

    return render_template(
        "newpassword.html",
        role=role,
        data=data,
    )


@app.route("/admin/additem", methods=["GET", "POST"])
def additem():

    if "admin" not in session:
        return redirect(url_for("login", role="admin"))

    if request.method == "POST":

        item_name = request.form.get("item_name", "").strip()
        item_description = request.form.get("item_description", "").strip()
        item_about = request.form.get("item_about", "").strip()
        item_price = request.form.get("item_price", "").strip()
        item_quantity = request.form.get("item_quantity", "").strip()
        item_category = request.form.get("item_category", "").strip()

        if not all([
            item_name,
            item_description,
            item_about,
            item_price,
            item_quantity,
            item_category,
        ]):
            flash("All fields are required.")
            return redirect(url_for("additem"))

        image = request.files.get("image")

        if not image or image.filename == "":
            flash("Please select an image.")
            return redirect(url_for("additem"))

        if not allowed_file(image.filename):
            flash("Only JPG, JPEG, PNG and WEBP images are allowed.")
            return redirect(url_for("additem"))

        try:
            item_price = float(item_price)
            item_quantity = int(item_quantity)

            if item_price <= 0 or item_quantity < 0:
                raise ValueError

        except ValueError:
            flash("Invalid product details.")
            return redirect(url_for("additem"))

        extension = image.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4()}.{extension}"

        image.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename,
            )
        )

        cursor = mydb.cursor()

        cursor.execute(
            """
            INSERT INTO items
            (
                itemid,
                item_name,
                item_description,
                item_about,
                item_price,
                item_quantity,
                item_category,
                item_filename
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                uuid.uuid4().bytes,
                item_name,
                item_description,
                item_about,
                item_price,
                item_quantity,
                item_category,
                filename,
            ),
        )

        mydb.commit()
        cursor.close()

        flash("Product added successfully.")
        return redirect(url_for("viewallitems"))

    return render_template("admin_addproduct.html")

@app.route("/admin/logout")
def adminlogout():

    session.clear()

    flash("Logged out successfully.")

    return redirect(url_for("login", role="admin"))

@app.route("/admin/products")
def viewallitems():

    if "admin" not in session:
        flash("Please login as administrator.")
        return redirect(url_for("login", role="admin"))

    search = request.args.get("search", "").strip()

    cursor = mydb.cursor()

    if search:

        cursor.execute(
            """
            SELECT
                itemid,
                item_name,
                item_description,
                item_about,
                item_price,
                item_quantity,
                item_category,
                item_filename,
                created_at
            FROM items
            WHERE item_name LIKE %s
            ORDER BY created_at DESC
            """,
            (f"%{search}%",),
        )

    else:

        cursor.execute(
            """
            SELECT
                itemid,
                item_name,
                item_description,
                item_about,
                item_price,
                item_quantity,
                item_category,
                item_filename,
                created_at
            FROM items
            ORDER BY created_at DESC
            """
        )

    products = cursor.fetchall()
    cursor.close()

    formatted_products = []

    for row in products:
        row = list(row)
        row[0] = str(uuid.UUID(bytes=row[0]))
        formatted_products.append(row)

    return render_template(
        "admin_viewallitems.html",
        products=formatted_products,
        search=search,
    )

@app.route("/viewproduct/<itemid>")
def viewproduct(itemid):

    if "admin" not in session:
        flash("Please login as administrator.")
        return redirect(url_for("login", role="admin"))

    try:
        itemid = uuid.UUID(itemid).bytes
    except ValueError:
        flash("Invalid product.")
        return redirect(url_for("viewallitems"))

    cursor = mydb.cursor()

    cursor.execute(
        """
        SELECT
            itemid,
            item_name,
            item_description,
            item_about,
            item_price,
            item_quantity,
            item_category,
            item_filename
        FROM items
        WHERE itemid=%s
        """,
        (itemid,),
    )

    product = cursor.fetchone()
    cursor.close()

    if not product:
        flash("Product not found.")
        return redirect(url_for("viewallitems"))

    return render_template(
        "admin_viewproduct.html",
        product=product,
    )

@app.route("/editproduct/<itemid>", methods=["GET", "POST"])
def editproduct(itemid):

    # ==========================
    # Admin Authentication
    # ==========================
    if "admin" not in session:
        flash("Please login as administrator.")
        return redirect(url_for("login", role="admin"))

    # ==========================
    # Validate UUID
    # ==========================
    try:
        itemid = uuid.UUID(itemid).bytes
    except ValueError:
        flash("Invalid product.")
        return redirect(url_for("viewallitems"))

    cursor = mydb.cursor()

    # ==========================
    # Fetch Existing Product
    # ==========================
    cursor.execute(
        """
        SELECT
            item_name,
            item_description,
            item_about,
            item_price,
            item_quantity,
            item_category,
            item_filename
        FROM items
        WHERE itemid=%s
        """,
        (itemid,),
    )

    product = cursor.fetchone()

    if not product:
        cursor.close()
        flash("Product not found.")
        return redirect(url_for("viewallitems"))

    # ==========================
    # Update Product
    # ==========================
    if request.method == "POST":

        item_name = request.form.get("item_name", "").strip()
        item_description = request.form.get("item_description", "").strip()
        item_about = request.form.get("item_about", "").strip()
        item_price = request.form.get("item_price", "").strip()
        item_quantity = request.form.get("item_quantity", "").strip()
        item_category = request.form.get("item_category", "").strip()

        # Validate Empty Fields
        if not all([
            item_name,
            item_description,
            item_about,
            item_price,
            item_quantity,
            item_category,
        ]):
            flash("All fields are required.")
            return redirect(request.url)

        # Validate Price
        try:
            item_price = float(item_price)

            if item_price <= 0:
                raise ValueError

        except ValueError:
            flash("Invalid product price.")
            return redirect(request.url)

        # Validate Quantity
        try:
            item_quantity = int(item_quantity)

            if item_quantity < 0:
                raise ValueError

        except ValueError:
            flash("Invalid product quantity.")
            return redirect(request.url)

        image = request.files.get("image")

        # Existing filename
        filename = product[6]

        # New image uploaded
        if image and image.filename:

            if not allowed_file(image.filename):
                flash("Only JPG, JPEG, PNG and WEBP images are allowed.")
                return redirect(request.url)

            extension = image.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4()}.{extension}"

            image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename,
                )
            )

        cursor.execute(
            """
            UPDATE items
            SET
                item_name=%s,
                item_description=%s,
                item_about=%s,
                item_price=%s,
                item_quantity=%s,
                item_category=%s,
                item_filename=%s
            WHERE itemid=%s
            """,
            (
                item_name,
                item_description,
                item_about,
                item_price,
                item_quantity,
                item_category,
                filename,
                itemid,
            ),
        )

        mydb.commit()
        cursor.close()

        flash("Product updated successfully.")

        return redirect(url_for("viewallitems"))

    # Convert tuple to list for template
    product = list(product)

    return render_template(
        "admin_editproduct.html",
        product=product,
    )

@app.route("/deleteproduct/<itemid>")
def deleteproduct(itemid):

    # ==========================
    # Admin Authentication
    # ==========================
    if "admin" not in session:
        flash("Please login as administrator.")
        return redirect(url_for("login", role="admin"))

    # ==========================
    # Validate UUID
    # ==========================
    try:
        itemid = uuid.UUID(itemid).bytes
    except ValueError:
        flash("Invalid product.")
        return redirect(url_for("viewallitems"))

    cursor = mydb.cursor()

    # ==========================
    # Check Product Exists
    # ==========================
    cursor.execute(
        """
        SELECT item_filename
        FROM items
        WHERE itemid=%s
        """,
        (itemid,),
    )

    product = cursor.fetchone()

    if not product:
        cursor.close()
        flash("Product not found.")
        return redirect(url_for("viewallitems"))

    # ==========================
    # Delete Product Image
    # ==========================
    image_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        product[0],
    )

    if os.path.exists(image_path):
        os.remove(image_path)

    # ==========================
    # Delete Product
    # ==========================
    cursor.execute(
        """
        DELETE FROM items
        WHERE itemid=%s
        """,
        (itemid,),
    )

    mydb.commit()
    cursor.close()

    flash("Product deleted successfully.")

    return redirect(url_for("viewallitems"))
@app.route("/admin/orders")
def adminorders():

    # ==========================
    # Admin Authentication
    # ==========================
    if "admin" not in session:
        flash("Please login as administrator.")
        return redirect(url_for("login", role="admin"))

    cursor = mydb.cursor()

    cursor.execute(
        """
        SELECT
            o.orderid,
            u.username,
            o.total_amount,
            o.order_status,
            o.created_at
        FROM orders AS o
        JOIN userdata AS u
            ON o.userid = u.userid
        ORDER BY o.created_at DESC
        """
    )

    orders = cursor.fetchall()
    cursor.close()

    return render_template(
        "admin_orders.html",
        orders=orders,
    )

@app.route("/admin/customers")
def admincustomers():

    # ==========================
    # Admin Authentication
    # ==========================
    if "admin" not in session:
        flash("Please login as administrator.")
        return redirect(url_for("login", role="admin"))

    cursor = mydb.cursor()

    cursor.execute(
        """
        SELECT
            u.userid,
            u.username,
            u.userphone,
            COUNT(o.orderid) AS total_orders,
            COALESCE(SUM(o.total_amount), 0) AS total_spent

        FROM userdata AS u

        LEFT JOIN orders AS o
            ON u.userid = o.userid

        GROUP BY
            u.userid,
            u.username,
            u.userphone

        ORDER BY total_orders DESC
        """
    )

    customers = cursor.fetchall()
    cursor.close()

    return render_template(
        "admin_customers.html",
        customers=customers,
    )


@app.route("/addtocart/<itemid>")
def addtocart(itemid):

    # ==========================
    # User Authentication
    # ==========================
    if "userid" not in session:
        flash("Please login first.")
        return redirect(url_for("login", role="user"))

    userid = session.get("userid")

    # ==========================
    # Validate UUID
    # ==========================
    try:
        itemid = uuid.UUID(itemid).bytes
    except ValueError:
        flash("Invalid product.")
        return redirect(url_for("home"))

    cursor = mydb.cursor()

    # ==========================
    # Verify Product Exists
    # ==========================
    cursor.execute(
        """
        SELECT itemid
        FROM items
        WHERE itemid=%s
        """,
        (itemid,),
    )

    if not cursor.fetchone():
        cursor.close()
        flash("Product not found.")
        return redirect(url_for("home"))

    # ==========================
    # Check Cart
    # ==========================
    cursor.execute(
        """
        SELECT quantity
        FROM cart
        WHERE userid=%s
        AND itemid=%s
        """,
        (userid, itemid),
    )

    cart = cursor.fetchone()

    if cart:

        cursor.execute(
            """
            UPDATE cart
            SET quantity = quantity + 1
            WHERE userid=%s
            AND itemid=%s
            """,
            (userid, itemid),
        )

    else:

        cursor.execute(
            """
            INSERT INTO cart
            (
                cartid,
                userid,
                itemid,
                quantity,
                created_at
            )
            VALUES (%s,%s,%s,%s,NOW())
            """,
            (
                uuid.uuid4().bytes,
                userid,
                itemid,
                1,
            ),
        )

    mydb.commit()
    cursor.close()

    flash("Product added to cart.")

    return redirect(request.referrer or url_for("home"))

@app.route("/cart")
def cart():

    # ==========================
    # User Authentication
    # ==========================
    if "userid" not in session:
        flash("Please login to view your cart.")
        return redirect(url_for("login", role="user"))

    userid = session.get("userid")

    cursor = mydb.cursor()

    cursor.execute(
        """
        SELECT
            c.cartid,
            i.itemid,
            i.item_name,
            i.item_price,
            i.item_filename,
            c.quantity,
            (i.item_price * c.quantity) AS total

        FROM cart AS c

        JOIN items AS i
            ON c.itemid = i.itemid

        WHERE c.userid = %s
        """,
        (userid,),
    )

    cart_items = cursor.fetchall()
    cursor.close()

    grand_total = sum(
        float(item[6])
        for item in cart_items
    )

    return render_template(
        "cart.html",
        cart_items=cart_items,
        grand_total=grand_total,
    )

@app.route("/removefromcart/<cartid>")
def removefromcart(cartid):

    # ==========================
    # User Authentication
    # ==========================
    if "userid" not in session:
        flash("Please login first.")
        return redirect(url_for("login", role="user"))

    # ==========================
    # Validate UUID
    # ==========================
    try:
        cartid = uuid.UUID(cartid).bytes
    except ValueError:
        flash("Invalid cart item.")
        return redirect(url_for("cart"))

    userid = session.get("userid")

    cursor = mydb.cursor()

    cursor.execute(
        """
        DELETE FROM cart
        WHERE cartid=%s
        AND userid=%s
        """,
        (
            cartid,
            userid,
        ),
    )

    mydb.commit()

    if cursor.rowcount:
        flash("Product removed from cart.")
    else:
        flash("Cart item not found.")

    cursor.close()

    return redirect(url_for("cart"))

@app.route("/increase/<cartid>")
def increase(cartid):

    # ==========================
    # User Authentication
    # ==========================
    if "userid" not in session:
        flash("Please login first.")
        return redirect(url_for("login", role="user"))

    # ==========================
    # Validate UUID
    # ==========================
    try:
        cartid = uuid.UUID(cartid).bytes
    except ValueError:
        flash("Invalid cart item.")
        return redirect(url_for("cart"))

    userid = session.get("userid")

    cursor = mydb.cursor()

    # ==========================
    # Check Current Quantity & Stock
    # ==========================
    cursor.execute(
        """
        SELECT
            c.quantity,
            i.item_quantity
        FROM cart AS c
        JOIN items AS i
            ON c.itemid = i.itemid
        WHERE c.cartid=%s
        AND c.userid=%s
        """,
        (cartid, userid),
    )

    data = cursor.fetchone()

    if not data:
        cursor.close()
        flash("Cart item not found.")
        return redirect(url_for("cart"))

    current_quantity, stock = data

    if current_quantity >= stock:
        cursor.close()
        flash("Maximum available stock reached.")
        return redirect(url_for("cart"))

    cursor.execute(
        """
        UPDATE cart
        SET quantity = quantity + 1
        WHERE cartid=%s
        AND userid=%s
        """,
        (
            cartid,
            userid,
        ),
    )

    mydb.commit()
    cursor.close()

    return redirect(url_for("cart"))

@app.route("/decrease/<cartid>")
def decrease(cartid):

    # ==========================
    # User Authentication
    # ==========================
    if "userid" not in session:
        flash("Please login first.")
        return redirect(url_for("login", role="user"))

    # ==========================
    # Validate UUID
    # ==========================
    try:
        cartid = uuid.UUID(cartid).bytes
    except ValueError:
        flash("Invalid cart item.")
        return redirect(url_for("cart"))

    userid = session.get("userid")

    cursor = mydb.cursor()

    cursor.execute(
        """
        UPDATE cart
        SET quantity = quantity - 1
        WHERE cartid=%s
        AND userid=%s
        AND quantity > 1
        """,
        (
            cartid,
            userid,
        ),
    )

    mydb.commit()
    cursor.close()

    return redirect(url_for("cart"))

@app.route("/addtocartajax/<itemid>", methods=["POST"])
def addtocartajax(itemid):

    if "userid" not in session:
        return {"status": "login"}

    userid = session.get("userid")

    try:
        itemid = uuid.UUID(itemid).bytes
    except ValueError:
        return {
            "status": "error",
            "message": "Invalid product."
        }, 400

    cursor = mydb.cursor()

    # Verify product exists
    cursor.execute(
        """
        SELECT itemid
        FROM items
        WHERE itemid=%s
        """,
        (itemid,),
    )

    if not cursor.fetchone():
        cursor.close()
        return {
            "status": "error",
            "message": "Product not found."
        }, 404

    cursor.execute(
        """
        SELECT quantity
        FROM cart
        WHERE userid=%s
        AND itemid=%s
        """,
        (userid, itemid),
    )

    cart = cursor.fetchone()

    if cart:

        cursor.execute(
            """
            UPDATE cart
            SET quantity = quantity + 1
            WHERE userid=%s
            AND itemid=%s
            """,
            (userid, itemid),
        )

    else:

        cursor.execute(
            """
            INSERT INTO cart
            (
                cartid,
                userid,
                itemid,
                quantity,
                created_at
            )
            VALUES (%s,%s,%s,%s,NOW())
            """,
            (
                uuid.uuid4().bytes,
                userid,
                itemid,
                1,
            ),
        )

    mydb.commit()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM cart
        WHERE userid=%s
        """,
        (userid,),
    )

    count = cursor.fetchone()[0]
    cursor.close()

    return {
        "status": "success",
        "cart_count": count,
    }

@app.route("/checkout")
def checkout():

    if "userid" not in session:
        flash("Please login first.")
        return redirect(url_for("login", role="user"))

    userid = session.get("userid")

    cursor = mydb.cursor()

    cursor.execute(
        """
        SELECT
            c.cartid,
            i.itemid,
            i.item_name,
            i.item_price,
            i.item_filename,
            c.quantity,
            (i.item_price * c.quantity) AS total

        FROM cart AS c

        JOIN items AS i
            ON c.itemid = i.itemid

        WHERE c.userid=%s
        """,
        (userid,),
    )

    cart_items = cursor.fetchall()
    cursor.close()

    if not cart_items:
        flash("Your cart is empty.")
        return redirect(url_for("cart"))

    grand_total = sum(float(item[6]) for item in cart_items)

    razor_order = client.order.create(
        {
            "amount": int(grand_total * 100),
            "currency": "INR",
            "payment_capture": 1,
        }
    )

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        grand_total=grand_total,
        razor_order=razor_order,
        razor_key=os.getenv("RAZORPAY_KEY_ID"),
    )

@app.route("/product/<itemid>")
def productdetails(itemid):

    # ==========================================
    # Validate Product UUID
    # ==========================================
    try:
        itemid = uuid.UUID(itemid).bytes
    except ValueError:
        flash("Invalid product.")
        return redirect(url_for("home"))

    cursor = mydb.cursor(dictionary=True)

    # ==========================================
    # Product Details
    # ==========================================
    cursor.execute(
        """
        SELECT
            itemid,
            item_name,
            item_description,
            item_about,
            item_price,
            item_quantity,
            item_category,
            item_filename,
            created_at
        FROM items
        WHERE itemid = %s
        """,
        (itemid,),
    )

    product = cursor.fetchone()

    if not product:
        cursor.close()
        flash("Product not found.")
        return redirect(url_for("home"))

    # ==========================================
    # Product Reviews
    # ==========================================
    cursor.execute(
        """
        SELECT
            ir.reviewid,
            ir.userid,
            ir.itemid,
            ir.rating,
            ir.review,
            ir.created_at,
            u.username
        FROM item_reviews AS ir
        JOIN userdata AS u
            ON ir.userid = u.userid
        WHERE ir.itemid = %s
        ORDER BY ir.created_at DESC
        """,
        (itemid,),
    )

    reviews = cursor.fetchall()

    # ==========================================
    # Rating Summary
    # ==========================================
    cursor.execute(
        """
        SELECT
            AVG(rating) AS average_rating,
            COUNT(*) AS total_reviews
        FROM item_reviews
        WHERE itemid = %s
        """,
        (itemid,),
    )

    rating_data = cursor.fetchone()

    avg_rating = rating_data["average_rating"] or 0
    review_count = rating_data["total_reviews"]

    # ==========================================
    # Rating Breakdown
    # ==========================================
    cursor.execute(
        """
        SELECT
            rating,
            COUNT(*) AS total
        FROM item_reviews
        WHERE itemid = %s
        GROUP BY rating
        """,
        (itemid,),
    )

    rating_rows = cursor.fetchall()

    rating_percentage = {i: 0 for i in range(1, 6)}

    if review_count:

        for row in rating_rows:

            rating_percentage[row["rating"]] = round(
                (row["total"] / review_count) * 100
            )

    # ==========================================
    # Related Products
    # ==========================================
    cursor.execute(
        """
        SELECT
            itemid,
            item_name,
            item_price,
            item_filename,
            item_category
        FROM items
        WHERE
            item_category = %s
            AND itemid != %s
        ORDER BY RAND()
        LIMIT 4
        """,
        (
            product["item_category"],
            itemid,
        ),
    )

    related_products = cursor.fetchall()

    # ==========================================
    # Review Eligibility
    # ==========================================
    can_review = False

    userid = session.get("userid")

    if userid:

        # Check if user purchased this product
        cursor.execute(
            """
            SELECT 1
            FROM order_items AS oi
            JOIN orders AS o
                ON oi.orderid = o.orderid
            WHERE
                o.userid = %s
                AND oi.itemid = %s
                AND o.payment_status = 'Paid'
            LIMIT 1
            """,
            (
                userid,
                itemid,
            ),
        )

        purchased = cursor.fetchone()

        if purchased:

            cursor.execute(
                """
                SELECT 1
                FROM item_reviews
                WHERE
                    userid = %s
                    AND itemid = %s
                LIMIT 1
                """,
                (
                    userid,
                    itemid,
                ),
            )

            existing_review = cursor.fetchone()

            can_review = existing_review is None

    cursor.close()

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
@app.route("/payment-success")
def payment_success():

    payment_id = request.args.get("payment_id")
    order_id = request.args.get("order_id")
    signature = request.args.get("signature")

    try:
        client.utility.verify_payment_signature({
            "razorpay_payment_id": payment_id,
            "razorpay_order_id": order_id,
            "razorpay_signature": signature
        })

        flash("✅ Payment Successful! Order processing will be available in a future update.", "success")

        return redirect(url_for("home"))

    except Exception as e:
        print(e)
        flash("❌ Payment verification failed.", "danger")
        return redirect(url_for("checkout"))

    if "userid" not in session:
        flash("Please login first.")
        return redirect(url_for("login", role="user"))

    payment_id = request.args.get("payment_id")
    order_id = request.args.get("order_id")
    signature = request.args.get("signature")

    if not all([payment_id, order_id, signature]):
        flash("Invalid payment request.")
        return redirect(url_for("cart"))

    try:

        client.utility.verify_payment_signature(
            {
                "razorpay_payment_id": payment_id,
                "razorpay_order_id": order_id,
                "razorpay_signature": signature,
            }
        )

        userid = session.get("userid")
        cursor = mydb.cursor()

        mydb.start_transaction()

        cursor.execute(
            """
            SELECT orderid
            FROM orders
            WHERE razorpay_order_id=%s
            LIMIT 1
            """,
            (order_id,),
        )

        if cursor.fetchone():
            mydb.rollback()
            cursor.close()
            flash("Payment successful.")
            return redirect(url_for("home"))

        cursor.execute(
            """
            SELECT
                c.itemid,
                c.quantity,
                i.item_price,
                i.item_quantity
            FROM cart AS c
            JOIN items AS i
                ON c.itemid = i.itemid
            WHERE c.userid=%s
            FOR UPDATE
            """,
            (userid,),
        )

        cart_items = cursor.fetchall()

        if not cart_items:
            mydb.rollback()
            cursor.close()
            flash("Your cart is empty.")
            return redirect(url_for("cart"))

        for itemid, quantity, item_price, stock in cart_items:
            if quantity > stock:
                mydb.rollback()
                cursor.close()
                flash("Some items are no longer available in the requested quantity.")
                return redirect(url_for("cart"))

        order_uuid = uuid.uuid4().bytes
        total_amount = sum(
            item_price * quantity
            for _, quantity, item_price, _ in cart_items
        )

        cursor.execute(
            """
            INSERT INTO orders
            (
                orderid,
                userid,
                razorpay_order_id,
                razorpay_payment_id,
                total_amount,
                payment_status,
                order_status
            )
            VALUES (%s,%s,%s,%s,%s,'Paid','Placed')
            """,
            (
                order_uuid,
                userid,
                order_id,
                payment_id,
                total_amount,
            ),
        )

        cursor.executemany(
            """
            INSERT INTO order_items
            (
                orderitemid,
                orderid,
                itemid,
                quantity,
                price
            )
            VALUES (%s,%s,%s,%s,%s)
            """,
            [
                (
                    uuid.uuid4().bytes,
                    order_uuid,
                    itemid,
                    quantity,
                    item_price,
                )
                for itemid, quantity, item_price, _ in cart_items
            ],
        )

        cursor.executemany(
            """
            UPDATE items
            SET item_quantity = item_quantity - %s
            WHERE itemid=%s
            """,
            [
                (
                    quantity,
                    itemid,
                )
                for itemid, quantity, _, _ in cart_items
            ],
        )

        cursor.execute(
            """
            DELETE FROM cart
            WHERE userid=%s
            """,
            (userid,),
        )

        mydb.commit()
        cursor.close()

        flash("Payment successful.")

        return redirect(url_for("home"))

    except Exception as e:

        mydb.rollback()
        if cursor:
            cursor.close()

        app.logger.exception(e)

        flash("Payment verification failed.")

        return redirect(url_for("cart"))

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=os.getenv("FLASK_DEBUG", "False") == "True",
    )
