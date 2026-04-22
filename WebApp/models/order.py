from WebApp import db
from sqlalchemy.sql import text

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status = db.Column(db.String(50), default='feldolgozas_alatt', nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=text("UTC_TIMESTAMP()"), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=text("UTC_TIMESTAMP()"), onupdate=text("UTC_TIMESTAMP()"), nullable=False)

    
    buyer = db.relationship('User', foreign_keys=[buyer_id], back_populates='buyer_orders')
    supplier = db.relationship('User', foreign_keys=[supplier_id], back_populates='supplier_orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    shipments = db.relationship('Shipment', back_populates='order')
    complaints = db.relationship('Complaint', back_populates='order')