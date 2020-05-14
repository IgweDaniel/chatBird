from app.models import db, User, Tweet, ma
from flask import Flask
import os


from app.utils import mail, generate_code
basedir = os.path.abspath(os.path.dirname(__file__))


def loadDB():
    u1 = User(username='daniel', email='daniel@mail.com')
    u2 = User(username='test', email='test@test.com')
    s1 = Tweet(text='Who you, who be you', user=u1)
    s2 = Tweet(text='I am the Indaboski', user=u2, in_reply_to_status=s1)
    s3 = Tweet(text='Mad Oh!', user=u1, in_reply_to_status=s2)
    s4 = Tweet(text='Daniel Igwe is a good man', user=u2)

    db.session.add(u1)
    db.session.add(u2)
    db.session.add_all([s1, s2, s3, s4])
    db.session.commit()
    u1.follow(u2)
    u2.follow(u1)
    db.session.commit()


def create_app(config):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(
        basedir, 'database.db')

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    # enter your email here
    app.config['MAIL_USERNAME'] = 'gmailusername'

    app.config['MAIL_DEFAULT_SENDER'] = 'gmailusername'
    app.config['MAIL_PASSWORD'] = 'gmailpassword'
    db.init_app(app)
    ma.init_app(app)
    mail.init_app(app)
    with app.app_context():
        db.drop_all()
        db.create_all()
        loadDB()
    from app.user import user as userBluePrint
    app.register_blueprint(userBluePrint)
    return app
