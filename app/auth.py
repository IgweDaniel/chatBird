from flask import request, jsonify, Blueprint
from app.utils import generate_token, protected
from app.models import db, User
from sqlalchemy import exc
from werkzeug.security import generate_password_hash, check_password_hash

import hashlib

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    try:
        user = User(
            username=data['username'], email=data['email'], password_hash=generate_password_hash(data['password']))
        db.session.add(user)
        db.session.commit()
    except exc.IntegrityError:
        return jsonify({'error': {'message': 'user already exists', 'code': 400}, 'data': None})

    token = generate_token({'id': user.id, 'username': user.username})
    return jsonify({'error': None, 'data': {'token': token.decode("utf-8")}})


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'error': {'message': 'Invalid Credentials', 'code': 400}, 'data': None})
    if not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': {'message': 'Invalid Credentials', 'code': 400}, 'data': None})
    token = generate_token({'id': user.id, 'username': user.username})
    return jsonify({'error': None, 'data': {'token': token.decode("utf-8")}})
