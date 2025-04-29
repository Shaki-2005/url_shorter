from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Link, Click
from forms import RegisterForm, LoginForm
from utils import generate_short_code, get_client_ip
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables_once():
    if not hasattr(app, 'db_initialized'):
        db.create_all()
        app.db_initialized = True


@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        original_url = request.form['original_url']
        short_code = generate_short_code()
        new_link = Link(original_url=original_url, short_code=short_code, user_id=current_user.id)
        db.session.add(new_link)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/<short_code>')
def redirect_url(short_code):
    link = Link.query.filter_by(short_code=short_code).first_or_404()
    click = Click(link_id=link.id, timestamp=datetime.utcnow(), ip_address=get_client_ip(request), user_agent=request.headers.get('User-Agent'))
    db.session.add(click)
    db.session.commit()
    return redirect(link.original_url)

@app.route('/dashboard')
@login_required
def dashboard():
    links = Link.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', links=links)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        flash("Invalid credentials.")
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
