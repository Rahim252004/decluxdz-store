from flask import render_template, request, redirect, url_for, session, flash, jsonify
from app import app, db
from models import Admin, Product, Category, Order, Customer, Contact, OrderItem
from forms import LoginForm, ProductForm, OrderStatusForm
from werkzeug.security import check_password_hash
from utils import save_uploaded_file
import json
from datetime import datetime, timedelta
from sqlalchemy import func

def admin_required(f):
    """Decorator to require admin authentication"""
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('يجب تسجيل الدخول للوصول إلى لوحة التحكم', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        
        if admin and admin.check_password(form.password.data):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('admin/login.html', form=form)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    # Get dashboard statistics
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_customers = Customer.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Monthly revenue
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    monthly_revenue = db.session.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= thirty_days_ago
    ).scalar() or 0
    
    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         total_customers=total_customers,
                         pending_orders=pending_orders,
                         recent_orders=recent_orders,
                         monthly_revenue=monthly_revenue)

@app.route('/admin/products')
@admin_required
def admin_products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name.contains(search) | 
                           Product.name_ar.contains(search))
    
    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/products.html', products=products, search_query=search)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    form = ProductForm()
    
    # Populate category choices
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name_ar) for c in categories]
    
    if not categories:
        # Create default categories if none exist
        default_categories = [
            {'name': 'Ceiling Decorations', 'name_ar': 'ديكور أسقف'},
            {'name': 'Wall Designs', 'name_ar': 'تصاميم جدران'},
            {'name': 'Cornices', 'name_ar': 'كورنيش'},
            {'name': 'Columns', 'name_ar': 'أعمدة'},
            {'name': 'Frames', 'name_ar': 'إطارات'},
            {'name': 'Accessories', 'name_ar': 'إكسسوارات'}
        ]
        
        for cat_data in default_categories:
            category = Category(**cat_data)
            db.session.add(category)
        
        db.session.commit()
        categories = Category.query.all()
        form.category_id.choices = [(c.id, c.name_ar) for c in categories]
    
    if form.validate_on_submit():
        # Handle image upload
        image_filename = None
        if form.image.data:
            image_filename = save_uploaded_file(form.image.data)
        
        product = Product(
            name=form.name.data,
            name_ar=form.name_ar.data,
            description=form.description.data,
            description_ar=form.description_ar.data,
            price=form.price.data,
            category_id=form.category_id.data,
            image_url=image_filename,
            in_stock=form.in_stock.data,
            featured=form.featured.data
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('تم إضافة المنتج بنجاح', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/product_form.html', form=form, title='إضافة منتج جديد')

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    
    # Populate category choices
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name_ar) for c in categories]
    
    if form.validate_on_submit():
        # Handle image upload
        if form.image.data:
            image_filename = save_uploaded_file(form.image.data)
            product.image_url = image_filename
        
        product.name = form.name.data
        product.name_ar = form.name_ar.data
        product.description = form.description.data
        product.description_ar = form.description_ar.data
        product.price = form.price.data
        product.category_id = form.category_id.data
        product.in_stock = form.in_stock.data
        product.featured = form.featured.data
        product.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('تم تحديث المنتج بنجاح', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/product_form.html', form=form, product=product, title='تعديل المنتج')

@app.route('/admin/products/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_product(id):
    product = Product.query.get_or_404(id)
    
    # Check if product has orders
    if OrderItem.query.filter_by(product_id=id).first():
        flash('لا يمكن حذف المنتج لأنه مرتبط بطلبات موجودة', 'error')
        return redirect(url_for('admin_products'))
    
    db.session.delete(product)
    db.session.commit()
    
    flash('تم حذف المنتج بنجاح', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Order.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/orders.html', orders=orders, status_filter=status_filter)

@app.route('/admin/orders/<int:id>/update_status', methods=['POST'])
@admin_required
def admin_update_order_status(id):
    order = Order.query.get_or_404(id)
    form = OrderStatusForm()
    
    if form.validate_on_submit():
        order.status = form.status.data
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('تم تحديث حالة الطلب بنجاح', 'success')
    
    return redirect(url_for('admin_orders'))

@app.route('/admin/customers')
@admin_required
def admin_customers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Customer.query
    
    if search:
        query = query.filter(Customer.name.contains(search) | 
                           Customer.phone.contains(search))
    
    customers = query.order_by(Customer.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/customers.html', customers=customers, search_query=search)

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    # Top selling products
    top_products = db.session.query(
        Product.name_ar,
        func.sum(OrderItem.quantity).label('total_sold'),
        func.sum(OrderItem.quantity * OrderItem.price).label('total_revenue')
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
    ).all()
    
    # Monthly revenue trend (last 6 months)
    monthly_revenue = []
    for i in range(6):
        start_date = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        end_date = (start_date + timedelta(days=32)).replace(day=1)
        
        revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.created_at >= start_date,
            Order.created_at < end_date
        ).scalar() or 0
        
        monthly_revenue.append({
            'month': start_date.strftime('%Y-%m'),
            'revenue': float(revenue)
        })
    
    monthly_revenue.reverse()
    
    return render_template('admin/analytics.html',
                         top_products=top_products,
                         sales_by_province=sales_by_province,
                         monthly_revenue=monthly_revenue)
