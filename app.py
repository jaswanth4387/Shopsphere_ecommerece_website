from flask import Flask,request,redirect,url_for,render_template,jsonify,session,make_response,flash
from flask_session import Session
from otp import genotp
from stoken import endata,dndata
from cmail import sendmail
from flask_bcrypt import Bcrypt 
from werkzeug.utils import secure_filename #removes extra , /,- infilename
from mysql.connector import connection

def get_db():

    return connection.MySQLConnection(

        host='localhost',

        user='root',

        password='',

        database='ShopSphere'

    )


import os
import uuid
import razorpay

mydb = connection.MySQLConnection(
    host='localhost',
    user='root',
    password='',
    database='ShopSphere'
)

BASE_DIR=os.path.abspath(os.path.dirname(__file__)) #dynamic fetching of app directory path
print(BASE_DIR)
UPLOAD_FOLDER=os.path.join(BASE_DIR,'static','images') #fetch static folder path
print(UPLOAD_FOLDER)
ALLOWED_EXETENSIONS={"png",'jpeg',"jpg",'webp','gif'} #allowing only certain exts
MAX_CONTENT_LENGTH=6*1024*1024  #MB #accepting only 6mb file
os.makedirs(UPLOAD_FOLDER,exist_ok=True)
client = razorpay.Client(auth=("", ""))
app=Flask(__name__)
bcrypt=Bcrypt(app)
app.secret_key="code9090"
app.config['SESSION_TYPE']='filesystem'
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH']=MAX_CONTENT_LENGTH
Session(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():

    search = request.args.get('q', '').strip()

    cursor = mydb.cursor()

    # SEARCH PRODUCTS
    if search:

        cursor.execute(
            """
            SELECT *
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

    products = cursor.fetchall()

    # DEFAULT CART COUNT
    cart_count = 0

    # IF USER LOGGED IN
    if 'userid' in session:

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

    if role not in ['user','admin']:
        return "Invalid role",404

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

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
                SELECT admin_username,
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

@app.route('/signup/<role>', methods=['GET','POST'])
def signup(role):

    if role not in ['user', 'admin']:
        return "Invalid role", 404

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        address = request.form['address']
        password = request.form['password']

        cursor = mydb.cursor()

        if role == 'user':
            cursor.execute(
                """
                SELECT useremail
                FROM userdata
                WHERE useremail=%s
                """,
                [email]
                )

        else:
        
            cursor.execute(
                """
                SELECT admin_useremail
                FROM admindata
                WHERE admin_useremail=%s
                """,
                [email]
            )

        exists = cursor.fetchone()

        if exists:

            flash("Email already registered")
            return redirect(
                url_for(
                    'signup',
                    role=role
                )
            )

        otp = genotp()

        session['signup_otp'] = otp
        session['signup_role'] = role

        session['signup_data'] = {
            'name': name,
            'email': email,
            'address': address,
            'password': password
        }

        sendmail(
            to=email,
            subject='ShopSphere Email Verification',
            body=f'Your OTP is {otp}'
        )

        return redirect(
            url_for(
                'signupotp',
                role=role
            )
        )

    return render_template(
        'signup.html',
        role=role
    )

@app.route('/forgot/<role>', methods=['GET','POST'])
def forgot(role):

    if request.method == 'POST':

        email = request.form['email']

        cursor = mydb.cursor()

        if role == 'user':

            cursor.execute(
                "SELECT useremail FROM userdata WHERE useremail=%s",
                [email]
            )

        else:

            cursor.execute(
                "SELECT admin_useremail FROM admindata WHERE admin_useremail=%s",
                [email]
            )

        data = cursor.fetchone()

        if data:

            otp = genotp()

            session['otp'] = otp
            session['email'] = email

            sendmail(
                to=email,
                subject='ShopSphere Password Reset OTP',
                body=f'Your OTP is {otp}'
            )

            return redirect(
                url_for(
                    'forgototp',
                    role=role
                )
            )

        flash("Email not registered")

    return render_template(
        'forgot.html',
        role=role
    )




@app.route('/forgototp/<role>', methods=['GET','POST'])
def forgototp(role):

    if request.method == 'POST':

        userotp = request.form['otp']

        if userotp == str(session.get('otp')):

            token = endata(
                session['email']
            )

            return redirect(
                url_for(
                    'newpassword',
                    role=role,
                    data=token
                )
            )

        flash("Invalid OTP")

    return render_template(
        'forgototp.html',
        role=role
    )

@app.route('/signupotp/<role>', methods=['GET','POST'])
def signupotp(role):

    if request.method == 'POST':

        otp = request.form['otp']

        if otp == str(session.get('signup_otp')):

            data = session['signup_data']

            hashed = bcrypt.generate_password_hash(
                data['password']
            ).decode('utf-8')

            cursor = mydb.cursor()

            if role == 'user':

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

                    VALUES(%s,%s,%s,%s,%s)
                    """,

                    (
                        userid,
                        data['name'],
                        data['email'],
                        data['address'],
                        hashed
                    )
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
            
                    VALUES(%s,%s,%s,%s,%s)
                    """,
            
                    (
                        adminid,
                        data['name'],
                        data['email'],
                        data['address'],
                        hashed
                    )
                )                  
            mydb.commit()

            flash("Account created successfully")

            return redirect(
                url_for(
                    'login',
                    role=role
                )
            )

        flash("Invalid OTP")

    return render_template(
        'otp.html',
        role=role
    )


@app.route(
    '/newpassword/<role>/<data>',
    methods=['GET','POST']
)
def newpassword(role,data):

    email = dndata(data)

    if request.method == 'POST':

        password = request.form['password']

        hashed = bcrypt.generate_password_hash(
            password
        ).decode('utf-8')

        cursor = mydb.cursor()

        if role == 'user':

            cursor.execute(
                '''
                update userdata
                set userpassword=%s
                where useremail=%s
                ''',
                [hashed,email]
            )

        else:

            cursor.execute(
                '''
                update admindata
                set admin_password=%s
                where admin_useremail=%s
                ''',
                [hashed,email]
            )

        mydb.commit()

        flash("Password updated successfully")

        return redirect(
            url_for(
                'login',
                role=role
            )
        )

    return render_template(
        'newpassword.html',
        role=role,
        data=data
    )

@app.route('/admin/dashboard')
def admindashboard():

    if 'admin' not in session:

        return redirect(
            url_for(
                'login',
                role='admin'
            )
        )

    return render_template(
        'admindashboard.html'
    )

@app.route('/admin/additem',methods=['GET','POST'])
def additem():

    if 'admin' not in session:

        return redirect(
            url_for(
                'login',
                role='admin'
            )
        )

    if request.method == 'POST':

        item_name=request.form['item_name']

        item_description=request.form['item_description']

        item_about=request.form['item_about']

        item_price=request.form['item_price']

        item_quantity=request.form['item_quantity']

        item_category=request.form['item_category']

        image=request.files['image']


        filename=secure_filename(
            image.filename
        )


        image.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )


        itemid=uuid.uuid4().bytes


        cursor=mydb.cursor()


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

            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
            """,

            (

            itemid,

            item_name,

            item_description,

            item_about,

            item_price,

            item_quantity,

            item_category,

            filename

            )

        )

        mydb.commit()

        flash(
            "Product added successfully"
        )

        return redirect(
            url_for(
                'viewallitems'
            )
        )

    return render_template(
        'admin_addproduct.html'
    )

@app.route('/admin/logout')
def adminlogout():

    session.pop(
        'admin',
        None
    )

    return redirect(
        url_for(
            'login',
            role='admin'
        )
    )

@app.route('/admin/products')
def viewallitems():

    if 'admin' not in session:

        flash('Please login')

        return redirect(
            url_for(
                'login',
                role='admin'
            )
        )

    search = request.args.get(
        'search',
        ''
    )

    cursor = mydb.cursor()

    if search:

        cursor.execute(
            """
            SELECT *
            FROM items

            WHERE item_name LIKE %s

            ORDER BY created_at DESC
            """,

            ['%'+search+'%']
        )

    else:

        cursor.execute(
            """
            SELECT *

            FROM items

            ORDER BY created_at DESC
            """
        )

    products = cursor.fetchall()

    new_products = []
    
    for row in products:
    
        row = list(row)
    
        # Convert Binary UUID to String UUID
        row[0] = str(uuid.UUID(bytes=row[0]))
    
        new_products.append(row)
        print(new_products[0][0])
        print(type(new_products[0][0]))
    
    return render_template(
        "admin_viewallitems.html",
        products=new_products,
        search=search
    )
    

@app.route('/viewproduct/<itemid>')
def viewproduct(itemid):

    print("="*60)
    print("Received itemid :", itemid)
    print("Type :", type(itemid))
    print("Length :", len(itemid))
    print("="*60)

    itemid = uuid.UUID(itemid).bytes

    cursor = mydb.cursor()

    cursor.execute("""
        SELECT *
        FROM items
        WHERE itemid=%s
    """,(itemid,))

    product = cursor.fetchone()

    return render_template(
        "admin_viewproduct.html",
        product=product
    )

@app.route('/editproduct/<itemid>', methods=['GET', 'POST'])
def editproduct(itemid):

    if 'admin' not in session:
        return redirect(url_for('login', role='admin'))

    itemid = uuid.UUID(itemid).bytes

    cursor = mydb.cursor()

    if request.method == 'POST':

        item_name = request.form['item_name']
        item_description = request.form['item_description']
        item_about = request.form['item_about']
        item_price = request.form['item_price']
        item_quantity = request.form['item_quantity']
        item_category = request.form['item_category']

        image = request.files['image']

        # Get existing filename
        cursor.execute(
            """
            SELECT item_filename
            FROM items
            WHERE itemid=%s
            """,
            (itemid,)
        )

        old_image = cursor.fetchone()[0]

        filename = old_image

        if image and image.filename != "":

            filename = secure_filename(image.filename)

            image.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    filename
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
                itemid
            )
        )

        mydb.commit()

        flash("Product Updated Successfully")

        return redirect(url_for('viewallitems'))

    cursor.execute(
        """
        SELECT *

        FROM items

        WHERE itemid=%s
        """,
        (itemid,)
    )

    product = list(cursor.fetchone())

    product[0] = str(uuid.UUID(bytes=product[0]))

    return render_template(
        'admin_editproduct.html',
        product=product
    )

    cursor = mydb.cursor()

    ...
    if request.method=='POST':

        item_name=request.form['item_name']

        item_description=request.form['item_description']

        item_about=request.form['item_about']

        item_price=request.form['item_price']

        item_quantity=request.form['item_quantity']

        item_category=request.form['item_category']


        cursor.execute(

        """

        UPDATE items

        SET

        item_name=%s,

        item_description=%s,

        item_about=%s,

        item_price=%s,

        item_quantity=%s,

        item_category=%s

        WHERE itemid=%s

        """,

        (

        item_name,

        item_description,

        item_about,

        item_price,

        item_quantity,

        item_category,

        itemid

        )

        )

        mydb.commit()


        flash(

        'Updated successfully'

        )


        return redirect(

        url_for(

        'viewallitems'

        )

        )


    cursor.execute(

    """

    SELECT *

    FROM items

    WHERE itemid=%s

    """,

    [itemid]

    )

    product=cursor.fetchone()


    return render_template(

    'admin_editproduct.html',

    product=product

    )
@app.route('/deleteproduct/<itemid>')
def deleteproduct(itemid):

    itemid = uuid.UUID(itemid).bytes

    cursor = mydb.cursor()

    cursor.execute(
        """
        DELETE FROM items
        WHERE itemid=%s
        """,
        (itemid,)
    )

    mydb.commit()

    flash("Product deleted")

    return redirect(url_for("viewallitems"))

    
@app.route('/admin/orders')
def adminorders():

    if 'admin' not in session:

        return redirect(
            url_for(
                'login',
                role='admin'
            )
        )

    cursor=mydb.cursor()

    cursor.execute(
        """

        SELECT

        orders.orderid,

        userdata.username,

        orders.total_amount,

        orders.order_status,

        orders.created_at

        FROM orders

        JOIN userdata

        ON orders.userid=userdata.userid

        ORDER BY orders.created_at DESC

        """
    )

    orders=cursor.fetchall()

    return render_template(

        'admin_orders.html',

        orders=orders

    )

@app.route('/admin/customers')

def admincustomers():

    if 'admin' not in session:

        return redirect(

            url_for(

                'login',

                role='admin'

            )
        )

    cursor=mydb.cursor()

    cursor.execute(
        """

        SELECT

        u.userid,

        u.username,

        u.userphone,

        COUNT(o.orderid),

        COALESCE(

        SUM(o.total_amount),

        0

        )

        FROM userdata u

        LEFT JOIN orders o

        ON u.userid=o.userid

        GROUP BY

        u.userid,

        u.username,

        u.userphone

        ORDER BY

        COUNT(o.orderid)

        DESC

        """
    )

    customers=cursor.fetchall()

    return render_template(

        'admin_customers.html',

        customers=customers

    )


import uuid
from flask import session, redirect, url_for, flash

@app.route('/addtocart/<itemid>')
def addtocart(itemid):

    if 'userid' not in session:
        flash("Please login first.")
        return redirect(url_for('login', role='user'))

    userid = session['userid']

    itemid = uuid.UUID(itemid).bytes

    cursor = mydb.cursor()

    cursor.execute(
        """
        SELECT quantity
        FROM cart
        WHERE userid=%s
        AND itemid=%s
        """,
        (userid, itemid)
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
            (userid, itemid)
        )

    else:

        cartid = uuid.uuid4().bytes

        cursor.execute(
            """
            INSERT INTO cart
            VALUES(%s,%s,%s,%s,NOW())
            """,
            (
                cartid,
                userid,
                itemid,
                1
            )
        )

    mydb.commit()

    flash("Product added to cart.")

    return redirect(request.referrer or url_for('home'))

@app.route('/cart')
def cart():

    if 'userid' not in session:

        flash("Please login.")

        return redirect(
            url_for(
                'login',
                role='user'
            )
        )

    cursor = mydb.cursor()

    cursor.execute(
        """
        SELECT

            cart.cartid,

            items.itemid,

            items.item_name,

            items.item_price,

            items.item_filename,

            cart.quantity,

            (items.item_price * cart.quantity) AS total

        FROM cart

        JOIN items

        ON cart.itemid = items.itemid

        WHERE cart.userid=%s
        """,

        (session['userid'],)

    )

    cart_items = cursor.fetchall()

    grand_total = sum(float(item[6]) for item in cart_items)

    return render_template(

        "cart.html",

        cart_items=cart_items,

        grand_total=grand_total

    )

@app.route('/removefromcart/<cartid>')
def removefromcart(cartid):

    cursor = mydb.cursor()

    cursor.execute(

        """
        DELETE FROM cart
        WHERE cartid=%s
        """,

        (uuid.UUID(cartid).bytes,)

    )

    mydb.commit()

    flash("Product removed.")

    return redirect(url_for('cart'))

@app.route('/increase/<cartid>')
def increase(cartid):

    cursor = mydb.cursor()

    cursor.execute(

        """
        UPDATE cart

        SET quantity = quantity + 1

        WHERE cartid=%s
        """,

        (uuid.UUID(cartid).bytes,)

    )

    mydb.commit()

    return redirect(url_for('cart'))

@app.route('/decrease/<cartid>')
def decrease(cartid):

    cursor = mydb.cursor()

    cursor.execute(

        """
        UPDATE cart

        SET quantity = quantity - 1

        WHERE cartid=%s

        AND quantity>1
        """,

        (uuid.UUID(cartid).bytes,)

    )

    mydb.commit()

    return redirect(url_for('cart'))

@app.route('/addtocartajax/<itemid>', methods=['POST'])
def addtocartajax():

    if 'userid' not in session:

        return {
            "status": "login"
        }

    userid = session['userid']

    itemid = request.view_args['itemid']

    itemid = uuid.UUID(itemid).bytes

    cursor = mydb.cursor()

    cursor.execute(
        """
        SELECT quantity
        FROM cart
        WHERE userid=%s
        AND itemid=%s
        """,
        (userid, itemid)
    )

    cart = cursor.fetchone()

    if cart:

        cursor.execute(
            """
            UPDATE cart
            SET quantity=quantity+1
            WHERE userid=%s
            AND itemid=%s
            """,
            (userid, itemid)
        )

    else:

        cartid = uuid.uuid4().bytes

        cursor.execute(
            """
            INSERT INTO cart
            VALUES(%s,%s,%s,%s,NOW())
            """,
            (
                cartid,
                userid,
                itemid,
                1
            )
        )

    mydb.commit()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM cart
        WHERE userid=%s
        """,
        (userid,)
    )

    count = cursor.fetchone()[0]

    return {

        "status":"success",

        "cart_count":count

    }

@app.route("/checkout")
def checkout():

    if "userid" not in session:

        return redirect(url_for("login",role="user"))

    cursor=mydb.cursor()

    cursor.execute("""

    SELECT

    cart.cartid,

    items.itemid,

    items.item_name,

    items.item_price,

    items.item_filename,

    cart.quantity,

    items.item_price*cart.quantity

    FROM cart

    JOIN items

    ON cart.itemid=items.itemid

    WHERE cart.userid=%s

    """,(session["userid"],))

    cart_items=cursor.fetchall()

    grand_total=sum(float(i[6]) for i in cart_items)

    amount=int(grand_total*100)

    razor_order=client.order.create({

        "amount":amount,

        "currency":"INR",

        "payment_capture":1

    })

    return render_template(

        "checkout.html",

        cart_items=cart_items,

        grand_total=grand_total,

        razor_order=razor_order,

        razor_key="rzp_test_T7jGp4Wq6s8Bc5"

    )


@app.route('/product/<itemid>')
def productdetails(itemid):

    try:

        itemid = uuid.UUID(itemid).bytes

    except ValueError:

        flash("Invalid Product")

        return redirect(url_for('home'))

    cursor = mydb.cursor(dictionary=True)

    # =====================================================
    # PRODUCT DETAILS
    # =====================================================

    cursor.execute("""
        SELECT *
        FROM items
        WHERE itemid=%s
    """, (itemid,))

    product = cursor.fetchone()

    if not product:

        flash("Product not found.")

        return redirect(url_for('home'))

    # =====================================================
    # ALL REVIEWS
    # =====================================================

    cursor.execute("""
        SELECT

            ir.*,

            u.username

        FROM item_reviews ir

        JOIN userdata u

        ON ir.userid=u.userid

        WHERE ir.itemid=%s

        ORDER BY ir.created_at DESC
    """, (itemid,))

    reviews = cursor.fetchall()

    # =====================================================
    # AVERAGE RATING
    # =====================================================

    cursor.execute("""
        SELECT

            AVG(rating),

            COUNT(*)

        FROM item_reviews

        WHERE itemid=%s
    """, (itemid,))

    rating_data = cursor.fetchone()

    avg_rating = rating_data["AVG(rating)"] or 0

    review_count = rating_data["COUNT(*)"]

    # =====================================================
    # RATING PERCENTAGE
    # =====================================================

    cursor.execute("""
        SELECT

            rating,

            COUNT(*) AS total

        FROM item_reviews

        WHERE itemid=%s

        GROUP BY rating
    """, (itemid,))

    rating_rows = cursor.fetchall()

    rating_percentage = {

        5:0,

        4:0,

        3:0,

        2:0,

        1:0

    }

    if review_count > 0:

        for row in rating_rows:

            rating_percentage[row["rating"]] = round(

                (row["total"] / review_count) * 100

            )

    # =====================================================
    # RELATED PRODUCTS
    # =====================================================

    cursor.execute("""
        SELECT *

        FROM items

        WHERE item_category=%s

        AND itemid!=%s

        LIMIT 4
    """,

    (

        product["item_category"],

        itemid

    ))

    related_products = cursor.fetchall()

    # =====================================================
    # CAN REVIEW
    # =====================================================
    
    can_review = False
    
    if "userid" in session:
    
        # Check if the customer purchased the product
    
        cursor.execute("""
            SELECT oi.orderitemid
    
            FROM order_items oi
    
            JOIN orders o
    
            ON oi.orderid = o.orderid
    
            WHERE
    
                o.userid = %s
    
            AND
    
                oi.itemid = %s
    
            AND
    
                o.payment_status='Paid'
    
            LIMIT 1
        """,
        (
            session["userid"],
            itemid
        ))
    
        purchased = cursor.fetchone()
    
        if purchased:
    
            # Check if the customer already reviewed it
    
            cursor.execute("""
                SELECT reviewid
    
                FROM item_reviews
    
                WHERE
    
                    userid=%s
    
                AND
    
                    itemid=%s
    
                LIMIT 1
            """,
            (
                session["userid"],
                itemid
            ))
    
            existing_review = cursor.fetchone()
    
            if existing_review:
    
                can_review = False
    
            else:
    
                can_review = True
    
    # =====================================================
    # RENDER TEMPLATE
    # =====================================================

    return render_template(

        "product_details.html",

        product=product,

        reviews=reviews,

        avg_rating=avg_rating,

        review_count=review_count,

        rating_percentage=rating_percentage,

        related_products=related_products,

        can_review=can_review

    )

if __name__ == "__main__":
    app.run(debug=True)