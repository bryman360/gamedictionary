import uuid
from datetime import datetime


first_game_id = uuid.uuid4().hex
first_word_id = uuid.uuid4().hex
first_author_id = uuid.uuid4().hex


games_db = {
    first_game_id : {
        "game_id": first_game_id,
        "game_name": "Shadowrun (2007)",
        "published": True
    }
}

words_db = {
    first_word_id : {
        "word_id": first_word_id,
        "word": "FPS",
        "definition": "Abbreviation standing for First-Person Shooter.",
        "example": "My favorite FPS is Shadowrun (2007).",
        "author_id": first_author_id,
        "published": True,
        "submit_datetime": datetime.now()
    }
}



authors_db = {
    first_author_id : {
        "author_id": first_author_id,
        "username" : "BryanL",
        "join_date": datetime.now()
    }
}