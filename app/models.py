from .extensions import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from datetime import datetime


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)  # Убедитесь, что этот атрибут определен

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Transaction(db.Model):
    __tablename__ = 'bank_transactions'
    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                           nullable=False)  # Убедитесь, что это правильный внешний ключ
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    type = db.Column(db.Enum('deposit', 'withdrawal'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
