from db import db

class GameModel(db.Model):
    __tablename__ = 'games'

    game_id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String(50), unique=False, nullable=False)
    image_url = db.Column(db.Text(), unique=False, nullable=True)
    wiki_url = db.Column(db.Text(), unique=False, nullable=True)
    is_active = db.Column(db.Boolean, unique=False, nullable=False)

    words = db.relationship('WordModel', back_populates='games', secondary='games_words')