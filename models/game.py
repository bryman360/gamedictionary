from db import db

class GameModel(db.Model):
    __tablename__ = 'games'

    game_id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String(50), unique=False, nullable=False)
    developer = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, unique=False, nullable=False)

    words = db.relationship('WordModel', back_populates='games', secondary='games_words')