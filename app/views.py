from flask_login import login_user, current_user
from flask import render_template, redirect, url_for, flash, Blueprint
from .forms import LoginForm, RegistrationForm
from .models import User
from flask import Blueprint, render_template
from .extensions import db
from werkzeug.security import generate_password_hash


main_blueprint = Blueprint('main', __name__)


@main_blueprint.route('/')
def home():
    return render_template('base.html')


@main_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))  # Пользователь уже вошел

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))  # Редирект для администратора
            else:
                return redirect(url_for('main.dashboard'))  # Редирект для пользователя
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)


@main_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password_hash=generate_password_hash(form.password.data))
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)
