from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy.dialects import postgresql
import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_PERMANENT'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRES_DATABASE','sqlite:///site.db')


#postgres://default:y5AmTrIcR4zW@ep-royal-lake-92857756.us-east-1.postgres.vercel-storage.com:5432/verceldb

db = SQLAlchemy(app)

login_manager = LoginManager(app)
migrate = Migrate(app, db)

# Define the User class
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class PostForm(FlaskForm):
    business_idea = StringField('Business Idea', validators=[DataRequired()])
    contact_information = StringField('Contact Information', validators=[DataRequired()])
    submit = SubmitField('Post')  

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_idea = db.Column(db.String(200), nullable=False)
    contact_information = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('posts', lazy=True))

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html', current_user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken. Please choose another username.', 'danger')
            return redirect(url_for('register'))
        
        # Check if the email already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered. Please use a different email address.', 'danger')
            return redirect(url_for('register'))



        # Use the default hashing method
        hashed_password = generate_password_hash(password)

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    form = PostForm()  # Replace YourFormClass with the actual form class you are using

    if request.method == 'POST' and form.validate_on_submit():
        # Extract data from the form
        business_idea = form.business_idea.data
        contact_information = form.contact_information.data

        # Create a new post instance
        new_post = Post(
            business_idea=business_idea,
            contact_information=contact_information,
            user_id=current_user.id
        )

        # Add the new post to the database session
        db.session.add(new_post)

        # Commit the changes to the database
        db.session.commit()

        # Redirect to the explore page after posting
        return redirect(url_for('explore'))

    return render_template('post.html', form=form)

@app.route('/explore')
def explore():
    # Retrieve all business ideas from the database
    all_business_ideas = Post.query.all()
    all_contact_information = Post.query.all()

    # Pass the list of business ideas to the template
    return render_template('explore.html', posts=all_business_ideas, contact_information=all_contact_information)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
