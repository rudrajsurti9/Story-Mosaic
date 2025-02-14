from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db, login_manager
from models import User, Story
from forms import LoginForm, RegisterForm, StoryForm, SearchForm

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@app.route('/home')
def home():
    stories = Story.query.order_by(Story.created_at.desc()).all()
    return render_template('home.html', stories=stories)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('home'))
            flash('Invalid email or password. Please try again.', 'error')
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            # Check for existing username with proper error handling
            if User.query.filter_by(username=form.username.data).first():
                flash('This username is already taken. Please choose another.', 'error')
                return render_template('register.html', form=form)

            # Check for existing email with proper error handling
            if User.query.filter_by(email=form.email.data).first():
                flash('An account with this email already exists.', 'error')
                return render_template('register.html', form=form)

            # Create new user with proper error handling
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data)
            )
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')

    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/create_story', methods=['GET', 'POST'])
@login_required
def create_story():
    form = StoryForm()
    if form.validate_on_submit():
        story = Story(
            title=form.title.data,
            content=form.content.data,
            author=current_user
        )
        db.session.add(story)
        db.session.commit()
        return redirect(url_for('story', story_id=story.id))
    return render_template('create_story.html', form=form)

@app.route('/story/<int:story_id>')
def story(story_id):
    story = Story.query.get_or_404(story_id)
    return render_template('story.html', story=story)

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    users = []
    if form.validate_on_submit():
        users = User.query.filter(User.username.like(f'%{form.username.data}%')).all()
    return render_template('search.html', form=form, users=users)

@app.route('/add_friend/<int:user_id>')
@login_required
def add_friend(user_id):
    user = User.query.get_or_404(user_id)
    if user != current_user:
        current_user.friends.append(user)
        db.session.commit()
    return redirect(url_for('profile', username=user.username))

@app.route('/story/<int:story_id>/invite', methods=['POST'])
@login_required
def invite_collaborator(story_id):
    story = Story.query.get_or_404(story_id)
    if story.author != current_user:
        flash('Only the story author can invite collaborators')
        return redirect(url_for('story', story_id=story_id))

    friend_id = request.form.get('friend_id')
    if not friend_id:
        flash('No friend selected')
        return redirect(url_for('story', story_id=story_id))

    friend = User.query.get_or_404(friend_id)
    if friend in story.contributors:
        flash('User is already a collaborator')
    else:
        story.contributors.append(friend)
        db.session.commit()
        flash(f'Added {friend.username} as a collaborator')

    return redirect(url_for('story', story_id=story_id))

@app.route('/story/<int:story_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_story(story_id):
    story = Story.query.get_or_404(story_id)
    if current_user != story.author and current_user not in story.contributors:
        flash('You do not have permission to edit this story')
        return redirect(url_for('story', story_id=story_id))

    form = StoryForm()
    if form.validate_on_submit():
        story.title = form.title.data
        story.content = form.content.data
        db.session.commit()
        flash('Story updated successfully')
        return redirect(url_for('story', story_id=story.id))

    form.title.data = story.title
    form.content.data = story.content
    return render_template('edit_story.html', form=form, story=story)