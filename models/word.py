from db import db


class WordModel(db.Model):
    __tablename__ = 'words'

    word_id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50), unique=False, nullable=False)
    definition = db.Column(db.Text(), unique=False, nullable=False)
    example = db.Column(db.Text(), unique=False, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=False, nullable=False)
    published = db.Column(db.Boolean, unique=False, nullable=False)
    submit_datetime = db.Column(db.DateTime, unique=False, nullable=False)
    is_active = db.Column(db.Boolean, unique=False, nullable=False)
    upvotes = db.Column(db.Integer, nullable=False)
    downvotes = db.Column(db.Integer, nullable=False)

    user = db.relationship('UserModel', back_populates='words')
    games = db.relationship('GameModel', back_populates='words', secondary='games_words')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
