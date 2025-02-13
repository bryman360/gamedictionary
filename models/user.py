from db import db

class UserModel(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    # TODO: Store Hashed Password

    # words = db.relationship("WordModel", back_populates="user", lazy="dynamic")