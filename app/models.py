from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from flask_marshmallow import Marshmallow
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
ma = Marshmallow()


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    code = db.Column(db.String(6))
    issuedAt = db.Column(db.DateTime(), default=datetime.utcnow)

    def insert(self):
        db.session.add(self)
        db.session.commit()


followers = db.Table('followers',
                     db.Column('follower_id', db.Integer,
                               db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer,
                               db.ForeignKey('user.id'))
                     )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    avatar = db.Column(db.String(128), default="url for default user mage")
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    code = db.Column(db.String(6))
    verified = db.Column(db.Boolean, default=False)
    tweets = db.relationship('Tweet', backref='user', lazy='dynamic')
    followers_count = db.Column(db.Integer, default=0)
    followed_count = db.Column(db.Integer, default=0)
    followed = db.relationship('User', secondary=followers, primaryjoin=(followers.c.follower_id == id), secondaryjoin=(
        followers.c.followed_id == id), backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def follow(self, user):
        if not self.is_following(user):
            self.followed_count += 1
            user.followers_count += 1
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed_count -= 1
            user.followers_count -= 1
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0


def hashPassword(mapper, connection, target):
    target.password_hash = generate_password_hash(target.password_hash)


event.listen(
    User, 'before_insert', hashPassword)


class UserSchema(ma.Schema):
    # followers =ma.Nested("self",many=True, exclude=('followers',"followed","tweets"))
    # followed =ma.Nested("self",many=True, exclude=('followers',"followed","tweets"))
    # tweets =ma.Nested(lambda:TweetSchema(),many=True)
    class Meta:
        fields = ("email", "id", "username",
                  "followed_count", "followers_count")


class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    in_reply_to_status_id = db.Column(db.Integer, db.ForeignKey('tweet.id'))
    replies = db.relationship(
        'Tweet', backref=db.backref('in_reply_to_status', remote_side=[id]),
        lazy='dynamic')
    reply_count = db.Column(db.Integer, default=0)

    def insert(self):
        db.session.add(self)
        db.session.commit()


class TweetSchema(ma.Schema):
    in_reply_to_status = ma.Nested(
        lambda: TweetSchema(exclude=('in_reply_to_status',)))
    # user=ma.Nested(UserSchema,exclude=("followers","followed","tweets"))
    # user = ma.Nested(UserSchema, exclude=("tweets",))
    user = ma.Nested(UserSchema)

    class Meta:
        fields = ("text", "id", "timestamp", "in_reply_to_status", "user")
