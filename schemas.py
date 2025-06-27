from marshmallow import Schema, fields


# ------------------------------------------------------------
# 'Plain' Schemas (aka Schemas without relationships)
# ------------------------------------------------------------

class PlainWordSchema(Schema):
    word_id = fields.Int(dump_only=True)
    word = fields.Str(required=True)
    definition = fields.Str(required=True)
    example = fields.Str(required=True)
    published = fields.Bool(dump_only=True)
    submit_datetime = fields.DateTime(dump_only=True)
    is_active = fields.Int(dump_only=True)
    upvotes = fields.Int(dump_only=True)
    downvotes = fields.Int(dump_only=True)

class PlainGameSchema(Schema):
    game_id = fields.Int(dump_only=True)
    game_name = fields.Str(required=True)
    image_url = fields.Str()
    wiki_url = fields.Str()
    is_active = fields.Int(dump_only=True)

class PlainUserSchema(Schema):
    user_id = fields.Int(dump_only=True)
    email = fields.Str(required=True)
    username = fields.Str(required=True)
    is_active = fields.Int(dump_only=True)


# ------------------------------------------------------------
# Base Schemas (aka Plain Schemas now including relationships)
# ------------------------------------------------------------

class WordSchema(PlainWordSchema):
    author_id = fields.Int(dump_only=True)
    user = fields.Nested(PlainUserSchema(), dump_only=True)
    games = fields.Nested(PlainGameSchema(), dump_only=True, many=True)

class GameSchema(PlainGameSchema):
    words = fields.Nested(PlainWordSchema(), dump_only=True)

class UserSchema(PlainUserSchema):
    words = fields.List(fields.Nested(PlainWordSchema()), dump_only=True)

class GameAndWordSchema(Schema):
    message = fields.Str()
    game = fields.Nested(GameSchema)
    word = fields.Nested(WordSchema)


# ------------------------------------------------------------
# Update Schemas
# ------------------------------------------------------------

class WordUpdateSchema(Schema):
    word = fields.Str()
    definition = fields.Str()
    example = fields.Str()

class GameUpdateSchema(Schema):
    game_name = fields.Str()
    image_url = fields.Str()
    wiki_url = fields.Str()

class UserUpdateSchema(Schema):
    username = fields.Str()
    password = fields.Str()


# ------------------------------------------------------------
# Search Query Schema
# ------------------------------------------------------------

class SearchSchema(Schema):
    name = fields.Str()
    word = fields.Str()
    offset = fields.Int()
    limit = fields.Int()
    startsWith = fields.Str()
    author = fields.Str()


# ------------------------------------------------------------
# On the Fly Schemas (built after querying but before sending)
# ------------------------------------------------------------

class WordWithUsernameSchema(WordSchema):
    author_username = fields.Str()

class WordAndWordIdSchema(Schema):
    word_id = fields.Str(dump_only=True)
    word = fields.Str(dump_only=True)


# ------------------------------------------------------------
# Search Result Schemas
# ------------------------------------------------------------

class GameWordsSearchResultSchema(PlainGameSchema):
    words = fields.Nested(WordWithUsernameSchema, many=True)

class GamesSearchResultSchema(PlainGameSchema):
    words = fields.Nested(WordAndWordIdSchema, many=True)


# ------------------------------------------------------------
# Vote Action Schemas
# ------------------------------------------------------------

class VoteActionSchema(Schema):
    upvote_action = fields.Str(load_only=True)
    downvote_action = fields.Str(load_only=True)

class VoteReturnSchema(Schema):
    word_id = fields.Int(dump_only=True)
    upvotes = fields.Int(dump_only=True)
    downvotes = fields.Int(dump_only=True)


# ------------------------------------------------------------
# Login Schema
# ------------------------------------------------------------

class LoginSchema(Schema):
    source = fields.Str()
    token = fields.Str()