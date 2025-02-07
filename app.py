from flask import Flask, request
from flask_smorest import abort

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
def get_word(word_id: int):
    try:
        return words_db[word_id]
    except KeyError:
        abort(404, message=f"Word with ID {word_id} not found.")


@app.post("/word")
def create_word():
    request_data = request.get_json()
    if (
        "word" not in request_data or
        "definition" not in request_data or
        "example" not in request_data
    ):
        abort(400, message="Bad request. Ensure 'word', 'definition', and 'example' are in the payload.")

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



@app.get("/game/<int:game_id>")
def get_game(game_id: int):
    try:
        return games_db[game_id]
    except KeyError:
        abort(404, message=f"Game with ID {game_id} not found.")


@app.post("/game")
def create_game():
    request_data = request.get_json()
    if (
        "game_name" not in request_data
    ):
        abort(400, message="Bad request. Ensure 'game_name' is in the payload.")

    global game_count
    game_count = game_count + 1
    new_word_post = {
        "game_name": request_data["game_name"]
    }

    games_db[game_count] = new_word_post
    return new_word_post, 201

