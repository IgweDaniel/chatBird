from app.models import db, User, Tweet, ma
from flask import Flask
import os


from app.utils import mail, generate_code
basedir = os.path.abspath(os.path.dirname(__file__))


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    # enter your email here

    db.init_app(app)
    ma.init_app(app)
    mail.init_app(app)
    with app.app_context():
        db.create_all()

    from app.user import user as userBluePrint
    from app.tweet import status as statusBluePrint
    app.register_blueprint(userBluePrint)
    app.register_blueprint(statusBluePrint)
    return app
