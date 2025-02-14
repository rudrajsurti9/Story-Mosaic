from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    stories = db.relationship('Story', backref='author', lazy=True)
    friends = db.relationship('User', 
                            secondary='friendships',
                            primaryjoin='User.id==friendships.c.user_id',
                            secondaryjoin='User.id==friendships.c.friend_id',
                            lazy='dynamic')

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contributors = db.relationship('User', 
                                 secondary='story_contributors',
                                 backref=db.backref('contributed_stories', lazy=True))

# Association tables
friendships = db.Table('friendships',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'))
)

story_contributors = db.Table('story_contributors',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('story_id', db.Integer, db.ForeignKey('story.id'))
)
