from db import db

class GamesWordsLinkUserModel(db.Model):
    __tablename__ = 'games_words_link_authors'

    game_word_id = db.Column(db.Integer, db.ForeignKey('games_words.game_word_id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)