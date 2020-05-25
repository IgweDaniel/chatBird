import jwt
from functools import wraps
from flask import jsonify, request, render_template, current_app
from datetime import datetime, timedelta
from app.models import User, db
from flask_mail import Message, Mail
from concurrent.futures import ThreadPoolExecutor
import random
import math

mail = Mail()
SECRET = "myownsecret"


def protected(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'error': {'message': 'token is missing', 'code': 401}, 'data': None})

        data = decode_token(token)

        if data == 'Invalid token' or data == 'Signature expired':
            return jsonify({'error': {'message': 'malformed token', 'code': 401}, 'data': None})

        current_user = User.query.filter_by(id=data['id']).first()
        if not current_user:
            return jsonify({'error': {'message': 'malformed token', 'code': 401}, 'data': None})
        if not current_user.verified:
            return jsonify({'error': {'message': 'please verify account', 'code': 400}, 'data': None})

        return f(current_user, *args, **kwargs)

    return decorated_function


def generate_token(data, expire=timedelta(days=0, seconds=3600)):
    try:
        payload = {
            'exp': datetime.utcnow() + expire,
            'iat': datetime.utcnow(),
            'sub': data
        }
        token = jwt.encode(
            payload,
            SECRET,
            algorithm='HS256'
        )
        return token.decode("utf-8")
    except Exception as e:
        return e


def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET, algorithms='HS256')
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Signature expired'
    except jwt.InvalidTokenError:
        return 'Invalid token'


def generate_code():
    digits = [i for i in range(0, 10)]
    random_str = ""
    for _ in range(6):
        index = math.floor(random.random() * 10)
        random_str += str(digits[index])
    return random_str


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)
    # print('sent')


def send_mail(subject, recipient, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(
        subject, sender='igwedanielchi@gmail.com', recipients=[recipient])
    msg.html = render_template(template, **kwargs)
    with ThreadPoolExecutor(3) as executor:
        executor.submit(lambda arg: send_async_email(*arg), [app, msg])
