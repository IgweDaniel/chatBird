from datetime import datetime
from flask import request, jsonify, Blueprint
from sqlalchemy import exc
from app.models import db, User, TweetSchema, Tweet
from app.utils import generate_token, protected

status = Blueprint('status', __name__, url_prefix='/statuses')


tweet_serializer = TweetSchema()
tweets_serializer = TweetSchema(many=True)


@status.route('/', methods=['POST'])
@protected
def create_status(current_user):
    data = request.get_json()
    s = Tweet(text=data['text'], user=current_user)
    s.insert()
    return jsonify({'data': 'success', 'error': None}), 201


@status.route('/reply', methods=['POST'])
@protected
def reply_status(current_user):
    data = request.get_json()
    s = Tweet.query.filter_by(id=data['id']).first()
    if not s:
        return jsonify({'data': 'Resource not found', 'error': None}), 404
    reply = Tweet(text=data['text'], user=current_user, in_reply_to_status=s)
    reply.insert()
    s.reply_count += 1
    db.session.commit()
    return jsonify({'data': 'success', 'error': None}), 201


@status.route('/<int:status_id>', methods=['GET'])
def get_a_status(status_id):
    s = Tweet.query.filter_by(id=status_id).first()
    if not s:
        return jsonify({'data': 'Resource not found', 'error': None}), 404
    status = tweet_serializer.dump(s)
    return jsonify({'data': {'status': status}, 'error': None}), 200


@status.route('/<int:status_id>/replies', methods=['GET'])
def get_replies_for_status(status_id):
    data = request.get_json()
    s = Tweet.query.filter_by(id=status_id).first()
    if not s:
        return jsonify({'data': 'Resource not found', 'error': None}), 404
    r = Tweet.query.filter_by(in_reply_to_status=s).all()
    replies = tweets_serializer.dump(r)
    return jsonify({'data': {'replies': replies}, 'error': None}), 200
