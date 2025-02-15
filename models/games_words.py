from db import db


class GamesWordsModel(db.Model):
    __tablename__ = "games_words"

    game_word_id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.game_id"), nullable=False)
    word_id = db.Column(db.Integer, db.ForeignKey("words.word_id"), nullable=False)

    # User = Store, Game = Item, Word = Tag

