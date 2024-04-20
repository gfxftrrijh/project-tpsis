from flask import Blueprint, render_template, redirect, url_for, flash, make_response
from flask_login import login_user, current_user, logout_user
from .forms import LoginForm, RegistrationForm, PaymentForm, TransferForm
from .models import User, Transaction
from .extensions import db
from werkzeug.security import generate_password_hash
from reportlab.pdfgen import canvas
import datetime

# Инициализация Blueprint
main_blueprint = Blueprint('main', __name__)


@main_blueprint.route('/')
def home():
    return render_template('base.html')


@main_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.admin_dashboard' if current_user.is_admin else 'main.user_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.admin_dashboard' if user.is_admin else 'main.user_dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)


@main_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.admin_dashboard' if current_user.is_admin else 'main.user_dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password_hash=hashed_password, is_admin=False)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)


@main_blueprint.route('/admin_dashboard')
def admin_dashboard():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('You must be an admin to view this page.')
        return redirect(url_for('main.login'))
    return render_template('admin_dashboard.html')


@main_blueprint.route('/user_dashboard')
def user_dashboard():
    if not current_user.is_authenticated:
        flash('You must be logged in to view this page.')
        return redirect(url_for('main.login'))
    return render_template('user_dashboard.html')


@main_blueprint.route('/make_payment', methods=['GET', 'POST'])
def make_payment():
    if not current_user.is_authenticated:
        flash('You must be logged in to perform this action.')
        return redirect(url_for('main.login'))

    form = PaymentForm()
    if form.validate_on_submit():
        # Предположим, что у вас есть логика для сохранения платежа
        flash('Payment successful!')
        return redirect(url_for('main.user_dashboard'))
    return render_template('make_payment.html', form=form)


@main_blueprint.route('/transfer_money', methods=['GET', 'POST'])
def transfer_money():
    if not current_user.is_authenticated:
        flash('You must be logged in to perform this action.')
        return redirect(url_for('main.login'))

    form = TransferForm()
    if form.validate_on_submit():
        # Предположим, что у вас есть логика для перевода денег
        flash('Transfer successful!')
        return redirect(url_for('main.user_dashboard'))
    return render_template('transfer_money.html', form=form)


@main_blueprint.route('/view_history')
def view_history():
    if not current_user.is_authenticated:
        flash('You must be logged in to view this page.')
        return redirect(url_for('main.login'))

    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).all()
    if not transactions:
        flash('No transactions found.')
    return render_template('view_history.html', transactions=transactions)


@main_blueprint.route('/export_pdf')
def export_pdf():
    if not current_user.is_authenticated:
        flash('You must be logged in to view this page.')
        return redirect(url_for('main.login'))

    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).all()
    response = make_response()
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=transactions.pdf'

    p = canvas.Canvas(response)
    p.drawString(100, 750, "Transaction History:")
    y = 730
    for transaction in transactions:
        p.drawString(100, y,
                     f"{transaction.timestamp.strftime('%Y-%m-%d %H:%M')} - {transaction.type} - ${transaction.amount}")
        y -= 20
    p.showPage()
    p.save()
    return response


@main_blueprint.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.login'))
