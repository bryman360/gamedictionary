from db import db

class UserModel(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(), unique=False, nullable=False)
    is_active = db.Column(db.Boolean, unique=False, nullable=False)

    words = db.relationship('WordModel', back_populates='user', lazy='dynamic')