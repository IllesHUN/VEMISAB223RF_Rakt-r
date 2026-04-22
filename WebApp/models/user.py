from WebApp import db
from sqlalchemy.sql import text

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='megrendelo', nullable=False)
    created_at = db.Column(db.DateTime, server_default=text("UTC_TIMESTAMP()"), nullable=False)

    
    buyer_orders = db.relationship('Order', foreign_keys='Order.buyer_id', back_populates='buyer')
    supplier_orders = db.relationship('Order', foreign_keys='Order.supplier_id', back_populates='supplier')
    carrier_shipments = db.relationship('Shipment', foreign_keys='Shipment.carrier_id', back_populates='carrier')
    complaints = db.relationship('Complaint', back_populates='user')