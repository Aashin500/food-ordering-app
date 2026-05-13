from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import bcrypt

app = Flask(__name__)
app.secret_key = 'foodappsecret'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root123@localhost/foodapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# USER TABLE
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(255))


# ORDER TABLE
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    food_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    total_price = db.Column(db.Integer)
    status = db.Column(db.String(50), default='Pending')


# FOOD TABLE
class Food(db.Model):
    __tablename__ = 'foods'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    image = db.Column(db.String(500))


# ADMIN TABLE
class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(255))


# CREATE DEFAULT FOOD ITEMS AND ADMIN
def setup_default_data():
    with app.app_context():
        db.create_all()

        if Food.query.count() == 0:
            foods = [
                Food(
                    name='Burger',
                    price=120,
                    image='https://images.unsplash.com/photo-1568901346375-23c9450c58cd'
                ),
                Food(
                    name='Pizza',
                    price=250,
                    image='https://images.unsplash.com/photo-1513104890138-7c749659a591'
                ),
                Food(
                    name='French Fries',
                    price=90,
                    image='https://images.unsplash.com/photo-1573080496219-bb080dd4f877'
                )
            ]

            db.session.add_all(foods)
            db.session.commit()

        if Admin.query.count() == 0:
            password = bcrypt.hashpw(
                'admin123'.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            admin = Admin(
                username='admin',
                password=password
            )

            db.session.add(admin)
            db.session.commit()


# HOME
@app.route('/')
def home():
    return render_template('index.html')


# REGISTER PAGE
@app.route('/register')
def register():
    return render_template('register.html')


# SAVE USER
@app.route('/save_user', methods=['POST'])
def save_user():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    hashed_password = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    new_user = User(
        username=username,
        email=email,
        password=hashed_password
    )

    db.session.add(new_user)
    db.session.commit()

    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Registration Success</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body style="background-color:#0f0f0f;">
<div class="container">
    <div class="row justify-content-center align-items-center vh-100">
        <div class="col-md-6">
            <div class="card border-0 shadow-lg" style="background-color:#1a1a1a; border-radius:20px;">
                <div class="card-body text-center p-5">
                    <h1 style="color:#d4af37; font-size:70px;">✓</h1>
                    <h2 style="color:#d4af37;">Registration Successful</h2>
                    <p style="color:#cccccc;">Your account has been created successfully.</p>
                    <a href="/login" class="btn btn-lg mt-3" style="background-color:#d4af37; color:black; font-weight:bold;">
                        Go To Login
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
'''


# LOGIN PAGE
@app.route('/login')
def login():
    return render_template('login.html')


# LOGIN USER
@app.route('/login_user', methods=['POST'])
def login_user():
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email).first()

    if user:
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session['user'] = user.username
            session['cart_count'] = {}
            session['cart_items'] = []
            return redirect('/dashboard')

    return '''
<h1 style="color:red; text-align:center; margin-top:100px;">
Invalid Email or Password
</h1>
<center><a href="/login">Try Again</a></center>
'''


# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']
    foods = Food.query.all()

    cart_count = session.get('cart_count', {})
    cart_items = session.get('cart_items', [])

    cart_added_count = {}

    for item in cart_items:
        cart_added_count[str(item['id'])] = item['quantity']

    total_cart_items = sum(item['quantity'] for item in cart_items)

    food_cards = ""

    for food in foods:
        selected_quantity = cart_count.get(str(food.id), 0)
        added_quantity = cart_added_count.get(str(food.id), 0)
        quantity = selected_quantity + added_quantity

        food_cards += f"""
        <div class="col-md-4">
            <div class="card border-0 shadow-lg" style="background-color:#1a1a1a;">
                <img src="{food.image}" class="card-img-top" height="250" style="object-fit:cover;">

                <div class="card-body">
                    <h4 style="color:#d4af37;">{food.name}</h4>
                    <h5 style="color:white;">₹{food.price}</h5>

                    <div class="d-flex justify-content-center align-items-center gap-3 mt-4">
                        <a href="/decrease/{food.id}" class="btn" style="background-color:#d4af37; color:black; font-weight:bold;">-</a>

                        <span class="badge bg-dark text-white fs-5 px-3 py-2">{quantity}</span>

                        <a href="/increase/{food.id}" class="btn" style="background-color:#d4af37; color:black; font-weight:bold;">+</a>
                    </div>

                    <a href="/add_to_cart/{food.id}" class="btn w-100 mt-4" style="background-color:#d4af37; color:black; font-weight:bold;">
                        🛒 Add To Cart
                    </a>
                </div>
            </div>
        </div>
        """

    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body style="background-color:#0f0f0f; color:white;">

<nav class="navbar navbar-expand-lg" style="background-color:#1a1a1a;">
    <div class="container">
        <a class="navbar-brand" style="color:#d4af37; font-size:28px; font-weight:bold;">🍔 Food Ordering App</a>

        <div>
            <span style="margin-right:20px;">Welcome, {username}</span>

            <a href="/cart" class="btn me-2" style="background-color:#d4af37; color:black; font-weight:bold;">
                🛒 Cart ({total_cart_items})
            </a>

            <a href="/admin_login" class="btn me-2" style="border:1px solid #d4af37; color:#d4af37;">
                Admin
            </a>

            <a href="/logout" class="btn btn-danger">Logout</a>
        </div>
    </div>
</nav>

<div class="container mt-5">
    <div class="p-5 rounded" style="background:linear-gradient(to right,#d4af37,#8b6914);">
        <h1 class="fw-bold text-dark">Premium Food Experience</h1>
        <p class="text-dark fs-5">Order delicious foods instantly.</p>
    </div>
</div>

<div class="container mt-5">
    <h2 class="text-center mb-5" style="color:#d4af37;">Popular Foods</h2>
    <div class="row g-4">
        {food_cards}
    </div>
</div>

</body>
</html>
'''


# INCREASE QUANTITY
@app.route('/increase/<int:food_id>')
def increase(food_id):
    counts = session.get('cart_count', {})
    counts[str(food_id)] = counts.get(str(food_id), 0) + 1
    session['cart_count'] = counts
    return redirect('/dashboard')


# DECREASE QUANTITY
@app.route('/decrease/<int:food_id>')
def decrease(food_id):
    counts = session.get('cart_count', {})
    cart_items = session.get('cart_items', [])

    food_key = str(food_id)

    if counts.get(food_key, 0) > 0:
        counts[food_key] -= 1
        session['cart_count'] = counts
        return redirect('/dashboard')

    for item in cart_items:
        if item['id'] == food_id:
            if item['quantity'] > 1:
                item['quantity'] -= 1
            else:
                cart_items.remove(item)
            break

    session['cart_items'] = cart_items
    return redirect('/dashboard')


# ADD TO CART
@app.route('/add_to_cart/<int:food_id>')
def add_to_cart(food_id):
    counts = session.get('cart_count', {})
    qty = counts.get(str(food_id), 0)

    if qty > 0:
        cart_items = session.get('cart_items', [])

        found = False

        for item in cart_items:
            if item['id'] == food_id:
                item['quantity'] += qty
                found = True
                break

        if not found:
            cart_items.append({
                'id': food_id,
                'quantity': qty
            })

        counts[str(food_id)] = 0

        session['cart_items'] = cart_items
        session['cart_count'] = counts

    return redirect('/cart')


# CART PAGE
@app.route('/cart')
def cart():
    if 'user' not in session:
        return redirect('/login')

    cart_items = session.get('cart_items', [])

    total = 0
    cart_html = ""

    if len(cart_items) == 0:
        cart_html = '''
        <div class="card border-0 shadow-lg" style="background-color:#1a1a1a;">
            <div class="card-body text-center p-5">
                <h3 style="color:#d4af37;">Your cart is empty</h3>
                <p style="color:#cccccc;">Add food from dashboard.</p>
            </div>
        </div>
        '''

    for index, item in enumerate(cart_items):
        food = Food.query.get(item['id'])

        if food:
            subtotal = food.price * item['quantity']
            total += subtotal

            cart_html += f"""
            <div class="card mb-3 border-0 shadow-lg" style="background-color:#1a1a1a; color:white;">
                <div class="card-body d-flex justify-content-between align-items-center">
                    <img src="{food.image}" style="height:100px; width:120px; object-fit:cover;" class="rounded">

                    <div>
                        <h4 style="color:#d4af37;">{food.name}</h4>
                        <h5>₹{food.price} each</h5>
                    </div>

                    <div>
                        <a href="/remove_one/{index}" class="btn btn-danger">-</a>
                        <span class="badge bg-dark fs-5">{item['quantity']}</span>
                        <a href="/add_one/{index}" class="btn" style="background-color:#d4af37; color:black;">+</a>
                    </div>

                    <h4 style="color:#d4af37;">₹{subtotal}</h4>
                </div>
            </div>
            """

    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Cart</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body style="background-color:#0f0f0f; color:white;">

<div class="container mt-5">
    <h1 style="color:#d4af37;">Your Cart</h1>

    {cart_html}

    <div class="card mt-4" style="background-color:#d4af37; color:black;">
        <div class="card-body">
            <h3>Total: ₹{total}</h3>
        </div>
    </div>

    <a href="/place_order" class="btn btn-success btn-lg mt-4">Place Order</a>
    <a href="/dashboard" class="btn btn-lg mt-4" style="background-color:#d4af37; color:black;">Continue Shopping</a>
</div>

</body>
</html>
'''


# PLACE ORDER
@app.route('/place_order')
def place_order():
    if 'user' not in session:
        return redirect('/login')

    cart_items = session.get('cart_items', [])

    if len(cart_items) == 0:
        return redirect('/cart')

    username = session['user']

    for item in cart_items:
        food = Food.query.get(item['id'])

        if food:
            new_order = Order(
                username=username,
                food_name=food.name,
                quantity=item['quantity'],
                total_price=food.price * item['quantity'],
                status='Pending'
            )

            db.session.add(new_order)

    db.session.commit()

    session['cart_items'] = []
    session['cart_count'] = {}

    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Order Success</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body style="background-color:#0f0f0f;">
<div class="container">
    <div class="row justify-content-center align-items-center vh-100">
        <div class="col-md-6">
            <div class="card border-0 shadow-lg" style="background-color:#1a1a1a;">
                <div class="card-body text-center p-5">
                    <h1 style="color:#d4af37; font-size:70px;">✓</h1>
                    <h2 style="color:#d4af37;">Order Placed Successfully</h2>
                    <p style="color:#cccccc;">Your order is saved in database.</p>
                    <a href="/dashboard" class="btn btn-lg" style="background-color:#d4af37; color:black;">
                        Back To Dashboard
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
'''


# ADD ONE ITEM IN CART
@app.route('/add_one/<int:index>')
def add_one(index):
    cart_items = session.get('cart_items', [])

    if index < len(cart_items):
        cart_items[index]['quantity'] += 1
        session['cart_items'] = cart_items

    return redirect('/cart')


# REMOVE ONE ITEM IN CART
@app.route('/remove_one/<int:index>')
def remove_one(index):
    cart_items = session.get('cart_items', [])

    if index < len(cart_items):
        if cart_items[index]['quantity'] > 1:
            cart_items[index]['quantity'] -= 1
        else:
            cart_items.pop(index)

        session['cart_items'] = cart_items

    return redirect('/cart')


# ADMIN LOGIN
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()

        if admin and bcrypt.checkpw(password.encode('utf-8'), admin.password.encode('utf-8')):
            session['admin'] = username
            return redirect('/admin')

    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body style="background-color:#0f0f0f;">
<div class="container">
    <div class="row justify-content-center align-items-center vh-100">
        <div class="col-md-5">
            <div class="card p-5" style="background-color:#1a1a1a;">
                <h2 style="color:#d4af37;">Admin Login</h2>

                <form method="POST">
                    <input type="text" name="username" class="form-control mt-3" placeholder="Admin Username" required>
                    <input type="password" name="password" class="form-control mt-3" placeholder="Admin Password" required>

                    <button class="btn mt-4 w-100" style="background-color:#d4af37; color:black;">
                        Login
                    </button>
                </form>

        
            </div>
        </div>
    </div>
</div>
</body>
</html>
'''


# ADMIN PANEL
@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect('/admin_login')

    keyword = request.args.get('keyword', '')

    if keyword:
        orders = Order.query.filter(
            (Order.username.contains(keyword)) |
            (Order.food_name.contains(keyword)) |
            (Order.status.contains(keyword))
        ).all()
    else:
        orders = Order.query.all()

    total_sales = db.session.query(func.sum(Order.total_price)).scalar() or 0
    total_orders = Order.query.count()

    most_ordered = db.session.query(
        Order.food_name,
        func.sum(Order.quantity)
    ).group_by(Order.food_name).order_by(func.sum(Order.quantity).desc()).first()

    most_ordered_text = most_ordered[0] if most_ordered else 'No orders yet'

    order_rows = ""

    for order in orders:
        order_rows += f"""
        <tr>
            <td>{order.id}</td>
            <td>{order.username}</td>
            <td>{order.food_name}</td>
            <td>{order.quantity}</td>
            <td>₹{order.total_price}</td>
            <td>{order.status}</td>
            <td>
                <a href="/update_status/{order.id}/Pending" class="btn btn-sm btn-warning">Pending</a>
                <a href="/update_status/{order.id}/Preparing" class="btn btn-sm btn-info">Preparing</a>
                <a href="/update_status/{order.id}/Delivered" class="btn btn-sm btn-success">Delivered</a>
                <a href="/update_status/{order.id}/Cancelled" class="btn btn-sm btn-secondary">Cancelled</a>
                <a href="/delete_order/{order.id}" class="btn btn-sm btn-danger">Delete</a>
            </td>
        </tr>
        """

    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body style="background-color:#0f0f0f; color:white;">

<nav class="navbar navbar-expand-lg" style="background-color:#1a1a1a;">
    <div class="container">
        <a class="navbar-brand" style="color:#d4af37;">Admin Panel</a>

        <div>
            <a href="/admin_users" class="btn btn-outline-warning me-2">Users</a>
            <a href="/admin_foods" class="btn btn-outline-warning me-2">Foods</a>
            <a href="/dashboard" class="btn btn-warning me-2">Dashboard</a>
            <a href="/admin_logout" class="btn btn-danger">Admin Logout</a>
        </div>
    </div>
</nav>

<div class="container mt-5">

    <h1 style="color:#d4af37;">Sales Dashboard</h1>

    <div class="row mt-4">
        <div class="col-md-4">
            <div class="card p-3" style="background-color:#1a1a1a;">
                <h4>Total Sales</h4>
                <h2 style="color:#d4af37;">₹{total_sales}</h2>
            </div>
        </div>

        <div class="col-md-4">
            <div class="card p-3" style="background-color:#1a1a1a;">
                <h4>Total Orders</h4>
                <h2 style="color:#d4af37;">{total_orders}</h2>
            </div>
        </div>

        <div class="col-md-4">
            <div class="card p-3" style="background-color:#1a1a1a;">
                <h4>Most Ordered</h4>
                <h2 style="color:#d4af37;">{most_ordered_text}</h2>
            </div>
        </div>
    </div>

    <form class="mt-4" method="GET" action="/admin">
        <input type="text" name="keyword" class="form-control" placeholder="Search by username, food or status">
        <button class="btn mt-2" style="background-color:#d4af37; color:black;">Search</button>
    </form>

    <h2 class="mt-5" style="color:#d4af37;">Order Management</h2>

    <table class="table table-dark table-bordered table-striped mt-4">
        <thead>
            <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Food</th>
                <th>Qty</th>
                <th>Total</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>

        <tbody>
            {order_rows}
        </tbody>
    </table>
</div>
</body>
</html>
'''


# DELETE ORDER
@app.route('/delete_order/<int:id>')
def delete_order(id):
    order = Order.query.get(id)

    if order:
        db.session.delete(order)
        db.session.commit()

    return redirect('/admin')


# UPDATE ORDER STATUS
@app.route('/update_status/<int:id>/<status>')
def update_status(id, status):
    order = Order.query.get(id)

    if order:
        order.status = status
        db.session.commit()

    return redirect('/admin')


# USER MANAGEMENT
@app.route('/admin_users')
def admin_users():
    if 'admin' not in session:
        return redirect('/admin_login')

    users = User.query.all()

    rows = ""

    for user in users:
        rows += f"""
        <tr>
            <td>{user.id}</td>
            <td>{user.username}</td>
            <td>{user.email}</td>
            <td>
                <a href="/delete_user/{user.id}" class="btn btn-danger btn-sm">Delete</a>
            </td>
        </tr>
        """

    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>User Management</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body style="background-color:#0f0f0f; color:white;">
<div class="container mt-5">
    <h1 style="color:#d4af37;">User Management</h1>

    <table class="table table-dark table-bordered mt-4">
        <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Email</th>
            <th>Action</th>
        </tr>
        {rows}
    </table>

    <a href="/admin" class="btn" style="background-color:#d4af37; color:black;">Back Admin</a>
</div>
</body>
</html>
'''


# DELETE USER
@app.route('/delete_user/<int:id>')
def delete_user(id):
    user = User.query.get(id)

    if user:
        db.session.delete(user)
        db.session.commit()

    return redirect('/admin_users')


# FOOD MANAGEMENT
@app.route('/admin_foods')
def admin_foods():
    if 'admin' not in session:
        return redirect('/admin_login')

    foods = Food.query.all()

    rows = ""

    for food in foods:
        rows += f"""
        <tr>
            <td>{food.id}</td>
            <td>{food.name}</td>
            <td>₹{food.price}</td>
            <td><img src="{food.image}" width="80"></td>
            <td>
                <a href="/delete_food/{food.id}" class="btn btn-danger btn-sm">Delete</a>
            </td>
        </tr>
        """

    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Food Management</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body style="background-color:#0f0f0f; color:white;">
<div class="container mt-5">

    <h1 style="color:#d4af37;">Food Management</h1>

    <form action="/add_food" method="POST" class="mt-4">
        <input type="text" name="name" class="form-control mt-2" placeholder="Food Name" required>
        <input type="number" name="price" class="form-control mt-2" placeholder="Price" required>
        <input type="text" name="image" class="form-control mt-2" placeholder="Image URL" required>

        <button class="btn mt-3" style="background-color:#d4af37; color:black;">
            Add Food
        </button>
    </form>

    <table class="table table-dark table-bordered mt-4">
        <tr>
            <th>ID</th>
            <th>Food</th>
            <th>Price</th>
            <th>Image</th>
            <th>Action</th>
        </tr>
        {rows}
    </table>

    <a href="/admin" class="btn" style="background-color:#d4af37; color:black;">Back Admin</a>

</div>
</body>
</html>
'''


# ADD FOOD
@app.route('/add_food', methods=['POST'])
def add_food():
    if 'admin' not in session:
        return redirect('/admin_login')

    food = Food(
        name=request.form['name'],
        price=request.form['price'],
        image=request.form['image']
    )

    db.session.add(food)
    db.session.commit()

    return redirect('/admin_foods')


# DELETE FOOD
@app.route('/delete_food/<int:id>')
def delete_food(id):
    if 'admin' not in session:
        return redirect('/admin_login')

    food = Food.query.get(id)

    if food:
        db.session.delete(food)
        db.session.commit()

    return redirect('/admin_foods')


# ADMIN LOGOUT
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/admin_login')


# USER LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('cart_count', None)
    session.pop('cart_items', None)

    return redirect('/login')


if __name__ == '__main__':
    setup_default_data()
    app.run(debug=True)