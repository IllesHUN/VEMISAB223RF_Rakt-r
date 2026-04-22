from flask_sqlalchemy import SQLAlchemy
from WebApp.models.product import Product


class ProductManager:
    def __init__(self, db: SQLAlchemy):
        self.__db = db

    def list_products(self, page=1, per_page=15, name=None):
        query = self.__db.session.query(Product)
        if name:
            query = query.filter(Product.name.like(f'%{name}%'))
        return query.order_by(Product.name).paginate(
            page=page, per_page=per_page, error_out=False)

    def get_product(self, product_id: int):
        return self.__db.session.query(Product).get(product_id)

    def add_product(self, name: str, sku: str, description: str = None,
                    unit: str = 'db', price: float = 0.0):
        try:
            product = Product(name=name, sku=sku, description=description,
                              unit=unit, price=price)
            self.__db.session.add(product)
            self.__db.session.commit()
            return product
        except Exception as e:
            self.__db.session.rollback()
            raise e

    def update_product(self, product_id: int, name: str, sku: str,
                       description: str = None, unit: str = 'db',
                       price: float = 0.0):
        product = self.get_product(product_id)
        if not product:
            return None
        try:
            product.name = name
            product.sku = sku
            product.description = description
            product.unit = unit
            product.price = price
            self.__db.session.commit()
            return product
        except Exception as e:
            self.__db.session.rollback()
            raise e
