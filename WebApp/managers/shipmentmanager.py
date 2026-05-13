from flask_sqlalchemy import SQLAlchemy
from WebApp.models.shipment import Shipment
from WebApp.models.order import Order
from datetime import datetime


class ShipmentManager:
    def __init__(self, db: SQLAlchemy):
        self.__db = db


    def create_shipment(self, order_id: int, expected_at=None, note: str = None):
        try:
            shipment = Shipment(
                order_id=order_id,
                expected_at=expected_at,
                note=note
            )
            self.__db.session.add(shipment)
            self.__db.session.commit()
            return shipment
        except Exception as e:
            self.__db.session.rollback()
            raise e


    def get_shipment(self, shipment_id: int):
        return self.__db.session.query(Shipment).get(shipment_id)


    def assign_carrier(self, shipment_id: int, carrier_id: int):
        shipment = self.get_shipment(shipment_id)
        if not shipment:
            return False
        try:
            shipment.carrier_id = carrier_id
            self.__db.session.commit()
            return True
        except Exception as e:
            self.__db.session.rollback()
            raise e


    def update_status(self, shipment_id: int, status: str):
        shipment = self.get_shipment(shipment_id)
        if not shipment:
            return False
        
       
        if shipment.status == 'Megérkezett':
            return 'locked'
        
        try:
            shipment.status = status
            if status == 'Megérkezett':
                shipment.delivered_at = datetime.utcnow()
            self.__db.session.commit()
            return True
        except Exception as e:
            self.__db.session.rollback()
            raise e


    def set_expected_at(self, shipment_id: int, expected_at):
        shipment = self.get_shipment(shipment_id)
        if not shipment:
            return False
        
        
        if shipment.expected_at is not None:
            return 'locked'
        
        try:
            shipment.expected_at = expected_at
            self.__db.session.commit()
            return True
        except Exception as e:
            self.__db.session.rollback()
            raise e


    def list_shipments(self, page=1, per_page=15,
                       carrier_id=None, status=None, order_id=None,
                       exclude_stock_orders=False):
        query = self.__db.session.query(Shipment)
        if carrier_id:
            query = query.filter(Shipment.carrier_id == carrier_id)
        if status:
            query = query.filter(Shipment.status == status)
        if order_id:
            query = query.filter(Shipment.order_id == order_id)
        if exclude_stock_orders:
            query = query.join(Order, Order.id == Shipment.order_id).filter(
                ~Order.note.like('[RAKTÁR RENDELÉS%')
            )
        return query.order_by(Shipment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)