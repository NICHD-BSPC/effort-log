from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap

db = SQLAlchemy()


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)
    Bootstrap(app)

    db.init_app(app)
    migrate = Migrate(app, db)

    with app.app_context():
        from . import routes, models

        return app
