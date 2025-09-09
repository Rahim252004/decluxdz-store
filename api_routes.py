from flask import jsonify, request, session
from app import app, db, csrf
from models import Product, Category, Order, OrderItem, Customer, Admin
from utils import generate_order_number
from werkzeug.security import check_password_hash
from datetime import datetime

# Customer API endpoints (no authentication required)

@app.route('/api/products', methods=['GET'])
def api_get_products():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    per_page = request.args.get('per_page', 12, type=int)
    
    query = Product.query.filter_by(in_stock=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(Product.name.contains(search) | 
                           Product.name_ar.contains(search))
    
    products = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'products': [{
            'id': p.id,
            'name': p.name,
            'name_ar': p.name_ar,
            'description': p.description,
            'description_ar': p.description_ar,
            'price': p.price,
            'category_id': p.category_id,
            'image_url': p.image_url,
            'featured': p.featured
        } for p in products.items],
        'total': products.total,
        'pages': products.pages,
        'current_page': products.page,
        'has_next': products.has_next,
        'has_prev': products.has_prev
    })

@app.route('/api/products/<int:id>', methods=['GET'])
def api_get_product(id):
    product = Product.query.get_or_404(id)
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'name_ar': product.name_ar,
        'description': product.description,
        'description_ar': product.description_ar,
        'price': product.price,
        'category_id': product.category_id,
        'image_url': product.image_url,
        'additional_images': product.additional_images,
        'in_stock': product.in_stock,
        'featured': product.featured
    })

@app.route('/api/cart', methods=['GET'])
def api_get_cart():
    if 'cart' not in session:
        return jsonify({'items': [], 'total': 0})
    
    cart_items = []
    total = 0
    
    for product_id, quantity in session['cart'].items():
        product = Product.query.get(int(product_id))
        if product and product.in_stock:
            item_total = product.price * quantity
            cart_items.append({
                'product_id': product.id,
                'name': product.name,
                'name_ar': product.name_ar,
                'price': product.price,
                'quantity': quantity,
                'total': item_total,
                'image_url': product.image_url
            })
            total += item_total
    
    return jsonify({'items': cart_items, 'total': total})

@app.route('/api/cart', methods=['POST'])
@csrf.exempt
def api_add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return jsonify({'error': 'Product ID required'}), 400
    
    product = Product.query.get(product_id)
    if not product or not product.in_stock:
        return jsonify({'error': 'Product not available'}), 404
    
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        cart[product_id_str] += quantity
    else:
        cart[product_id_str] = quantity
    
    session['cart'] = cart
    
    return jsonify({'message': 'Product added to cart', 'cart_count': sum(cart.values())})

@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    data = request.get_json()
    
    required_fields = ['name', 'phone', 'address', 'wilaya']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if 'cart' not in session or not session['cart']:
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Calculate total and prepare items
    total = 0
    cart_items = []
    
    for product_id, quantity in session['cart'].items():
        product = Product.query.get(int(product_id))
        if product and product.in_stock:
            item_total = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': product.price
            })
            total += item_total
    
    if not cart_items:
        return jsonify({'error': 'No available products in cart'}), 400
    
    try:
        # Create or get customer
        customer = Customer.query.filter_by(phone=data['phone']).first()
        if not customer:
            customer = Customer(
                name=data['name'],
                phone=data['phone'],
                email=data.get('email')
            )
            db.session.add(customer)
            db.session.flush()
        
        # Create order
        order = Order(
            order_number=generate_order_number(),
            customer_id=customer.id,
            total_amount=total,
            address=data['address'],
            wilaya=data['wilaya'],
            notes=data.get('notes', '')
        )
        db.session.add(order)
        db.session.flush()
        
        # Create order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product'].id,
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        # Clear cart
        session['cart'] = {}
        
        return jsonify({
            'message': 'Order created successfully',
            'order_number': order.order_number,
            'total_amount': total
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create order'}), 500

@app.route('/api/orders/<order_id>', methods=['GET'])
def api_get_order(order_id):
    order = Order.query.filter_by(order_number=order_id).first()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify({
        'order_number': order.order_number,
        'status': order.status,
        'total_amount': order.total_amount,
        'address': order.address,
        'wilaya': order.wilaya,
        'created_at': order.created_at.isoformat(),
        'items': [{
            'product_name': item.product.name_ar,
            'quantity': item.quantity,
            'price': item.price
        } for item in order.items]
    })

# Admin API endpoints (authentication required)

def api_admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    admin = Admin.query.filter_by(username=username).first()
    
    if admin and admin.check_password(password):
        session['admin_id'] = admin.id
        session['admin_username'] = admin.username
        return jsonify({'message': 'Login successful', 'admin_id': admin.id})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/admin/products', methods=['POST'])
@api_admin_required
def api_admin_add_product():
    data = request.get_json()
    
    required_fields = ['name', 'name_ar', 'price', 'category_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        product = Product(
            name=data['name'],
            name_ar=data['name_ar'],
            description=data.get('description', ''),
            description_ar=data.get('description_ar', ''),
            price=float(data['price']),
            category_id=int(data['category_id']),
            image_url=data.get('image_url'),
            in_stock=data.get('in_stock', True),
            featured=data.get('featured', False)
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product added successfully',
            'product_id': product.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add product'}), 500

@app.route('/api/admin/products/<int:id>', methods=['PUT'])
@api_admin_required
def api_admin_update_product(id):
    product = Product.query.get_or_404(id)
    data = request.get_json()
    
    try:
        if 'name' in data:
            product.name = data['name']
        if 'name_ar' in data:
            product.name_ar = data['name_ar']
        if 'description' in data:
            product.description = data['description']
        if 'description_ar' in data:
            product.description_ar = data['description_ar']
        if 'price' in data:
            product.price = float(data['price'])
        if 'category_id' in data:
            product.category_id = int(data['category_id'])
        if 'image_url' in data:
            product.image_url = data['image_url']
        if 'in_stock' in data:
            product.in_stock = data['in_stock']
        if 'featured' in data:
            product.featured = data['featured']
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Product updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update product'}), 500

@app.route('/api/admin/products/<int:id>', methods=['DELETE'])
@api_admin_required
def api_admin_delete_product(id):
    product = Product.query.get_or_404(id)
    
    # Check if product has orders
    if OrderItem.query.filter_by(product_id=id).first():
        return jsonify({'error': 'Cannot delete product with existing orders'}), 400
    
    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete product'}), 500

@app.route('/api/admin/orders', methods=['GET'])
@api_admin_required
def api_admin_get_orders():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status')
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Order.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'orders': [{
            'id': o.id,
            'order_number': o.order_number,
            'customer_name': o.customer.name,
            'customer_phone': o.customer.phone,
            'total_amount': o.total_amount,
            'status': o.status,
            'address': o.address,
            'wilaya': o.wilaya,
            'created_at': o.created_at.isoformat(),
            'item_count': len(o.items)
        } for o in orders.items],
        'total': orders.total,
        'pages': orders.pages,
        'current_page': orders.page
    })

@app.route('/api/admin/orders/<int:id>', methods=['PUT'])
@api_admin_required
def api_admin_update_order(id):
    order = Order.query.get_or_404(id)
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
    
    valid_statuses = ['pending', 'in_delivery', 'delivered']
    if data['status'] not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400
    
    try:
        order.status = data['status']
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Order status updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update order'}), 500

@app.route('/api/admin/customers', methods=['GET'])
@api_admin_required
def api_admin_get_customers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Customer.query
    
    if search:
        query = query.filter(Customer.name.contains(search) | 
                           Customer.phone.contains(search))
    
    customers = query.order_by(Customer.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'customers': [{
            'id': c.id,
            'name': c.name,
            'phone': c.phone,
            'email': c.email,
            'created_at': c.created_at.isoformat(),
            'order_count': len(c.orders),
            'total_spent': sum(order.total_amount for order in c.orders)
        } for c in customers.items],
        'total': customers.total,
        'pages': customers.pages,
        'current_page': customers.page
    })

@app.route('/api/admin/analytics', methods=['GET'])
@api_admin_required
def api_admin_get_analytics():
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Basic stats
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_customers = Customer.query.count()
    total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0
    
    # Top products
    top_products = db.session.query(
        Product.name_ar,
        func.sum(OrderItem.quantity).label('total_sold')
    ).join(OrderItem).group_by(Product.id).order_by(
        func.sum(OrderItem.quantity).desc()
    ).limit(10).all()
    
    # Sales by province
    sales_by_province = db.session.query(
        Order.wilaya,
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('total_revenue')
    ).group_by(Order.wilaya).order_by(
        func.sum(Order.total_amount).desc()
    ).limit(10).all()
    
    return jsonify({
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_revenue': float(total_revenue),
        'top_products': [
            {'name': p.name_ar, 'sold': p.total_sold} 
            for p in top_products
        ],
        'sales_by_province': [
            {
                'province': s.wilaya,
                'order_count': s.order_count,
                'revenue': float(s.total_revenue)
            } for s in sales_by_province
        ]
    })
