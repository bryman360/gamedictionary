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
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    cover_url = fields.Str(dump_only=True)
    summary = fields.Str(dump_only=True)
    first_release_date = fields.DateTime(dump_only=True)
    slug=fields.Str(dump_only=True)

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
    game_id = fields.Nested(PlainGameSchema(), dump_only=True)

class GameSchema(PlainGameSchema):
    words = fields.Nested(PlainWordSchema(), dump_only=True)

class UserSchema(PlainUserSchema):
    words = fields.List(fields.Nested(PlainWordSchema()), dump_only=True)


# ------------------------------------------------------------
# Update Schemas
# ------------------------------------------------------------

class WordUpdateSchema(Schema):
    word = fields.Str()
    definition = fields.Str()
    example = fields.Str()
    game_id = fields.Str()

class UserUpdateSchema(Schema):
    username = fields.Str()


# ------------------------------------------------------------
# Search Query Schema
# ------------------------------------------------------------

class SearchSchema(Schema):
    offset = fields.Int()
    limit = fields.Int()

class WordSearchSchema(SearchSchema):
    word = fields.Str()
    startsWith = fields.Str()
    author = fields.Str()
    game_id = fields.Int()


class GameSearchSchema(SearchSchema):
    name = fields.Str()
    startsWith = fields.Str()


# ------------------------------------------------------------
# On the Fly Schemas (built after querying but before sending)
# ------------------------------------------------------------

class WordWithUsernameSchema(WordSchema):
    author_username = fields.Str()


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
    source = fields.Str(required=True)
    token = fields.Str(required=True)


# ------------------------------------------------------------
# Flag Schema
# ------------------------------------------------------------

class FlagSchema(Schema):
    content_type = fields.Str(required=True)
    id = fields.Int()
    description = fields.Str()
    reason = fields.Str(required=True)