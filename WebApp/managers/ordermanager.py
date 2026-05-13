from flask_sqlalchemy import SQLAlchemy
from WebApp.models.order import Order
from WebApp.models.orderitem import OrderItem
from WebApp.models.storagelocation import StorageLocation
from datetime import datetime, timedelta
from sqlalchemy import func


class OrderManager:
    def __init__(self, db: SQLAlchemy):
        self.__db = db

    def _check_stock(self, items: list, exclude_order_id: int = None):
        for item in items:
            total_stock = self.__db.session.query(
                func.sum(StorageLocation.quantity)
            ).filter(
                StorageLocation.product_id == item['product_id']
            ).scalar() or 0

            reserved_query = self.__db.session.query(
                func.sum(OrderItem.quantity)
            ).join(Order, Order.id == OrderItem.order_id).filter(
                OrderItem.product_id == item['product_id'],
                Order.status.in_(['lezárva', 'szállítás alatt', 'feldolgozás alatt'])
            )

            if exclude_order_id:
                reserved_query = reserved_query.filter(Order.id != exclude_order_id)

            reserved = reserved_query.scalar() or 0
            available = total_stock - reserved

            if available < item['quantity']:
                from WebApp.models.product import Product
                product = self.__db.session.query(Product).get(item['product_id'])
                name = product.name if product else f"#{item['product_id']}"
                return False, f"Nincs elég készlet: {name} — kért: {item['quantity']} db, elérhető: {available} db"

        return True, None
    def _deduct_stock(self, order: Order):
        """Lezárt rendelés tételeit levonja a raktárkészletből."""
        for item in order.items:
            # Megkeressük azokat a raktárhelyeket ahol van ebből a termékből
            locations = self.__db.session.query(StorageLocation).filter(
                StorageLocation.product_id == item.product_id,
                StorageLocation.quantity > 0
            ).order_by(StorageLocation.quantity.desc()).all()

            remaining = item.quantity

            for location in locations:
                if remaining <= 0:
                    break

                if location.quantity >= remaining:
                    location.quantity -= remaining
                    remaining = 0
                else:
                    remaining -= location.quantity
                    location.quantity = 0

            # Ha nem volt elég készlet (elvileg nem fordulhat elő, de biztonság kedvéért)
            if remaining > 0:
                from WebApp.models.product import Product
                product = self.__db.session.query(Product).get(item.product_id)
                name = product.name if product else f"#{item.product_id}"
                raise ValueError(f"Nincs elég készlet a levonáshoz: {name}")
        

    def create_order(self, buyer_id: int, items: list, note: str = None):
        try:
            ok, error = self._check_stock(items)
            if not ok:
                raise ValueError(error)

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

    def update_order(self, order_id: int, items: list, note: str = None):
        order = self.get_order(order_id)
        if not order:
            return None, "Rendelés nem található"
        if not self.is_editable(order):
            return None, "A rendelés már nem szerkeszthető (24 óra eltelt)"

        ok, error = self._check_stock(items, exclude_order_id=order_id)
        if not ok:
            return None, error

        try:
            self.__db.session.query(OrderItem).filter(
                OrderItem.order_id == order_id).delete()

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

    def get_order(self, order_id: int):
        return self.__db.session.query(Order).get(order_id)

    def is_editable(self, order: Order) -> bool:
        return datetime.utcnow() < order.created_at + timedelta(hours=24)

    def update_status(self, order_id: int, status: str):
        order = self.get_order(order_id)
        if not order:
            return False
        try:
            order.status = status
            
            # Ha lezárva státuszra vált, levonjuk a készletből
            if status == 'lezarva':
                self._deduct_stock(order)
            
            self.__db.session.commit()
            return True
        except Exception as e:
            self.__db.session.rollback()
            raise e

    def list_orders(self, page=1, per_page=15, buyer_id=None,
                    supplier_id=None, status=None,
                    only_stock_orders=False, exclude_stock_orders=False):
        query = self.__db.session.query(Order)
        if buyer_id:
            query = query.filter(Order.buyer_id == buyer_id)
        if supplier_id:
            query = query.filter(Order.supplier_id == supplier_id)
        if status:
            query = query.filter(Order.status == status)
        if only_stock_orders:
            query = query.filter(Order.note.like('[RAKTÁR RENDELÉS%'))
        if exclude_stock_orders:
            query = query.filter(
                ~Order.note.like('[RAKTÁR RENDELÉS%') | Order.note.is_(None)
            )
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