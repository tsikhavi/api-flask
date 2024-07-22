from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    phone_number = db.Column(db.String(15))
    password = db.Column(db.String(60))
    token = db.Column(db.String(100))
    verified = db.Column(db.String(1), default='0', nullable=False)

class Subscription(db.Model):
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    subscribed_at = db.Column(db.DateTime, default=db.func.current_timestamp())
