from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import db_config

cfg = db_config()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{cfg['user']}:{cfg['password']}"
    f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'raktar_secret_key_2026'
app.config['WTF_CSRF_ENABLED'] = True

db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

from WebApp.models.user import User
from WebApp.models.product import Product
from WebApp.models.order import Order
from WebApp.models.orderitem import OrderItem
from WebApp.models.shipment import Shipment
from WebApp.models.warehouse import Warehouse
from WebApp.models.storagelocation import StorageLocation
from WebApp.models.complaint import Complaint
