from db import db


class WordModel(db.Model):
    __tablename__ = 'words'

    word_id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50), unique=False, nullable=False, index=True)
    definition = db.Column(db.Text(), unique=False, nullable=False)
    example = db.Column(db.Text(), unique=False, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=False, nullable=False)
    published = db.Column(db.Boolean, unique=False, nullable=False, default=False)
    submit_datetime = db.Column(db.DateTime, unique=False, nullable=False)
    is_active = db.Column(db.Boolean, unique=False, nullable=False, default=True)
    upvotes = db.Column(db.Integer, unique=False, nullable=False, default=0)
    downvotes = db.Column(db.Integer, unique=False, nullable=False, default=0)
    game_id = db.Column(db.Integer, db.ForeignKey('games.game_id'), unique=False, nullable=False)

    user = db.relationship('UserModel', back_populates='words')
    game = db.relationship('GameModel', back_populates='words')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
