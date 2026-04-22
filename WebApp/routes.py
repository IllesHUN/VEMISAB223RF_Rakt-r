from flask import render_template, request, redirect, url_for, session, flash, jsonify
from WebApp import app, db
from WebApp.decorators import (login_required, role_required,
                                admin_required, raktaros_required,
                                fuvarozo_required, beszallito_required)
from WebApp.managers.usermanager import UserManager
from WebApp.managers.ordermanager import OrderManager
from WebApp.managers.shipmentmanager import ShipmentManager
from WebApp.managers.warehousemanager import WarehouseManager
from WebApp.managers.complaintmanager import ComplaintManager
from WebApp.managers.productmanager import ProductManager
from WebApp.forms.loginform import LoginForm
from WebApp.forms.registerform import RegisterForm
from WebApp.forms.shipmentform import ShipmentForm, ShipmentStatusForm
from WebApp.forms.complaintform import ComplaintForm
from WebApp.models.product import Product

um = UserManager(db)
om = OrderManager(db)
sm = ShipmentManager(db)
wm = WarehouseManager(db)
cm = ComplaintManager(db)
pm = ProductManager(db)

# AUTH 

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = um.verify_password(form.email.data, form.password.data)
        if user:
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['role'] = user.role
            flash(f'Üdvözöljük, {user.name}!', 'success')
            return redirect(url_for('index'))
        flash('Hibás email vagy jelszó!', 'danger')
    return render_template('auth/login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = um.create_user(
            form.name.data, form.email.data,
            form.password.data, form.role.data,
            form.phone.data
        )
        if user:
            flash('Sikeres regisztráció! Kérjük, jelentkezz be.', 'success')
            return redirect(url_for('login'))
        flash('Ez az email már foglalt!', 'danger')
    return render_template('auth/register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Sikeres kijelentkezés!', 'success')
    return redirect(url_for('login'))


# FŐOLDAL

@app.route('/')
@login_required
def index():
    role = session.get('role')
    user_id = session.get('user_id')
    sort = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')

    stats = {}

    if role == 'megrendelo':
        orders = om.list_orders(buyer_id=user_id, page=1, per_page=5)
        stats['orders'] = orders.items
        stats['total_orders'] = orders.total

    elif role == 'beszallito':
        orders = om.list_orders(supplier_id=user_id, page=1, per_page=5)
        stats['orders'] = orders.items
        stats['total_orders'] = orders.total

    elif role == 'fuvarozo':
        shipments = sm.list_shipments(carrier_id=user_id, page=1, per_page=5)
        stats['shipments'] = shipments.items
        stats['total_shipments'] = shipments.total

    elif role in ('raktaros', 'admin'):
        orders = om.list_orders(page=1, per_page=5)
        shipments = sm.list_shipments(page=1, per_page=5)

        # Rendezés státusz szerint
        orders_list = list(orders.items)
        shipments_list = list(shipments.items)

        if sort == 'status':
            orders_list = sorted(orders_list, key=lambda x: x.status, reverse=(order == 'desc'))
            shipments_list = sorted(shipments_list, key=lambda x: x.status, reverse=(order == 'desc'))

        stats['orders'] = orders_list
        stats['shipments'] = shipments_list

    return render_template('index.html', stats=stats, role=role,
                           sort=sort, order=order)


# PROFIL 

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = um.get_user(session['user_id'])

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        updated = um.update_profile(session['user_id'], name, email, phone)
        if updated:
            session['user_name'] = updated.name
            flash('✅ Profil sikeresen frissítve!', 'success')
        else:
            flash('❌ Hiba történt!', 'danger')

    return render_template('profile.html', user=user)

# ============ MEGRENDELÉSEK ============

@app.route('/orders')
@login_required
def order_list():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '', type=str)
    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'megrendelo':
        pagination = om.list_orders(
            page=page, buyer_id=user_id,
            status=status if status else None)
    elif role == 'beszallito':
        pagination = om.list_orders(
            page=page, supplier_id=user_id,
            status=status if status else None)
    else:
        pagination = om.list_orders(
            page=page, status=status if status else None)

    return render_template('order/list.html', pagination=pagination)


@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = om.get_order(order_id)
    if not order:
        flash('Rendelés nem található!', 'danger')
        return redirect(url_for('order_list'))

    # ✅ Jogosultság ellenőrzés
    if session.get('role') == 'megrendelo':
        if order.buyer_id != session['user_id']:
            flash('⛔ Nincs jogosultságod ehhez a rendeléshez!', 'danger')
            return redirect(url_for('order_list'))
    elif session.get('role') == 'beszallito':
        if order.supplier_id != session['user_id']:
            flash('⛔ Nincs jogosultságod ehhez a rendeléshez!', 'danger')
            return redirect(url_for('order_list'))

    is_editable = om.is_editable(order)
    shipments = sm.list_shipments(order_id=order_id, page=1, per_page=100).items
    complaints = cm.list_complaints(order_id=order_id, page=1, per_page=100).items

    return render_template('order/detail.html',
                           order=order,
                           is_editable=is_editable,
                           shipments=shipments,
                           complaints=complaints)



@app.route('/order/new', methods=['GET', 'POST'])
@login_required
@role_required('megrendelo', 'admin')
def order_new():
    # Termékek listává alakítása (JavaScript tojson miatt)
    products_list = [
        {
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'price': p.price,
            'unit': p.unit
        }
        for p in pm.list_products(page=1, per_page=1000).items
    ]

    if request.method == 'POST':
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        note = request.form.get('note', '')

        items = []
        for pid, qty in zip(product_ids, quantities):
            if pid and qty:
                product = pm.get_product(int(pid))
                items.append({
                    'product_id': int(pid),
                    'quantity': int(qty),
                    'unit_price': product.price if product else 0.0
                })

        if not items:
            flash('Legalább egy terméket adj meg!', 'danger')
            return render_template('order/new_edit.html',
                                   products=products_list,
                                   order=None,
                                   is_editable=True)

        order = om.create_order(session['user_id'], items, note)
        if order:
            flash(f'✅ Megrendelés sikeresen leadva! (#{order.id})', 'success')
            return redirect(url_for('order_detail', order_id=order.id))
        flash('❌ Hiba történt a megrendelés rögzítésekor!', 'danger')

    return render_template('order/new_edit.html',
                           products=products_list,
                           order=None,
                           is_editable=True)



@app.route('/order/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('megrendelo', 'admin')
def order_edit(order_id):
    order = om.get_order(order_id)
    if not order:
        flash('Rendelés nem található!', 'danger')
        return redirect(url_for('order_list'))

    if not om.is_editable(order):
        flash('❌ A rendelés már nem szerkeszthető (24 óra eltelt)!', 'danger')
        return redirect(url_for('order_detail', order_id=order_id))

    # Termékek listává alakítása
    products_list = [
        {
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'price': p.price,
            'unit': p.unit
        }
        for p in pm.list_products(page=1, per_page=1000).items
    ]

    if request.method == 'POST':
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        note = request.form.get('note', '')

        items = []
        for pid, qty in zip(product_ids, quantities):
            if pid and qty:
                product = pm.get_product(int(pid))
                items.append({
                    'product_id': int(pid),
                    'quantity': int(qty),
                    'unit_price': product.price if product else 0.0
                })

        updated, message = om.update_order(order_id, items, note)
        if updated:
            flash(f'✅ {message}', 'success')
            return redirect(url_for('order_detail', order_id=order_id))
        flash(f'❌ {message}', 'danger')

    return render_template('order/new_edit.html',
                           products=products_list,
                           order=order,
                           is_editable=True)



@app.route('/order/<int:order_id>/status', methods=['POST'])
@login_required
@role_required('raktaros', 'admin')
def order_status_update(order_id):
    status = request.form.get('status')
    if om.update_status(order_id, status):
        flash(f'✅ Rendelés állapota frissítve: {status}', 'success')
    else:
        flash('❌ Hiba történt!', 'danger')
    return redirect(url_for('order_detail', order_id=order_id))








@app.route('/products')
@login_required                      
def product_list():
    products = pm.list_products(page=1, per_page=1000).items
    return render_template('products/list.html', products=products)

@app.route('/products/new', methods=['GET', 'POST'])
@login_required
@admin_required
def product_new():
    if request.method == 'POST':
        name        = request.form.get('name')
        sku         = request.form.get('sku')
        description = request.form.get('description', '')
        unit        = request.form.get('unit', 'db')
        price       = request.form.get('price', 0.0, type=float)

        try:
            product = pm.add_product(name, sku, description, unit, price)
            flash(f'✅ Termék sikeresen hozzáadva: {product.name}', 'success')
            return redirect(url_for('product_list'))
        except Exception as e:
            flash(f'❌ Hiba: {str(e)}', 'danger')

    return render_template('products/new_edit.html', product=None)


@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def product_edit(product_id):
    product = pm.get_product(product_id)
    if not product:
        flash('Termék nem található!', 'danger')
        return redirect(url_for('product_list'))

    if request.method == 'POST':
        name        = request.form.get('name')
        sku         = request.form.get('sku')
        description = request.form.get('description', '')
        unit        = request.form.get('unit', 'db')
        price       = request.form.get('price', 0.0, type=float)

        try:
            pm.update_product(product_id, name, sku, description, unit, price)
            flash('✅ Termék sikeresen frissítve!', 'success')
            return redirect(url_for('product_list'))
        except Exception as e:
            flash(f'❌ Hiba: {str(e)}', 'danger')

    return render_template('products/new_edit.html', product=product)

# ============ SZÁLLÍTMÁNYOK ============

@app.route('/shipments')
@login_required
def shipment_list():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '', type=str)
    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'fuvarozo':
        pagination = sm.list_shipments(
            page=page, carrier_id=user_id,
            status=status if status else None)
    else:
        pagination = sm.list_shipments(
            page=page, status=status if status else None)

    return render_template('shipment/list.html', pagination=pagination)


@app.route('/shipment/<int:shipment_id>')
@login_required
def shipment_detail(shipment_id):
    shipment = sm.get_shipment(shipment_id)
    if not shipment:
        flash('Szállítmány nem található!', 'danger')
        return redirect(url_for('shipment_list'))

    status_form = ShipmentStatusForm()

    # Fuvarozók listája (raktáros/admin számára)
    carriers = um.list_users(role='fuvarozo', page=1, per_page=100).items

    return render_template('shipment/detail.html',
                           shipment=shipment,
                           status_form=status_form,
                           carriers=carriers)



@app.route('/order/<int:order_id>/shipment/new', methods=['GET', 'POST'])
@login_required
@role_required('beszallito', 'admin')
def shipment_new(order_id):
    order = om.get_order(order_id)
    if not order:
        flash('Rendelés nem található!', 'danger')
        return redirect(url_for('order_list'))

    form = ShipmentForm()
    if form.validate_on_submit():
        shipment = sm.create_shipment(
            order_id=order_id,
            expected_at=form.expected_at.data,
            note=form.note.data
        )
        if shipment:
            om.update_status(order_id, 'szallitas_alatt')
            flash('✅ Szállítás rögzítve!', 'success')
            return redirect(url_for('order_detail', order_id=order_id))
        flash('❌ Hiba történt!', 'danger')

    return render_template('shipment/new.html', form=form, order=order)


@app.route('/shipment/<int:shipment_id>/status', methods=['POST'])
@login_required
@role_required('fuvarozo', 'admin')
def shipment_status_update(shipment_id):
    status = request.form.get('status')
    shipment = sm.get_shipment(shipment_id)

    if sm.update_status(shipment_id, status):
        if status == 'megerkezett':
            om.update_status(shipment.order_id, 'raktarba_erkezett')
        flash(f'✅ Szállítmány állapota frissítve: {status}', 'success')
    else:
        flash('❌ Hiba történt!', 'danger')

    return redirect(url_for('shipment_detail', shipment_id=shipment_id))


@app.route('/shipment/<int:shipment_id>/assign_carrier', methods=['POST'])
@login_required
@role_required('raktaros', 'admin')
def assign_carrier(shipment_id):
    carrier_id = request.form.get('carrier_id', type=int)
    if sm.assign_carrier(shipment_id, carrier_id):
        flash('✅ Fuvarozó hozzárendelve!', 'success')
    else:
        flash('❌ Hiba történt!', 'danger')
    return redirect(url_for('shipment_detail', shipment_id=shipment_id))


# ============ RAKTÁR ============

@app.route('/warehouses')
@login_required
@role_required('raktaros', 'admin')
def warehouse_list():
    page = request.args.get('page', 1, type=int)
    pagination = wm.list_warehouses(page=page)
    return render_template('warehouse/list.html', pagination=pagination)

@app.route('/warehouse/new', methods=['POST'])
@admin_required
def warehouse_new():
    name = request.form.get('name')
    address = request.form.get('address')
    capacity = request.form.get('capacity', type=int)

    wh = wm.create_warehouse(name, address, capacity)
    if wh:
        flash(f'✅ Raktár létrehozva: {wh.name}', 'success')
    else:
        flash('❌ Hiba történt!', 'danger')
    return redirect(url_for('warehouse_list'))

@app.route('/warehouse/<int:warehouse_id>')
@login_required
@raktaros_required
def warehouse_detail(warehouse_id):
    warehouse = wm.get_warehouse(warehouse_id)
    if not warehouse:
        flash('Raktár nem található!', 'danger')
        return redirect(url_for('warehouse_list'))

    page = request.args.get('page', 1, type=int)
    stock = wm.get_stock(warehouse_id, page=page)
    all_products = pm.list_products(page=1, per_page=1000).items

    return render_template('warehouse/detail.html',
                           warehouse=warehouse,
                           stock=stock,
                           all_products=all_products)

@app.route('/warehouse/<int:warehouse_id>/add_stock', methods=['POST'])
@login_required
@raktaros_required
def warehouse_add_stock(warehouse_id):
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int)
    location_code = request.form.get('location_code', '')

    location = wm.add_stock(warehouse_id, product_id, quantity, location_code)
    if location:
        flash(f'✅ Készlet frissítve! (+{quantity} db)', 'success')
    else:
        flash('❌ Hiba történt!', 'danger')

    return redirect(url_for('warehouse_detail', warehouse_id=warehouse_id))


@app.route('/warehouse/<int:warehouse_id>/remove_stock', methods=['POST'])
@login_required
@raktaros_required
def warehouse_remove_stock(warehouse_id):
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int)

    success, message = wm.remove_stock(warehouse_id, product_id, quantity)
    if success:
        flash(f'✅ {message}', 'success')
    else:
        flash(f'❌ {message}', 'danger')

    return redirect(url_for('warehouse_detail', warehouse_id=warehouse_id))


@app.route('/complaints')
@login_required
def complaint_list():
    page = request.args.get('page', 1, type=int)
    user_id = session.get('user_id')
    role = session.get('role')

    if role == 'megrendelo':
        pagination = cm.list_complaints(page=page, user_id=user_id)
    elif role in ['admin', 'raktaros']:
        pagination = cm.list_complaints(page=page)
    else:
        flash('⛔ Nincs jogosultságod!', 'danger')
        return redirect(url_for('index'))

    return render_template('complaint/list.html', pagination=pagination)

@app.route('/complaint/<int:complaint_id>/status', methods=['POST'])
@admin_required
def complaint_status_update(complaint_id):
    status = request.form.get('status')
    if cm.update_status(complaint_id, status):
        flash(f'✅ Reklamáció státusza frissítve!', 'success')
    else:
        flash('❌ Hiba történt!', 'danger')
    return redirect(url_for('complaint_list'))

@app.route('/order/<int:order_id>/complaint/new', methods=['GET', 'POST'])
@login_required
@role_required('megrendelo', 'admin')
def complaint_new(order_id):
    order = om.get_order(order_id)
    if not order:
        flash('Rendelés nem található!', 'danger')
        return redirect(url_for('order_list'))

    form = ComplaintForm()
    if form.validate_on_submit():
        complaint = cm.create_complaint(
            user_id=session['user_id'],
            order_id=order_id,
            complaint_type=form.type.data,
            description=form.description.data
        )
        if complaint:
            flash('✅ Reklamáció sikeresen beküldve!', 'success')
            return redirect(url_for('order_detail', order_id=order_id))
        flash('❌ Hiba történt!', 'danger')

    return render_template('complaint/new.html', form=form, order=order)



@app.route('/complaint/<int:complaint_id>', methods=['GET', 'POST'])
@login_required
def complaint_detail(complaint_id):
    complaint = cm.get_complaint(complaint_id)
    if not complaint:
        flash('Reklamáció nem található!', 'danger')
        return redirect(url_for('complaint_list'))

    # Megrendelő csak saját reklamációját láthatja
    if session.get('role') == 'megrendelo':
        if complaint.user_id != session['user_id']:
            flash('⛔ Nincs jogosultságod!', 'danger')
            return redirect(url_for('complaint_list'))

    if request.method == 'POST' and session.get('role') in ['admin', 'raktaros']:
        new_status = request.form.get('status')
        response_text = request.form.get('response', '')
        cm.update_status(complaint_id, status=new_status, response=response_text)
        flash('✅ Reklamáció frissítve!', 'success')
        return redirect(url_for('complaint_detail', complaint_id=complaint_id))

    return render_template('complaint/detail.html', complaint=complaint)


@app.route('/admin/stats')
@login_required
@role_required('admin')
def admin_stats():
    from sqlalchemy import func, extract
    from WebApp.models.orderitem import OrderItem
    from WebApp.models.order import Order
    from WebApp.models.user import User

    # Havi rendelésszám (idei év)
    monthly_orders = db.session.query(
        extract('month', Order.created_at).label('month'),
        func.count(Order.id).label('count')
    ).filter(
        extract('year', Order.created_at) == 2026
    ).group_by('month').order_by('month').all()

    # Havi bevétel
    monthly_revenue = db.session.query(
        extract('month', Order.created_at).label('month'),
        func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue')
    ).join(OrderItem, Order.id == OrderItem.order_id)\
     .filter(extract('year', Order.created_at) == 2026)\
     .group_by('month').order_by('month').all()

    # Top 5 megrendelő
    top_buyers = db.session.query(
        User.name,
        func.count(Order.id).label('count')
    ).join(Order, User.id == Order.buyer_id)\
     .group_by(User.id)\
     .order_by(func.count(Order.id).desc())\
     .limit(5).all()

    # Státusz megoszlás
    status_counts = db.session.query(
        Order.status,
        func.count(Order.id).label('count')
    ).group_by(Order.status).all()

    return render_template('admin/stats.html',
                           monthly_orders=monthly_orders,
                           monthly_revenue=monthly_revenue,
                           top_buyers=top_buyers,
                           status_counts=status_counts)

@app.route('/api/products', methods=['GET'])
@login_required
def api_products():
    products = pm.list_products(page=1, per_page=1000).items
    return jsonify({
        'success': True,
        'total': len(products),
        'products': [
            {
                'id': p.id,
                'name': p.name,
                'sku': p.sku,
                'description': p.description,
                'unit': p.unit,
                'price': p.price
            } for p in products
        ]
    }), 200


@app.route('/api/stock', methods=['GET'])
@login_required
def api_stock():
    from WebApp.models.storagelocation import StorageLocation

    stocks = db.session.query(StorageLocation).all()
    return jsonify({
        'success': True,
        'total': len(stocks),
        'stock': [
            {
                'warehouse_id': s.warehouse_id,
                'product_id': s.product_id,
                'product_name': s.product.name if s.product else None,
                'quantity': s.quantity,
                'location_code': s.code,
            } for s in stocks
        ]
    }), 200



@app.route('/api/shipments', methods=['GET'])
@login_required
def api_shipments():
    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'fuvarozo':
        shipments = sm.list_shipments(carrier_id=user_id, page=1, per_page=1000).items
    else:
        shipments = sm.list_shipments(page=1, per_page=1000).items

    return jsonify({
        'success': True,
        'total': len(shipments),
        'shipments': [
            {
                'id': s.id,
                'order_id': s.order_id,
                'status': s.status,
                'expected_at': s.expected_at.strftime('%Y-%m-%d') if s.expected_at else None,
                'carrier_id': s.carrier_id,
                'note': s.note
            } for s in shipments
        ]
    }), 200

@app.route('/api/orders', methods=['GET'])
@login_required
def api_orders():
    """API végpont - megrendelések JSON formátumban."""
    from WebApp.models.order import Order
    from sqlalchemy.orm import joinedload

    orders = db.session.query(Order).options(
        joinedload(Order.items),
        joinedload(Order.shipments)
    ).all()

    return jsonify({
        'success': True,
        'total': len(orders),
        'orders': [
            {
                'id': o.id,
                'buyer_id': o.buyer_id,
                'status': o.status,
                'created_at': o.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'items': [
                    {
                        'product_id': i.product_id,
                        'quantity': i.quantity,
                        'unit_price': i.unit_price
                    } for i in o.items
                ],
                'shipments_count': len(o.shipments)
            } for o in orders
        ]
    }), 200
