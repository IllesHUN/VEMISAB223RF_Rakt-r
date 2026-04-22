from flask_sqlalchemy import SQLAlchemy
from WebApp.models.complaint import Complaint
from datetime import datetime


class ComplaintManager:
    def __init__(self, db: SQLAlchemy):
        self.__db = db

    def create_complaint(self, user_id: int, order_id: int,
                         complaint_type: str, description: str):
        try:
            complaint = Complaint(
                user_id=user_id,
                order_id=order_id,
                type=complaint_type,
                description=description
            )
            self.__db.session.add(complaint)
            self.__db.session.commit()
            return complaint
        except Exception as e:
            self.__db.session.rollback()
            raise e

    def get_complaint(self, complaint_id: int):
        return self.__db.session.query(Complaint).get(complaint_id)

    def update_status(self, complaint_id: int, status: str, response: str = None):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            return False
        try:
            complaint.status = status
            if response:
                complaint.response = response
                complaint.response_at = datetime.now()
            self.__db.session.commit()
            return True
        except Exception as e:
            self.__db.session.rollback()
            raise e

    def list_complaints(self, page=1, per_page=15,
                        user_id=None, order_id=None, status=None):
        query = self.__db.session.query(Complaint)
        if user_id:
            query = query.filter(Complaint.user_id == user_id)
        if order_id:
            query = query.filter(Complaint.order_id == order_id)
        if status:
            query = query.filter(Complaint.status == status)
        return query.order_by(Complaint.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
