import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from app import app
from WebApp import db
from WebApp.models.user import User
from WebApp.models.product import Product
from WebApp.models.order import Order
from WebApp.managers.warehousemanager import WarehouseManager
from WebApp.managers.productmanager import ProductManager
from WebApp.managers.ordermanager import OrderManager
from WebApp.managers.shipmentmanager import ShipmentManager
from WebApp.managers.usermanager import UserManager

wm = WarehouseManager(db)
pm = ProductManager(db)
om = OrderManager(db)
sm = ShipmentManager(db)
um = UserManager(db)

with app.app_context():

    # ===== 0. ADMIN =====
    print("Admin letrehozasa...")
    if not User.query.filter_by(email='admin@admin.hu').first():
        admin = User(
            name='Admin',
            email='admin@admin.hu',
            role='admin',
            phone='',
            password_hash=generate_password_hash('admin1234')
        )
        db.session.add(admin)
        db.session.commit()
        print("  Admin user letrehozva!")
        print("  Email: admin@admin.hu")
        print("  Jelszo: admin1234")
    else:
        print("  Admin user mar letezik!")

    # ===== 1. RAKTARAK =====
    print("Raktarak letrehozasa...")
    warehouses_data = [
        ("Kozponti Raktar", "Budapest, Raktar utca 1.", 5000),
        ("Eszaki Raktar", "Miskolc, Ipari Park 12.", 3000),
        ("Deli Raktar", "Pecs, Logisztikai Centrum 5.", 2500),
        ("Nyugati Raktar", "Gyor, Kulso-Vamhazi ut 8.", 4000),
    ]
    warehouses = []
    for name, address, capacity in warehouses_data:
        try:
            wh = wm.create_warehouse(name, address, capacity)
            if wh:
                warehouses.append(wh)
                print(f"  {wh.name}")
        except:
            print(f"  Mar letezik: {name}")

    # ===== 2. TERMEKEK =====
    print("Termekek letrehozasa...")
    products_data = [
        ("Laptop Lenovo ThinkPad", "LAP-001", "14 colos uzleti laptop", "db", 450000),
        ("Monitor 24", "MON-001", "Full HD IPS monitor", "db", 89000),
        ("Billentyuzet Mechanikus", "KEY-001", "Magyar mechanikus billentyuzet", "db", 25000),
        ("Eger Logitech MX", "MOU-001", "Vezetek nelkuli ergonomikus eger", "db", 18000),
        ("USB Hub 7 port", "USB-001", "USB 3.0 eloszto", "db", 12000),
        ("A4 Papir 500 lap", "PAP-001", "Irodai nyomtatopapir", "csomag", 1500),
        ("Toner HP LaserJet", "TON-001", "HP LaserJet fekete toner", "db", 22000),
        ("Ethernet kabel 5m", "CAB-001", "Cat6 UTP patch kabel", "db", 3500),
        ("Irodai szek ergonomikus", "CHR-001", "Allithato magassagu irodai szek", "db", 75000),
        ("Irodasztal allithato", "DSK-001", "Elektromosan allithato asztal", "db", 120000),
        ("Nyomtato HP LaserJet", "PRN-001", "Vezetek nelkuli lezernyomtato", "db", 95000),
        ("Headset USB", "HDS-001", "Zajszuros USB headset", "db", 35000),
        ("Webkamera Full HD", "CAM-001", "1080p webkamera mikrofonnal", "db", 28000),
        ("SSD 1TB Samsung", "SSD-001", "SATA SSD meghajto", "db", 42000),
        ("RAM 16GB DDR4", "RAM-001", "DDR4 3200MHz memoria modul", "db", 22000),
    ]
    for name, sku, desc, unit, price in products_data:
        try:
            p = pm.add_product(name, sku, desc, unit, price)
            if p:
                print(f"  {p.name}")
        except:
            print(f"  Mar letezik: {name}")

    # ===== 3. KESZLET =====
    print("Keszlet feltoltese...")
    from WebApp.models.warehouse import Warehouse
    all_warehouses = db.session.execute(db.select(Warehouse)).scalars().all()
    all_products = db.session.execute(db.select(Product)).scalars().all()

    location_letters = ['A', 'B', 'C', 'D']
    stock_count = 0
    for warehouse in all_warehouses:
        selected = random.sample(all_products, min(8, len(all_products)))
        for i, product in enumerate(selected):
            code = f"{random.choice(location_letters)}-0{i+1}-00{i+1}"
            quantity = random.randint(5, 100)
            try:
                loc = wm.add_stock(warehouse.id, product.id, quantity, code)
                if loc:
                    stock_count += 1
            except:
                pass
    print(f"  {stock_count} keszlet bejegyzes letrehozva!")

    # ===== 4. FELHASZNALOK =====
    print("Felhasznalok letrehozasa...")
    users_data = [
        ("Megrendelo Anna", "anna@example.com", "jelszo123", "megrendelo"),
        ("Megrendelo Bela", "bela@example.com", "jelszo123", "megrendelo"),
        ("Megrendelo Csilla", "csilla@example.com", "jelszo123", "megrendelo"),
        ("Beszallito Kft", "beszallito@example.com", "jelszo123", "beszallito"),
        ("Gyors Fuvar Bt", "fuvar@example.com", "jelszo123", "fuvarozo"),
        ("Raktaros Denes", "denes@example.com", "jelszo123", "raktaros"),
    ]
    for name, email, password, role in users_data:
        try:
            u = um.create_user(name, email, password, role=role)
            if u:
                print(f"  {u.name} ({u.role})")
        except:
            print(f"  Mar letezik: {email}")

    # ===== 5. RENDELESEK =====
    print("Rendelesek letrehozasa...")
    megrendelok = db.session.execute(
        db.select(User).where(User.role == 'megrendelo')).scalars().all()
    beszallitok = db.session.execute(
        db.select(User).where(User.role == 'beszallito')).scalars().all()
    fuvarozok = db.session.execute(
        db.select(User).where(User.role == 'fuvarozo')).scalars().all()

    statuses = ['feldolgozas_alatt', 'szallitas_alatt', 'raktarba_erkezett', 'lezarva']
    notes = ["Surgos szallitas!", "Gondosan csomagoljak!", "Reggeli szallitast kerunk.", None]

    order_count = 0
    for megrendelo in megrendelok:
        for _ in range(random.randint(2, 4)):
            selected = random.sample(list(all_products), random.randint(1, 4))
            items = [{'product_id': p.id, 'quantity': random.randint(1, 10), 'unit_price': p.price} for p in selected]
            order = om.create_order(megrendelo.id, items, random.choice(notes))
            if order:
                status = random.choice(statuses)
                om.update_status(order.id, status)
                if beszallitok and random.random() > 0.3:
                    om.assign_supplier(order.id, random.choice(beszallitok).id)
                order_count += 1
                print(f"  Rendeles #{order.id} - {megrendelo.name} - {status}")

    print(f"  {order_count} rendeles letrehozva!")

    # ===== 6. SZALLITMANNYOK =====
    print("Szallitmannyok letrehozasa...")
    szallitas_orders = db.session.execute(
        db.select(Order).where(Order.status.in_(['szallitas_alatt', 'raktarba_erkezett', 'lezarva']))
    ).scalars().all()

    shipment_count = 0
    for order in szallitas_orders:
        expected = datetime.utcnow() + timedelta(days=random.randint(1, 7))
        shipment = sm.create_shipment(order_id=order.id, expected_at=expected, note="Tesztszallitmany")
        if shipment:
            if fuvarozok:
                sm.assign_carrier(shipment.id, random.choice(fuvarozok).id)
            sm.update_status(shipment.id, random.choice(['elokeszitve', 'uton', 'megerkezett']))
            shipment_count += 1
            print(f"  Szallitmany #{shipment.id} - Rendeles #{order.id}")

    print(f"  {shipment_count} szallitmany letrehozva!")
    print("Minden seed adat sikeresen letrehozva!")
    print("")
    print("=== ADMIN BEJELENTKEZESI ADATOK ===")
    print("Email: admin@admin.hu")
    print("Jelszo: admin1234")