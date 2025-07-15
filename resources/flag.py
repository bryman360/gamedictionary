import os

from flask import current_app
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_mail import Message, Mail
from flask_smorest import Blueprint

import json

from models import WordModel, GameModel, UserModel
from schemas import FlagSchema


blp = Blueprint('Flag', __name__, 'Blueprint for flag endpoint')

@blp.route('/flag')
class Flag(MethodView):
    # @jwt_required()
    @blp.arguments(FlagSchema)
    @blp.response(200)
    def post(self, request_payload: dict):
        # Link, word, game, other
        content_type = request_payload['content_type']
        content_id = request_payload['id']

        if content_type == 'word':
            content = WordModel.query.first_or_404(content_id)
        elif content_type == 'game':
            content = GameModel.query.first_or_404(content_id)

        user = UserModel.query.first_or_404(1)#get_jwt_identity())
        reason = request_payload['reason']

        subject = 'Flag for ' + content_type.upper() + ' ' + str(content_id)
        pretty_content = '{\n'
        for key, value in content.as_dict().items():
            pretty_content += f'\t\'{key}\':'
            if type(value) == str:
                pretty_content += f' \'{value}\',\n'
            else:
                pretty_content += f' {value},\n'

        pretty_content += '}'
        print(pretty_content)

        msg = Message(subject, sender=os.getenv('SEND_EMAIL'), recipients=[os.getenv('FLAG_RECV_EMAIL')])
        msg.body = f'Flagging for {content_type} with ID {content_id}.\n'
        msg.body += pretty_content

        msg.body += '\n\nReason: "' + reason + '"\nby User: { Username: ' + user.username + ', User ID: ' + str(user.user_id) + '}'

        with current_app.app_context():
            mail = Mail()
            mail.send(msg)
        return {}