from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from mainpage import db, login_manager, app
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	image_file = db.Column(db.String(20), default='default.png')
	password = db.Column(db.String(60), nullable=False)
	level = db.Column(db.String(20))
	posts = db.relationship('Post', backref='author', lazy=True)
	comments = db.relationship('Comment', backref='commenter', lazy=True)

	def get_reset_token(self, expires_sec=1800):
		s = Serializer(app.config['SECRET_KEY'], expires_sec)
		return s.dumps({'user_id': self.id}).decode('utf-8')

	def verify_reset_token(token):
		s = Serializer(app.config['SECRET_KEY'])
		try:
			user_id = s.loads(token)['user_id']
		except:
			return None
		return User.query.get(user_id)

	def __repr__(self):
		return "Username: {}.".format(self.username)

class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(100), nullable=False)
	date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	tldr = db.Column(db.String(200))
	content = db.Column(db.Text, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	comments = db.relationship('Comment', backref='source', lazy=True)

	def __repr__(self):
		return "Title: {}.".format(self.title)

class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	content = db.Column(db.Text, nullable=False)
	author = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
	post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Resource(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(20), nullable=False)
	resource = db.Column(db.String(20))