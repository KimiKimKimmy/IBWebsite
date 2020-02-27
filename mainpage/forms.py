from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from mainpage.models import User

class RegistrationForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
	email = StringField('Email', validators=[DataRequired(),Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Sign Up')

	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user:
			raise ValidationError('The username is already taken.')

	def validate_email(self, email):
		email = User.query.filter_by(email=email.data).first()
		if email:
			raise ValidationError('The email address is already taken.')

class LoginForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(),Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
	picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'img'])])
	submit = SubmitField('Update Your Account')

	def validate_username(self, username):
		if username.data != current_user.username:
			user = User.query.filter_by(username=username.data).first()
			if user:
				raise ValidationError('The username is already taken.')

class EventForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])
	content = TextAreaField('Content', validators=[DataRequired()])
	tldr = TextAreaField('TL;DR')
	picture = FileField('Attached Image', validators=[FileAllowed(['jpg', 'png', 'img'])])
	submit = SubmitField('Publish')

class CommentForm(FlaskForm):
	content = TextAreaField('Content', validators=[DataRequired()])
	submit = SubmitField('Comment')

class UploadResourceForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])
	content = FileField('Upload File', validators=[DataRequired()])
	submit = SubmitField('Upload Resources')

class RequestResetForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(),Email()])
	submit = SubmitField('Request Password Reset')
	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is None:
			raise ValidationError('There is no account with this email, try entering a different one.')

class ResetPasswordForm(FlaskForm):
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Reset Password')
