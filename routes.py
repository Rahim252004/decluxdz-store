from flask import render_template, request, redirect, url_for, session, flash, jsonify,send_from_directory
from app import app, db
from models import Product, Category, Order, OrderItem, Customer, Contact
from forms import CheckoutForm, ContactForm
from utils import generate_order_number
import json

@app.route('/')
def index():
    featured_products = Product.query.filter_by(featured=True, in_stock=True).limit(8).all()
    categories = Category.query.all()
    return render_template('index.html', 
                         featured_products=featured_products, 
                         categories=categories)

@app.route('/shop')
def shop():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    
    query = Product.query.filter_by(in_stock=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(Product.name.contains(search) | 
                           Product.name_ar.contains(search))
    
    products = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.all()
    
    return render_template('shop.html', 
                         products=products, 
                         categories=categories,
                         current_category=category_id,
                         search_query=search)

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.in_stock == True
    ).limit(4).all()
    
    additional_images = []
    if product.additional_images:
        try:
            additional_images = json.loads(product.additional_images)
        except:
            additional_images = []
    
    return render_template('product_detail.html', 
                         product=product, 
                         related_products=related_products,
                         additional_images=additional_images)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    
    product = Product.query.get_or_404(product_id)
    
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        cart[product_id_str] += quantity
    else:
        cart[product_id_str] = quantity
    
    session['cart'] = cart
    flash(f'تم إضافة {product.name_ar} إلى السلة', 'success')
    
    return redirect(request.referrer or url_for('shop'))

@app.route('/cart')
def cart():
    if 'cart' not in session or not session['cart']:
        return render_template('cart.html', cart_items=[], total=0)
    
    cart_items = []
    total = 0
    
    for product_id, quantity in session['cart'].items():
        product = Product.query.get(int(product_id))
        if product and product.in_stock:
            item_total = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity', type=int)
    
    if 'cart' in session and product_id in session['cart']:
        if quantity > 0:
            session['cart'][product_id] = quantity
        else:
            del session['cart'][product_id]
        session.modified = True
    
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' in session and str(product_id) in session['cart']:
        del session['cart'][str(product_id)]
        session.modified = True
        flash('تم حذف المنتج من السلة', 'success')
    
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('السلة فارغة', 'error')
        return redirect(url_for('cart'))
    
    form = CheckoutForm()
    
    if form.validate_on_submit():
        # Calculate total
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
            flash('لا توجد منتجات متاحة في السلة', 'error')
            return redirect(url_for('cart'))
        
        # Create or get customer
        customer = Customer.query.filter_by(phone=form.phone.data).first()
        if not customer:
            customer = Customer(
                name=form.name.data,
                phone=form.phone.data,
                email=form.email.data
            )
            db.session.add(customer)
            db.session.flush()
        
        # Create order
        order = Order(
            order_number=generate_order_number(),
            customer_id=customer.id,
            total_amount=total,
            address=form.address.data,
            wilaya=form.wilaya.data,
            notes=form.notes.data
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
        
        flash(f'تم إنشاء الطلب بنجاح. رقم الطلب: {order.order_number}', 'success')
        return redirect(url_for('order_success', order_number=order.order_number))
    
    # Calculate cart total for display
    cart_items = []
    total = 0
    
    for product_id, quantity in session['cart'].items():
        product = Product.query.get(int(product_id))
        if product and product.in_stock:
            item_total = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
    
    return render_template('checkout.html', form=form, cart_items=cart_items, total=total)

@app.route('/order_success/<order_number>')
def order_success(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return render_template('order_success.html', order=order)

@app.route('/track_order', methods=['GET', 'POST'])
def track_order():
    order = None
    if request.method == 'POST':
        order_number = request.form.get('order_number')
        if order_number:
            order = Order.query.filter_by(order_number=order_number).first()
            if not order:
                flash('لم يتم العثور على الطلب', 'error')
    
    return render_template('track_order.html', order=order)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    
    if form.validate_on_submit():
        contact_msg = Contact(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(contact_msg)
        db.session.commit()
        
        flash('تم إرسال رسالتك بنجاح. سنتواصل معك قريباً', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html', form=form)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files (images) from the uploads directory"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.context_processor
def inject_cart_count():
    cart_count = 0
    if 'cart' in session:
        cart_count = sum(session['cart'].values())
    return {'cart_count': cart_count}
