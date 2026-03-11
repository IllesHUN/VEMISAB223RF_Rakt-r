from WebApp import db
from sqlalchemy.sql import text


class StorageLocation(db.Model):
    __tablename__ = 'storage_location'

    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    code = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(db.DateTime, server_default=text("UTC_TIMESTAMP()"), nullable=False)