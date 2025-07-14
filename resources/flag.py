from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from models import WordModel, GameModel, GamesWordsModel
from schemas import FlagSchema


blp = Blueprint('Flag', __name__, 'Blueprint for flag endpoint')

@blp.route('/flag')
class Flag(MethodView):
    # @jwt_required()
    @blp.arguments(FlagSchema)
    def post(self, request_payload: dict):
        # Link, word, game, other
        content_type = request_payload['content_type']
        content_id = request_payload['id']

        if content_type == 'word':
            content = WordModel.query.first_or_404(content_id)
        elif content_type == 'game':
            content = GameModel.query.first_or_404(content_id)

        reason = request_payload['reason']

        print(content.as_dict(), reason)
        return {}, 200

        # msg = Message('Hello', sender=os.getenv('SEND_EMAIL'), recipients=[os.getenv('FLAG_RECV_EMAIL')])
        # msg.body = 