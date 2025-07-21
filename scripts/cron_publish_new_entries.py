import argparse
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session
import sys

parent_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
sys.path.append(parent_dir)

from models import WordModel


def publish_words(db_url: str | None = None):
    load_dotenv('../.env')
    print('sqlite://' + parent_dir + '/instance/data.db')
    db_url = db_url or os.getenv('DATABASE_URL', 'sqlite:///' + parent_dir + '/instance/data.db')
    engine = create_engine(db_url, echo=False)
    with Session(engine) as session:
        word_update = update(WordModel).where(WordModel.published == False).values(published=True)
        session.execute(word_update)
        session.commit()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--db_url', required=False, default=None)
    args = parser.parse_args()

    db_url = args.db_url
    publish_words(db_url)
