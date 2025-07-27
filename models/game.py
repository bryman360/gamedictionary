from db import db

class GameModel(db.Model):
    __tablename__ = 'games'

    game_id = db.Column(db.Integer, primary_key=True)

    words = db.relationship('WordModel', back_populates='game', lazy='dynamic')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
