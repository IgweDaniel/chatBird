from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from flask import request, jsonify, Blueprint
from sqlalchemy import exc
from app.models import db, User, UserSchema, Token
from app.utils import generate_token, protected, send_mail, generate_code, decode_token

user = Blueprint('user', __name__, url_prefix='/user')

user_serializer = UserSchema()
users_serializer = UserSchema(many=True)


@user.route('/create', methods=['POST'])
def create_user():
    data = request.get_json()
    code = generate_code()
    if not data:
        return jsonify({'error': {'message': 'Invalid Credentials'}, 'data': None}), 400
    try:
        user = User(
            username=data['username'], email=data['email'], code=code, password_hash=data['password'])
        user.insert()
        token = Token(user_id=user.id, code=code)
        token.insert()
    except exc.IntegrityError:
        return jsonify({'error': {'message': 'user already exists'}, 'data': None}), 400

    send_mail('Email Verification', user.email,
              'mail.html', code=code, username=user.username)

    return jsonify({'error': None, 'data': "success"}), 201


@user.route('/auth', methods=['POST'])
def authenticate_user():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'error': {'message': 'Invalid Credentials'}, 'data': None}), 400
    if not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': {'message': 'Invalid Credentials'}, 'data': None}), 400
    if not user.verified:
        return jsonify({'error': {'message': 'please verify account'}}), 400
    token = generate_token({'id': user.id, 'username': user.username})
    return jsonify({'error': None, 'data': {'token': token}}), 200


@user.route('/verify', methods=['POST'])
def verify_user():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'error': {'message': 'Invalid Credentials'}, 'data': None}), 400

    if user.verified:
        return jsonify({'error': {'message': 'Verified', }, 'data': None}), 400

    code = Token.query.filter_by(user_id=user.id).first()
    if code.code != data['code'] and code.issuedAt < datetime.utcnow():
        return jsonify({'error': {'message': 'Verification Failed'}, 'data': None}), 400
    db.session.delete(code)
    db.session.commit()
    token = generate_token(
        {'id': user.id, 'username': user.username})
    return jsonify({'error': None, 'data': {'token': token}}), 200


@user.route('/send_token', methods=['POST'])
def send_verification_code():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'error': {'message': 'Invalid Credentials'}, 'data': None}), 400
    if user.verified:
        return jsonify({'error': {'message': 'Verified'}, 'data': None}), 400
    code = generate_code()
    token = Token(user_id=user.id, code=code)
    db.session.add(token)
    db.session.commit()
    send_mail('Email Verification', user.email,
              'mail.html', code=code, username=user.username)
    return jsonify({'error': None, 'data': "success"}), 200


@user.route('/')
@user.route('/index', methods=['GET'])
def get_all_users():
    u = User.query.filter_by(verified=True).all()
    users = users_serializer.dump(u)
    return jsonify({'error': None, 'data': users}), 200


@user.route('/<int:user_id>', methods=['GET'])
def get_a_user(user_id):
    u = User.query.filter_by(verified=True, id=user_id).first()
    if not u:
        return jsonify({'error': {'message': 'Invalid User', }, 'data': None}), 404
    users = user_serializer.dump(u)
    return jsonify({'error': None, 'data': users}), 200


@user.route('/forgot_password', methods=['POST'])
def forgot_pssword():
    data = request.get_json()
    u = User.query.filter_by(email=data['email']).first()
    if not u:
        return jsonify({'error': {'message': 'Invalid User', }, 'data': None}), 404
    token = generate_token({'id': u.id})
    send_mail('Password Rest Request', u.email,
              'reset_password.html', link=f'http://localhost:5000/reset_password/{token}', username=u.username)
    return jsonify({'error': None, 'data': "success"}), 200


@user.route('/reset_password/<string:token>', methods=['POST'])
def reset_pssword(token):
    d_token = decode_token(token)
    if d_token == 'Invalid token' or d_token == 'Signature expired':
        return jsonify({'error': {'message': 'malformed token'}, 'data': None}), 401

    data = request.get_json()
    u = User.query.filter_by(id=d_token['id']).first()
    if not u:
        return jsonify({'error': {'message': 'malformed token'}, 'data': None}), 401
    u.password_hash = generate_password_hash(data['password'])
    db.session.commit()
    return jsonify({'error': None, 'data': "success"}), 200


@user.route('/friendships/create', methods=['POST'])
@protected
def follow_user(current_user):
    data = request.get_json()
    u = User.query.filter_by(id=data['id']).first()
    if not u:
        return jsonify({'error': {'message': 'Invalid User', }, 'data': None}), 404
    current_user.follow(u)
    db.session.commit()
    return jsonify({'error': None, 'data': "success"}), 200


@user.route('/friendships/delete', methods=['POST'])
@protected
def unfollow_user(current_user):
    data = request.get_json()
    u = User.query.filter_by(id=data['id']).first()
    if not u:
        return jsonify({'error': {'message': 'Invalid User', }, 'data': None}), 404
    current_user.unfollow(u)
    db.session.commit()
    return jsonify({'error': None, 'data': "success"}), 200


@user.route('/followers')
def get_followers():
    u = User.query.all()[0].followers.all()
    users = users_serializer.dump(u)
    print(users)
    return jsonify({'data': users})


@user.route('/followed')
def get_followed():
    u = User.query.all()[0].followed.all()
    user = user_serializer.dump(u)
    return jsonify({'data': user})
