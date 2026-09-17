from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'my_online_store'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_online_store'

mysql = MySQL(app)

@app.route('/')
def index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
    cursor.execute('SELECT * FROM products')
    all_products = cursor.fetchall()
    cursor.close()
    
    return render_template('index.html', products=all_products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username,password,))
        user = cursor.fetchone()
        cursor.close()
            
        if user:            
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
                                    
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Incorrect Username or Password!')            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']               
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        
        if account:
            flash('Username already exist!')
        else:            
            cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, password))
            mysql.connection.commit()
            flash('Registration successful! Please log in')
            return redirect(url_for('login'))
        cursor.close()
        
    return render_template('register.html')

@app.route('/logout')
def logout():    
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('login'))

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'loggedin' not in session:
        flash('Log in to add items to the cart')
        return redirect(url_for('login'))
    
    user_id = session['id']
    quantity = int(request.form.get('quantity', 1))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
    cursor.execute('SELECT * FROM cart WHERE user_id = %s AND product_id = %s', (user_id, product_id))
    item = cursor.fetchone()
    
    if item:        
        new_quantity = item['quantity'] + quantity
        cursor.execute('UPDATE cart SET quantity = %s WHERE id = %s', (new_quantity, item['id']))
    else:        
        cursor.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)', (user_id, product_id, quantity))
        
    mysql.connection.commit()
    cursor.close()
    
    flash('Product added to cart',)
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    if 'loggedin' not in session:
        flash('Log in to view your cart')
        return redirect(url_for('login'))
        
    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
    cursor.execute('''
        SELECT cart.id, cart.quantity, products.name, products.price, products.id AS product_id 
        FROM cart 
        JOIN products ON cart.product_id = products.id 
        WHERE cart.user_id = %s
    ''', (user_id,))
    cart_items = cursor.fetchall()
    
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    cursor.close()
    
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM cart WHERE id = %s AND user_id = %s', (cart_id, session['id']))
    mysql.connection.commit()
    cursor.close()
    
    flash('Item removed from cart')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'loggedin' not in session:
        flash('Log in to checkout')
        return redirect(url_for('login'))
        
    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
    cursor.execute('''
        SELECT cart.quantity, products.price, products.stock, products.id AS product_id 
        FROM cart 
        JOIN products ON cart.product_id = products.id 
        WHERE cart.user_id = %s
    ''', (user_id,))
    cart_items = cursor.fetchall()
    
    if not cart_items:
        flash('Your cart is empty!')
        return redirect(url_for('cart'))
        
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    
    if request.method == 'POST':        
        for item in cart_items:
            if item['quantity'] > item['stock']:
                flash(f"Insufficient stock")
                return redirect(url_for('cart'))
                
        cursor.execute('INSERT INTO orders (user_id, total_price, status) VALUES (%s, %s, %s)', (user_id, total_price, 'Processing'))
        order_id = cursor.lastrowid
                
        for item in cart_items:
            new_stock = item['stock'] - item['quantity']
            cursor.execute('UPDATE products SET stock = %s WHERE id = %s', (new_stock, item['product_id']))
                    
        cursor.execute('DELETE FROM cart WHERE user_id = %s', (user_id,))
        
        mysql.connection.commit()
        cursor.close()
        
        flash(f'Order placed successfully! Your Order ID is #{order_id}')
        return redirect(url_for('track_order_page', order_id=order_id))
        
    cursor.close()
    return render_template('checkout.html', cart_items=cart_items, total_price=total_price)

@app.route('/track_order', methods=['GET', 'POST'])
def track_order():
    if 'loggedin' not in session:
        flash('Log in to track your orders')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        if order_id:
            return redirect(url_for('track_order_page', order_id=order_id))
                
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id, total_price, status, created_at FROM orders WHERE user_id = %s ORDER BY created_at DESC', (session['id'],))
    user_orders = cursor.fetchall()
    cursor.close()
    
    return render_template('track_order.html', user_orders=user_orders)


@app.route('/track_order/<int:order_id>')
def track_order_page(order_id):
    if 'loggedin' not in session:
        flash('Log in to track order')
        return redirect(url_for('login'))
        
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
    cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()
    cursor.close()
    
    if not order:
        flash('Order ID not found')
        return redirect(url_for('track_order'))
            
    if not session.get('is_admin') and order['user_id'] != session['id']:
        flash('Unauthorized access')
        return redirect(url_for('track_order'))
        
    return render_template('track_order_id.html', order=order)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session or not session.get('is_admin'):
            flash('Access Denied: You are not an Administrator')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'POST' :        
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        image_url = request.form.get('image_url', '')
        
        cursor.execute('INSERT INTO products (name, description, price, stock, image_url) VALUES (%s, %s, %s, %s, %s)', 
                       (name, description, price, stock, image_url))
        mysql.connection.commit()
        flash(f'{name} successfully added to Product')
        return redirect(url_for('admin_dashboard'))
   
    cursor.execute('SELECT * FROM products')
    catalog_items = cursor.fetchall()
        
    cursor.execute('''
        SELECT orders.id, orders.total_price, orders.status, orders.created_at, users.username as customer_name 
        FROM orders 
        JOIN users ON orders.user_id = users.id 
        ORDER BY orders.created_at DESC
    ''')
    customer_orders = cursor.fetchall()
    cursor.close()
    
    return render_template('admin.html', products=catalog_items, orders=customer_orders)

@app.route('/admin/update_order/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order(order_id):
    new_status = request.form.get('status')
    
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE orders SET status = %s WHERE id = %s', (new_status, order_id))
    mysql.connection.commit()
    cursor.close()
    
    flash(f'Order #{order_id} status updated to {new_status}')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_product/<int:product_id>')
@admin_required
def admin_delete_product(product_id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
        mysql.connection.commit()
        flash('Product deleted successfully')
    except Exception as e:
        flash('Cannot delete product: Item is tied to an existing cart or order')
    finally:
        cursor.close()
        
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)