from marshmallow import Schema, fields


# ------------------------------------------------------------
# 'Plain' Schemas (aka Schemas without relationships)
# ------------------------------------------------------------

class PlainWordSchema(Schema):
    word_id = fields.Str(dump_only=True)
    word = fields.Str(required=True)
    definition = fields.Str(required=True)
    example = fields.Str(required=True)
    published = fields.Bool(dump_only=True)
    submit_datetime = fields.DateTime(dump_only=True)

class PlainGameSchema(Schema):
    game_id = fields.Str(dump_only=True)
    game_name = fields.Str(required=True)
    image_url = fields.Str()
    wiki_url = fields.Str()

class PlainUserSchema(Schema):
    user_id = fields.Int(dump_only=True)
    username = fields.Str(unique=True, required=True)


# ------------------------------------------------------------
# Base Schemas (aka Plain Schemas now including relationships)
# ------------------------------------------------------------

class WordSchema(PlainWordSchema):
    author_id = fields.Int(required=True, load_only=True)
    user = fields.Nested(PlainUserSchema(), dump_only=True)

class GameSchema(Schema):
    pass

class UserSchema(PlainUserSchema):
    words = fields.List(fields.Nested(PlainWordSchema()), dump_only=True)


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
