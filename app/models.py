from app import db
from datetime import datetime

class Author(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(20), index=True)
	blogPosts = db.relationship('BlogPost', backref='author', lazy='dynamic')


class BlogPost(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	author_id = db.Column(db.String(200), db.ForeignKey('author.id'))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)