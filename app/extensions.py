from flask_pymongo import PyMongo

# Setup MongoDB here
mongo = PyMongo()

def init_app(app):
    app.config['MONGO_URI'] = 'mongodb://localhost:27017/local'
    mongo.init_app(app)