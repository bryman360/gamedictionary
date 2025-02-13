from db import db


class WordModel(db.Model):
    __tablename__ = "words"

    word_id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50), unique=False, nullable=False)
    definition = db.Column(db.Text(), unique=False, nullable=False)
    example = db.Column(db.Text(), unique=False, nullable=False)
    author_id = db.Column(db.Integer, nullable=False)#, db.ForeignKey("users.user_id"), unique=False, nullable=False)
    published = db.Column(db.Boolean, unique=False, nullable=False)
    submit_datetime = db.Column(db.DateTime, unique=False, nullable=False)

    # user = db.relationship("UserModel", back_populates="words")
