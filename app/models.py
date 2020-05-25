from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from flask_marshmallow import Marshmallow
from marshmallow import fields
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


class Favorites(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'))

    def __repr__(self):
        return '<Favorite {} {}>'.format(self.user_id, self.tweet_id)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    avatar = db.Column(db.String(128), default="url for default user mage")
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    code = db.Column(db.String(6))
    verified = db.Column(db.Boolean, default=False)
    tweets = db.relationship('Tweet', backref='user', lazy='dynamic')
    followed = db.relationship('User', secondary=followers, primaryjoin=(followers.c.follower_id == id), secondaryjoin=(
        followers.c.followed_id == id), backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    favorite_tweets = db.relationship(
        'Favorites',
        backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def get_followed_tweets(self):
        return Tweet.query.join(followers, followers.c.followed_id == Tweet.user_id).filter(
            followers.c.follower_id == self.id).order_by(
            Tweet.timestamp.desc())

    def like(self, tweet):
        if not self.has_liked_tweet(tweet):
            like = Favorites(user_id=self.id, tweet_id=tweet.id)
            db.session.add(like)

    def unlike(self, tweet):
        if self.has_liked_tweet(tweet):
            Favorites.query.filter_by(
                user_id=self.id,
                tweet_id=tweet.id).delete()

    def has_liked_tweet(self, tweet):
        return Favorites.query.filter(
            Favorites.user_id == self.id,
            Favorites.tweet_id == tweet.id).count() > 0


def hashPassword(mapper, connection, target):
    target.password_hash = generate_password_hash(target.password_hash)


event.listen(
    User, 'before_insert', hashPassword)


class UserSchema(ma.Schema):
    # followers =ma.Nested("self",many=True, exclude=('followers',"followed","tweets"))
    # followed =ma.Nested("self",many=True, exclude=('followers',"followed","tweets"))
    # tweets =ma.Nested(lambda:TweetSchema(),many=True)

    followers_count = fields.Function(lambda obj: obj.followers.count())
    followed_count = fields.Function(lambda obj: obj.followed.count())

    class Meta:
        fields = ("email", "id", "username",
                  "followed_count", "followers_count")


class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    retweet_status_id = db.Column(db.Integer, db.ForeignKey('tweet.id'))
    retweets = db.relationship(
        'Tweet', foreign_keys=[retweet_status_id], backref=db.backref('retweet_status', remote_side=[id]),
        lazy='dynamic')

    in_reply_to_status_id = db.Column(db.Integer, db.ForeignKey('tweet.id'))

    replies = db.relationship(
        'Tweet', foreign_keys=[in_reply_to_status_id], backref=db.backref('in_reply_to_status', remote_side=[id]),
        lazy='dynamic')
    favorites = db.relationship('Favorites', backref='tweet', lazy='dynamic')

    def insert(self):
        db.session.add(self)
        db.session.commit()


def get_Like_state(obj, context):
    if not context.get('user', None):
        return False
    else:
        return context['user'].has_liked_tweet(obj)


class TweetSchema(ma.Schema):
    in_reply_to_status = ma.Nested(
        lambda: TweetSchema(exclude=('in_reply_to_status', )))
    retweet_status = ma.Nested(
        lambda: TweetSchema(exclude=('retweet_status', 'in_reply_to_status')))
    # user=ma.Nested(UserSchema,exclude=("followers","followed","tweets"))
    # user = ma.Nested(UserSchema, exclude=("tweets",))
    reply_count = fields.Function(lambda obj: obj.replies.count())
    like_count = fields.Function(lambda obj: obj.favorites.count())
    is_liked = fields.Function(
        lambda obj, context: get_Like_state(obj, context))
    user = ma.Nested(UserSchema)

    class Meta:
        fields = ("text", "id", "timestamp",
                  "in_reply_to_status", "user", "reply_count", "is_liked", "like_count", 'retweet_status')
