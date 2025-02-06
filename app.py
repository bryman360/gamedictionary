from flask import Flask, request

app = Flask(__name__)

word_count = 1
words_db = {
    1 : {
        "word": "FPS",
        "definition": "Abbreviation standing for First-Person Shooter.",
        "example": "My favorite FPS is Shadowrun (2007).",
        "author_id": "1"
    }
}

game_count = 1
games_db = {
    1 : {
        "game_name": "Shadowrun (2007)",
    }
}


@app.get("/word/<int:word_id>")
def get_word(word_id:int):
    if word_id in words_db:
        return words_db[word_id]
    return {"message": "Word not found"}, 404


@app.post("/word")
def create_word():
    request_data = request.get_json()
    global word_count
    word_count = word_count + 1
    new_word_post = {
        "word": request_data["word"],
        "definition": request_data["definition"],
        "example": request_data["example"],
        "author_id": 1
    }

    words_db[word_count] = new_word_post
    return new_word_post, 201


@app.post("/game")
def create_word():
    request_data = request.get_json()
    global game_count
    game_count = game_count + 1
    new_word_post = {
        "game_name": request_data["game_name"]
    }

    games_db[game_count] = new_word_post
    return new_word_post, 201

@app.get("/game/<int:game_id>")
def get_game(game_id:int):
    if game_id in games_db:
        return games_db[game_id]
    return {"message": f"Game with id {game_id} not found"}, 404

    
