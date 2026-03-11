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
    updated_at = db.Column(db.DateTime, server_default=text("UTC_TIMESTAMP()"),
                           onupdate=text("UTC_TIMESTAMP()"), nullable=False)

    
    
    items = db.relationship('OrderItem', backref='order', lazy=True,
                             cascade='all, delete-orphan')
    shipments = db.relationship('Shipment', backref='order', lazy=True)
    complaints = db.relationship('Complaint', backref='order', lazy=True)
    supplier = db.relationship('User', foreign_keys=[supplier_id])
