from WebApp import db


class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    unit = db.Column(db.String(50), nullable=False, default='db')
    price = db.Column(db.Float, nullable=False, default=0.0)
