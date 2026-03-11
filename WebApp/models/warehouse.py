from WebApp import db


class Warehouse(db.Model):
    __tablename__ = 'warehouse'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(500), nullable=True)
    capacity = db.Column(db.Integer, nullable=True)

    locations = db.relationship('StorageLocation', backref='warehouse', lazy=True, cascade='all, delete-orphan')
