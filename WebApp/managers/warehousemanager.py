from flask_sqlalchemy import SQLAlchemy
from WebApp.models.warehouse import Warehouse
from WebApp.models.storagelocation import StorageLocation
from sqlalchemy.sql import text


class WarehouseManager:
    def __init__(self, db: SQLAlchemy):
        self.__db = db

    def list_warehouses(self, page=1, per_page=10):
        return self.__db.session.query(Warehouse).paginate(
            page=page, per_page=per_page, error_out=False)

    def get_warehouse(self, warehouse_id: int):
        return self.__db.session.query(Warehouse).get(warehouse_id)

    def create_warehouse(self, name: str, address: str = None, capacity: int = None):
        try:
            wh = Warehouse(name=name, address=address, capacity=capacity)
            self.__db.session.add(wh)
            self.__db.session.commit()
            return wh
        except Exception as e:
            self.__db.session.rollback()
            raise e

    def add_stock(self, warehouse_id: int, product_id: int,
                  quantity: int, location_code: str):
        """Áru beérkezése / készlet növelése."""
        location = self.__db.session.query(StorageLocation).filter(
            StorageLocation.warehouse_id == warehouse_id,
            StorageLocation.product_id == product_id
        ).first()

        try:
            if location:
                location.quantity += quantity
                location.updated_at = text("UTC_TIMESTAMP()")
            else:
                location = StorageLocation(
                    warehouse_id=warehouse_id,
                    product_id=product_id,
                    code=location_code,
                    quantity=quantity
                )
                self.__db.session.add(location)
            self.__db.session.commit()
            return location
        except Exception as e:
            self.__db.session.rollback()
            raise e

    def remove_stock(self, warehouse_id: int, product_id: int, quantity: int):
        """Áru kiadása / készlet csökkentése."""
        location = self.__db.session.query(StorageLocation).filter(
            StorageLocation.warehouse_id == warehouse_id,
            StorageLocation.product_id == product_id
        ).first()

        if not location or location.quantity < quantity:
            return False, "Nincs elegendő készlet"

        try:
            location.quantity -= quantity
            self.__db.session.commit()
            return True, "Készlet sikeresen csökkentve"
        except Exception as e:
            self.__db.session.rollback()
            raise e

    def get_stock(self, warehouse_id: int, page=1, per_page=20):
        """Raktár készletének lekérdezése."""
        return self.__db.session.query(StorageLocation).filter(
            StorageLocation.warehouse_id == warehouse_id
        ).paginate(page=page, per_page=per_page, error_out=False)
