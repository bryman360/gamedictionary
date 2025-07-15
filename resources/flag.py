import os

from flask import current_app, jsonify
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_mail import Message, Mail
from flask_smorest import Blueprint, abort

from models import WordModel, GameModel, UserModel
from schemas import FlagSchema


blp = Blueprint('Flag', __name__, 'Blueprint for flag endpoint')

@blp.route('/flag')
class Flag(MethodView):
    @jwt_required()
    @blp.arguments(FlagSchema)
    @blp.response(200)
    def post(self, request_payload: dict):
        content_type = request_payload['content_type']
        reason = request_payload['reason']
        user = UserModel.query.first_or_404(get_jwt_identity())
        non_content_specific_line = f'\n\nReason: "{reason}"\n\nby User: {{Username: {user.username}, User ID: {user.user_id}}}'

        if content_type == 'other':
            if 'description' not in request_payload:
                abort(405)
            description = request_payload['description']
            subject = f'Flag for Uncategorized Reason'

            body = f'Flagging for "Other" reason.\n\nDescription: {description}\n\n'
            body += non_content_specific_line
            
        else:
            if 'id' not in request_payload:
                abort(405)
            content_id = request_payload['id']

            if content_type == 'word':
                content = WordModel.query.first_or_404(content_id)
            elif content_type == 'game':
                content = GameModel.query.first_or_404(content_id)


            subject = 'Flag for ' + content_type.upper() + ' ' + str(content_id)
            pretty_content = '{\n'
            for key, value in content.as_dict().items():
                pretty_content += f'\t\'{key}\':'
                if type(value) == str:
                    pretty_content += f' \'{value}\',\n'
                else:
                    pretty_content += f' {value},\n'

            pretty_content += '}'

            body = f'Flagging for {content_type} with ID {content_id}.\n\n'
            body += pretty_content
            body += non_content_specific_line

        with current_app.app_context():
            msg = Message(subject, sender=os.getenv('SEND_EMAIL'), recipients=[os.getenv('FLAG_RECV_EMAIL')])
            msg.body = body
            mail = Mail()
            mail.send(msg)
        return jsonify({'message': 'Successfully flagged content.'})