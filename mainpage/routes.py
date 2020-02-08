import os
import secrets
from PIL import Image
from flask import render_template, flash, url_for, redirect, request, abort, send_file
from mainpage import app, db, bcrypt, mail
from mainpage.models import User, Post, Comment, Resource
from mainpage.forms import RegistrationForm, LoginForm, UpdateAccountForm, EventForm, RequestResetForm, ResetPasswordForm, CommentForm, UploadResourceForm
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

def save_picture(form_picture):
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_picture.filename)
	picture_fn = random_hex + f_ext
	picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
	output_size = (125, 125)
	i = Image.open(form_picture)
	i.thumbnail(output_size)
	i.save(picture_path)
	return picture_fn

def save_resource(form_resource):
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_resource.filename)
	resource_fn = random_hex + f_ext
	resource_path = os.path.join(app.root_path, 'static/resources', resource_fn)
	form_resource.save(resource_path)
	return resource_fn

def send_reset_email(user):
	token = user.get_reset_token()
	msg = Message('Password Reset Request', sender='imsb5678@gmail.com', recipients=[user.email])
	msg.body = f"To reset your password, visit {url_for('reset_token', token=token, _external=True)}"
	mail.send(msg)

@app.route('/')
def home():
	return render_template('home.html', title="Home Page")

@app.route('/about')
def about():
	return render_template('about.html', title="Aboute Page")

@app.route('/events')
def news():
	page = request.args.get('page', 1, type=int)
	posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
	return render_template('events.html', title="Recent Events", posts=posts)

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
	form = UpdateAccountForm()
	if form.validate_on_submit():
		if form.picture.data:
			if current_user.image_file != 'default.png':
				old_picture = os.path.join(app.root_path, 'static/profile_pics', current_user.image_file)
				os.remove(old_picture)
			picture_file = save_picture(form.picture.data)
			current_user.image_file = picture_file
		current_user.username = form.username.data
		db.session.commit()
		flash('Your account has been updated.')
		return redirect(url_for('account'))
	elif request.method == 'GET':
		form.username.data = current_user.username
	image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
	return render_template('account.html', title="Account", image_file=image_file, form=form)

@app.route('/user/<string:username>')
def student_page(username):
	user = User.query.filter_by(username=username).first_or_404()
	return render_template('student_page.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(username=form.username.data, email=form.email.data, password=hashed_password)
		db.session.add(user)
		db.session.commit()
		login_user(user)
		flash("Registration is Successful. Welcome, {}.".format(form.username.data))
		return redirect(url_for('home'))
	return render_template('register.html', title="Register Page", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('home'))
		else:
			flash("Login unsuccessful. Please check for email and password.")
	return render_template('login.html', title="Login Page", form=form)

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('login'))

@app.route('/event/new', methods=['GET', 'POST'])
@login_required
def new_event():
	form = EventForm()
	if form.validate_on_submit():
		if form.tldr.data:
			post = Post(title=form.title.data, content=form.content.data, author=current_user, tldr=form.tldr.data)
		else:
			post = Post(title=form.title.data, content=form.content.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		return redirect(url_for('news'))
	return render_template('create_event.html', title="New Event", form=form, legend='Create New Event')

@app.route('/event/<post_id>', methods=['GET', 'POST'])
def event(post_id):
	post = Post.query.get_or_404(post_id)
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(content=form.content.data, commenter=current_user, source=post)
		db.session.add(comment)
		db.session.commit()
		return redirect(url_for('event', post_id=post.id))
	comments = Comment.query.filter_by(source=post)
	return render_template('event.html', title="Event Details", post=post, form=form, comments=comments)

@app.route('/event/<post_id>/update', methods=['GET', 'POST'])
@login_required
def update_event(post_id):
	post = Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)
	form = EventForm()
	if form.validate_on_submit():
		post.title = form.title.data
		post.content = form.content.data
		db.session.commit()
		flash('The Event Information has been updated.')
		return redirect(url_for('event', post_id=post.id))
	elif request.method == 'GET':
		form.title.data = post.title
		form.content.data = post.content
	return render_template('create_event.html', title="Update Event Information", form=form, legend='Update Event Information')

@app.route('/event/<post_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_event(post_id):
	post = Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)
	comments = Comment.query.filter_by(post_id=post.id)
	for comment in comments:
		db.session.delete(comment)
	db.session.delete(post)
	db.session.commit()
	flash('The Event has been deleted.')
	return redirect(url_for('news'))

@app.route('/upload_resources', methods=['GET', 'POST'])
@login_required
def upload_resources():
	form = UploadResourceForm()
	if form.validate_on_submit():
		new_resource = save_resource(form.content.data)
		resource = Resource(title=form.title.data , resource=new_resource)
		db.session.add(resource)
		db.session.commit()
		return redirect(url_for('resources'))
	return render_template('upload_resources.html', title="Upload Resources", form=form)

@app.route('/resources')
@login_required
def resources():
	resources = Resource.query.all()
	return render_template('resources.html', title="Resources", resources=resources)

@app.route('/return_files/<destination>', methods=['GET', 'POST'])
def return_files(destination):
	return send_file(os.path.join(app.root_path, 'static/resources', destination))

@app.route('/resources/<destination>/delete', methods=['GET', 'POST'])
@login_required
def delete_resource(destination):
	resource = Resource.query.filter_by(resource=destination).first()
	db.session.delete(resource)
	db.session.commit()
	flash('The File has been deleted.')
	return redirect(url_for('resources'))

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RequestResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		send_reset_email(user)
		flash('An email has been sent with instructions to reset your password.')
		return redirect(url_for('login'))
	return render_template('reset_request.html', title="Reset Password", form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	user = User.verify_reset_token(token)
	if user is None:
		flash('That is an invalid/expired token')
	form = ResetPasswordForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user.password = hashed_password
		db.session.commit()
		flash("Your password has been updated.")
		return redirect(url_for('login'))
	return render_template('reset_token.html', title='Reset Password', form=form)





