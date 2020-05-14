from flask import request, jsonify, Blueprint
from datetime import datetime
from app.models import db, User, Tweet, TweetSchema, UserSchema, Token
from app.utils import generate_token, protected, send_mail, generate_code
from sqlalchemy import exc
from werkzeug.security import generate_password_hash, check_password_hash

user = Blueprint('user', __name__, url_prefix='/user')

user_serializer = UserSchema()
users_serializer = UserSchema(many=True)
tweet_serializer = TweetSchema()
tweets_serializer = TweetSchema(many=True)


@user.route('/create', methods=['POST'])
def create_user():
    data = request.get_json()
    code = generate_code()
    try:
        user = User(
            username=data['username'], email=data['email'], code=code, password_hash=generate_password_hash(data['password']))
        db.session.add(user)
        db.session.commit()
        token = Token(user_id=user.id, code=code)
        db.session.add(token)
        db.session.commit()
    except exc.IntegrityError:
        return jsonify({'error': {'message': 'user already exists', 'code': 400}, 'data': None})

    send_mail('Email Verification', user.email,
              'mail.html', code=code, username=user.username)

    return jsonify({'error': None, 'data': "success"})


@user.route('/auth', methods=['POST'])
def authenticate_user():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'error': {'message': 'Invalid Credentials', 'code': 400}, 'data': None})
    if not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': {'message': 'Invalid Credentials', 'code': 400}, 'data': None})
    if not user.verified:
        return jsonify({'error': {'message': 'please verify account', 'code': 400}, 'data': None})
    token = generate_token({'id': user.id, 'username': user.username})
    return jsonify({'error': None, 'data': {'token': token.decode("utf-8")}})


@user.route('/verify', methods=['POST'])
def verify_user():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'error': {'message': 'Invalid Credentials', 'code': 400}, 'data': None})

    if user.verified:
        return jsonify({'error': {'message': 'Verified', 'code': 400}, 'data': None})

    code = Token.query.filter_by(user_id=user.id).first()
    print(code.issuedAt, datetime.utcnow())
    if code.code != data['code'] and code.issuedAt < datetime.utcnow():
        return jsonify({'error': {'message': 'Verification Failed', 'code': 400}, 'data': None})
    db.session.delete(code)
    db.session.commit()
    token = generate_token(
        {'id': user.id, 'username': user.username})
    return jsonify({'error': None, 'data': {'token': token.decode("utf-8")}})


@user.route('/send_token', methods=['POST'])
def send_verification_code():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'error': {'message': 'Invalid Credentials', 'code': 400}, 'data': None})
    if user.verified:
        return jsonify({'error': {'message': 'Verified', 'code': 400}, 'data': None})
    code = generate_code()
    token = Token(user_id=user.id, code=code)
    db.session.add(token)
    db.session.commit()
    send_mail('Email Verification', user.email,
              'mail.html', code=code, username=user.username)

    return jsonify({'error': None, 'data': "success"})


@user.route('/')
@user.route('/index')
def index():
    u = User.query.all()
    users = users_serializer.dump(u)
    print(users)
    return jsonify({'data': users})


@user.route('/test')
def follow():
    u = User.query.all()[0]
    user = user_serializer.dump(u)
    return jsonify({'data': user})


@user.route('/statuses')
def get_status():
    u = Tweet.query.all()[2]
    tweet = tweet_serializer.dump(u)
    print(tweet)
    return jsonify({'data': tweet})


@user.route('/followers')
def get_followers():
    u = User.query.all()[0].followers.all()
    users = users_serializer.dump(u)
    print(users)
    return jsonify({'data': users})


@user.route('/followed')
def get_followed():
    u = User.query.all()[0].followed.all()
    users = users_serializer.dump(u)
    print(users)
    return jsonify({'data': users})
