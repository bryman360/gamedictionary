from marshmallow import Schema, fields

class WordSchema(Schema):
    word_id = fields.Str(dump_only=True)
    word = fields.Str(required=True)
    definition = fields.Str(required=True)
    example = fields.Str(required=True)
    author_id = fields.Str(required=True)
    published = fields.Bool(dump_only=True)
    submit_datetime = fields.DateTime(dump_only=True)


class WordUpdateSchema(Schema):
    word = fields.Str()
    definition = fields.Str()
    example = fields.Str()


class GameSchema(Schema):
    game_id = fields.Str(dump_only=True)
    game_name = fields.Str(required=True)


class GameUpdateSchema(Schema):
    game_name = fields.Str()