from db import db

class UserModel(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True)
    is_active = db.Column(db.Boolean, nullable=False)

    words = db.relationship('WordModel', back_populates='user', lazy='dynamic')
    roles = db.relationship('RoleModel', back_populates='user', lazy='dynamic')