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
