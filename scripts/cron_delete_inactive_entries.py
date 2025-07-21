import argparse
import os
from dotenv import load_dotenv
from sqlalchemy import select, create_engine, delete
from sqlalchemy.orm import Session
import sys

parent_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
sys.path.append(parent_dir)

from models import WordModel, GameModel, GamesWordsModel


def delete_inactive_entries(db_url: str | None = None):
    load_dotenv('../.env')
    print('sqlite://' + parent_dir + '/instance/data.db')
    db_url = db_url or os.getenv('DATABASE_URL', 'sqlite:///' + parent_dir + '/instance/data.db')
    engine = create_engine(db_url, echo=False)
    with Session(engine) as session:
        inactive_words = session.execute(select(WordModel).where(WordModel.is_active == False))
        inactive_games = session.execute(select(GameModel).where(GameModel.is_active == False))
        inactive_word_ids = []
        inactive_game_ids = []
        for row in inactive_words.scalars():
            inactive_word_ids.append(row.word_id)
        for row in inactive_games.scalars():
            inactive_game_ids.append(row.game_id)

        inactive_games_delete = delete(GameModel).where(GameModel.is_active == False)
        inactive_games_words_delete_by_game_ids = delete(GamesWordsModel).where(GamesWordsModel.game_id.in_(inactive_game_ids))
        inactive_words_delete = delete(WordModel).where(WordModel.is_active == False)
        inactive_games_words_delete_by_word_ids = delete(GamesWordsModel).where(GamesWordsModel.word_id.in_(inactive_word_ids))
        session.execute(inactive_games_delete)
        session.execute(inactive_games_words_delete_by_game_ids)
        session.execute(inactive_words_delete)
        session.execute(inactive_games_words_delete_by_word_ids)
        session.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--db_url', required=False, default=None)
    args = parser.parse_args()

    db_url = args.db_url
    delete_inactive_entries(db_url)
