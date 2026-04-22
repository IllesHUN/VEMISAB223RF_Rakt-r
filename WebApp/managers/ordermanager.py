from flask_sqlalchemy import SQLAlchemy
from WebApp.models.order import Order
from WebApp.models.orderitem import OrderItem
from datetime import datetime, timedelta


class OrderManager:
    def __init__(self, db: SQLAlchemy):
        self.__db = db

    def create_order(self, buyer_id: int, items: list, note: str = None):
        """
        items: [{'product_id': int, 'quantity': int, 'unit_price': float}]
        """
        try:
            order = Order(buyer_id=buyer_id, note=note)
            self.__db.session.add(order)
            self.__db.session.flush()

            for item in items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item.get('unit_price', 0.0)
                )
                self.__db.session.add(order_item)

            self.__db.session.commit()
            return order
        except Exception as e:
            self.__db.session.rollback()
            raise e

    def get_order(self, order_id: int):
        return self.__db.session.query(Order).get(order_id)

    def is_editable(self, order: Order) -> bool:
        """Csak 24 óráig szerkeszthető a megrendelés."""
        return datetime.utcnow() < order.created_at + timedelta(hours=24)

    def update_order(self, order_id: int, items: list, note: str = None):
        order = self.get_order(order_id)
        if not order:
            return None, "Rendelés nem található"
        if not self.is_editable(order):
            return None, "A rendelés már nem szerkeszthető (24 óra eltelt)"

        try:
            # Régi tételek törlése
            self.__db.session.query(OrderItem).filter(
                OrderItem.order_id == order_id).delete()

            # Új tételek felvitele
            for item in items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item.get('unit_price', 0.0)
                )
                self.__db.session.add(order_item)

            order.note = note
            self.__db.session.commit()
            return order, "Rendelés sikeresen módosítva"
        except Exception as e:
            self.__db.session.rollback()
            raise e

    def update_status(self, order_id: int, status: str):
        order = self.get_order(order_id)
        if not order:
            return False
        try:
            order.status = status
            self.__db.session.commit()
            return True
        except Exception as e:
            self.__db.session.rollback()
            raise e

    def list_orders(self, page=1, per_page=15, buyer_id=None,
                    supplier_id=None, status=None):
        query = self.__db.session.query(Order)
        if buyer_id:
            query = query.filter(Order.buyer_id == buyer_id)
        if supplier_id:
            query = query.filter(Order.supplier_id == supplier_id)
        if status:
            query = query.filter(Order.status == status)
        return query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)

    def assign_supplier(self, order_id: int, supplier_id: int):
        order = self.get_order(order_id)
        if not order:
            return False
        try:
            order.supplier_id = supplier_id
            self.__db.session.commit()
            return True
        except Exception as e:
            self.__db.session.rollback()
            raise e
