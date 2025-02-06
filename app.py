from flask import Flask, request

app = Flask(__name__)

sequence_count = 1
words_db = [
    {
        "post_id": "1",
        "word": "FPS",
        "definition": "Abbreviation standing for First-Person Shooter.",
        "example": "My favorite FPS is Shadowrun (2007).",
        "author_id": "1"
    }
]

@app.get("/word/<string:word>")
def get_word(word: str):
    for post in words_db:
        if post["word"] == word:
            return {"word": post}
    return 404


@app.post("/word")
def create_word():
    request_data = request.get_json()
    global sequence_count
    sequence_count = sequence_count + 1
    new_word_post = {
        "post_id": str(sequence_count),
        "word": request_data["word"],
        "definition": request_data["definition"],
        "example": request_data["example"],
        "author_id": "1"
    }

    words_db.append(new_word_post)
    return new_word_post, 201

