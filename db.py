import uuid

games_db = {
    uuid.uuid4().hex : {
        "game_name": "Shadowrun (2007)",
        "published": True
    }
}

words_db = {
    uuid.uuid4().hex : {
        "word": "FPS",
        "definition": "Abbreviation standing for First-Person Shooter.",
        "example": "My favorite FPS is Shadowrun (2007).",
        "author_id": 1,
        "published": True
    }
}