from flask_sqlalchemy import SQLAlchemy
from WebApp.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash


class UserManager:
    def __init__(self, db: SQLAlchemy):
        self.__db = db

    def create_user(self, name: str, email: str, password: str,
                    role: str = 'megrendelo', phone: str = None):
        existing = self.get_user_by_email(email)
        if existing:
            return None
        try:
            user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
                phone=phone
            )
            self.__db.session.add(user)
            self.__db.session.commit()
            return user
        except Exception as e:
            self.__db.session.rollback()
            raise e

    def get_user(self, user_id: int):
        return self.__db.session.query(User).get(user_id)

    def get_user_by_email(self, email: str):
        return self.__db.session.query(User).filter(User.email == email).first()

    def verify_password(self, email: str, password: str):
        user = self.get_user_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            return user
        return None

    def update_profile(self, user_id: int, name: str, email: str, phone: str):
        user = self.get_user(user_id)
        if not user:
            return None
        try:
            user.name = name
            user.email = email
            user.phone = phone
            self.__db.session.commit()
            return user
        except Exception as e:
            self.__db.session.rollback()
            raise e

    def list_users(self, page=1, per_page=15, role=None, name=None):
        query = self.__db.session.query(User)
        if role:
            query = query.filter(User.role == role)
        if name:
            query = query.filter(User.name.like(f'%{name}%'))
        return query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
