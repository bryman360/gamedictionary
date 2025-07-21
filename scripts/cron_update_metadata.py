import argparse
import os
from dotenv import load_dotenv
from sqlalchemy import select, create_engine, func
from sqlalchemy.orm import Session
import json
import sys

parent_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
sys.path.append(parent_dir)

from models import WordModel, GameModel


def update_metadata(db_url: str | None = None):
    load_dotenv('../.env')
    print('sqlite://' + parent_dir + '/instance/data.db')
    db_url = db_url or os.getenv('DATABASE_URL', 'sqlite:///' + parent_dir + '/instance/data.db')
    engine = create_engine(db_url, echo=False)
    with Session(engine) as session:
        query = select(func.count(WordModel.word_id))
        word_count = session.scalar(query)
        query = select(func.count(GameModel.game_id))
        game_count = session.scalar(query)
        print('Count of words in words table is', word_count)
        print('Count of games in games table is', game_count)

        with open(os.path.join(parent_dir, 'metadata.json'), mode='w') as metadata:
            metadata_json = {}
            metadata_json['word_count'] = word_count
            metadata_json['game_count'] = game_count
            json.dump(metadata_json, metadata)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--db_url', required=False, default=None)
    args = parser.parse_args()

    db_url = args.db_url
    update_metadata(db_url)
