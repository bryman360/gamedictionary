from flask import Flask, request
from flask_smorest import abort

app = Flask(__name__)

word_count = 1
words_db = {
    1 : {
        "word": "FPS",
        "definition": "Abbreviation standing for First-Person Shooter.",
        "example": "My favorite FPS is Shadowrun (2007).",
        "author_id": 1,
        "published": True
    }
}

game_count = 1
games_db = {
    1 : {
        "game_name": "Shadowrun (2007)",
        "published": True
    }
}


@app.get("/word/<int:word_id>")
def get_word(word_id: int):
    try:
        return {"word_id": word_id, **words_db[word_id]}
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
        abort(400, message="Bad request. Ensure 'word', 'definition', and 'example' are included in JSON payload.")

    global word_count
    word_count = word_count + 1
    new_word_post = {
        "word": request_data["word"],
        "definition": request_data["definition"],
        "example": request_data["example"],
        "author_id": 1,
        "published": False
    }

    words_db[word_count] = new_word_post
    return new_word_post, 201


@app.put("/word/<int:word_id>")
def update_word(word_id: int):
    request_data = request.get_json()
    if (
        "word" not in request_data or
        "definition" not in request_data or
        "example" not in request_data
    ):
        abort(400, message="Bad request. Ensure 'word', 'definition', and 'example' are included in JSON payload.")
    try:
        word = words_db[word_id]
        word_update = {
            "word": request_data["word"],
            "definition": request_data["definition"],
            "example": request_data["example"],
        }
        word |= word_update
    except KeyError:
        abort(404, message=f"No word with ID {word_id} found.")


@app.delete("/word/<int:word_id>")
def delete_word(word_id: int):
    try:
        del words_db[word_id]
        return {"message": f"Item with ID {word_id} deleted"}
    except KeyError:
        abort(404, message=f"Item with ID {word_id} not found.")


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


@app.put("/game/<int:game_id>")
def update_game(game_id:int):
    request_data = request.get_json()
    if (
        "game_name" not in request_data
    ):
        abort(400, message="Bad request. Ensure 'game_name' is included in JSON payload.")
    try:
        game = games_db[game_id]
        game_update = {
            "game_name": request_data["game_name"]
        }
        game |= game_update
    except KeyError:
        abort(404, message=f"No word with ID {game_id} found.")


@app.delete("/game/<int:game_id>")
def delete_word(game_id: int):
    try:
        del games_db[game_id]
        return {"message": f"Item with ID {game_id} deleted"}
    except KeyError:
        abort(404, message=f"Item with ID {game_id} not found.")
