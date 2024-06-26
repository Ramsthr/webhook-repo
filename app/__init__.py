from flask import Flask
from app.webhook.routes import webhook
from app.extensions import init_app as init_mongo

def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(webhook)
    init_mongo(app)
    return app
