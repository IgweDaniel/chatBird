from datetime import datetime
from flask import request, jsonify, Blueprint
from sqlalchemy import exc
from app.models import db, User, TweetSchema, Tweet, Favorites
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
    db.session.commit()
    return jsonify({'data': 'success', 'error': None}), 201


@status.route('/retweet', methods=['POST'])
@protected
def share_a_status(current_user):
    data = request.get_json()
    s = Tweet.query.filter_by(id=data['id']).first()
    if not s:
        return jsonify({'data': 'Resource not found', 'error': None}), 404
    retweet = Tweet(text=data.get("text", None),
                    user=current_user, retweet_status=s)
    retweet.insert()
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


@status.route('/home_timeline', methods=['GET'])
@protected
def get_followed_statuses(current_user):
    s = current_user.get_followed_tweets()
    tweets_serializer.context = {"user": current_user}
    followed_tweets = tweets_serializer.dump(s)
    return jsonify({'data': {'tweets': followed_tweets}, 'error': None}), 200


@status.route('/like/<int:status_id>', methods=['POST'])
@protected
def favorite_status(current_user, status_id):
    s = Tweet.query.filter_by(id=status_id).first()
    if not s:
        return jsonify({'data': 'Resource not found', 'error': None}), 404
    current_user.like(s)
    db.session.commit()
    return jsonify({'data': "success", 'error': None}), 200


@status.route('/unlike/<int:status_id>', methods=['POST'])
@protected
def unfavorite_status(current_user, status_id):
    s = Tweet.query.filter_by(id=status_id).first()
    if not s:
        return jsonify({'data': 'Resource not found', 'error': None}), 404
    current_user.unlike(s)
    db.session.commit()
    return jsonify({'data': "success", 'error': None}), 200


@status.route('/favorites', methods=['GET'])
@protected
def get_favorite_statuses(current_user):
    f = Tweet.query.join(Favorites, Favorites.tweet_id == Tweet.id).filter(
        Favorites.user_id == current_user.id).all()
    tweets_serializer.context = {"user": current_user}
    favorite_tweets = tweets_serializer.dump(f)
    return jsonify({'data': {"statuses": favorite_tweets}, 'error': None}), 200


@status.route('/', methods=['GET'])
@protected
def get_a_statuses(current_user):
    u = Tweet.query.all()
    tweets_serializer.context = {"user": current_user}
    tweets = tweets_serializer.dump(u)
    return jsonify({'data': {"statuses": tweets}, 'error': None}), 200
