from flask import Blueprint, render_template, redirect, url_for, flash, make_response
from flask_login import login_user, current_user, logout_user
from .forms import LoginForm, RegistrationForm, PaymentForm, TransferForm
from .models import User, Transaction, BankAccount
from .extensions import db
from werkzeug.security import generate_password_hash
from reportlab.pdfgen import canvas
import datetime
import io
from reportlab.lib.pagesizes import letter
from flask import request, redirect, url_for
from .forms import LogoutForm
from flask import render_template


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
        db.session.flush()  # Сохраняем пользователя, чтобы получить его ID для внешнего ключа

        # Создаем банковский счет с начальным балансом 1000
        new_account = BankAccount(user_id=user.id, balance=1000.00)
        db.session.add(new_account)

        db.session.commit()  # Завершаем транзакцию, включая оба объекта
        flash('Congratulations, you are now a registered user with a new bank account!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)


@main_blueprint.route('/admin_dashboard')
def admin_dashboard():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('You must be an admin to view this page.')
        return redirect(url_for('main.login'))

    form = LogoutForm()  # Создаем экземпляр формы
    return render_template('admin_dashboard.html', form=form)


@main_blueprint.route('/user_dashboard')
def user_dashboard():
    if not current_user.is_authenticated:
        flash('You must be logged in to view this page.')
        return redirect(url_for('main.login'))
    return render_template('user_dashboard.html')


@main_blueprint.route('/make_payment', methods=['GET', 'POST'])
def make_payment():
    form = PaymentForm()
    if form.validate_on_submit():
        amount = form.amount.data
        user_account = BankAccount.query.filter_by(user_id=current_user.id).first()

        if user_account and user_account.balance >= amount:
            # Обновление баланса
            user_account.balance -= amount
            db.session.add(user_account)

            # Создание транзакции
            new_transaction = Transaction(
                account_id=user_account.account_id,
                amount=-amount,  # Отрицательное значение для платежа
                type='withdrawal'
            )
            db.session.add(new_transaction)

            db.session.commit()
            flash('Payment successful!')
            return redirect(url_for('main.user_dashboard'))
        else:
            flash('Insufficient funds!')

    return render_template('make_payment.html', form=form)


@main_blueprint.route('/transfer_money', methods=['GET', 'POST'])
def transfer_money():
    form = TransferForm()
    if form.validate_on_submit():
        recipient = User.query.filter_by(username=form.recipient_username.data).first()
        if not recipient:
            flash('Recipient not found.')
            return render_template('transfer_money.html', form=form)

        if recipient.id == current_user.id:
            flash('You cannot transfer money to yourself.')
            return render_template('transfer_money.html', form=form)

        amount = form.amount.data
        sender_account = BankAccount.query.filter_by(user_id=current_user.id).first()
        recipient_account = BankAccount.query.filter_by(user_id=recipient.id).first()

        if sender_account.balance < amount:
            flash('Insufficient funds.')
            return render_template('transfer_money.html', form=form)

        # Обновление балансов
        sender_account.balance -= amount
        recipient_account.balance += amount

        # Создание транзакций
        sender_transaction = Transaction(account_id=sender_account.account_id, amount=-amount, type='withdrawal')
        recipient_transaction = Transaction(account_id=recipient_account.account_id, amount=amount, type='transaction')

        db.session.add(sender_transaction)
        db.session.add(recipient_transaction)
        db.session.commit()

        flash('Transfer successful!')
        return redirect(url_for('main.user_dashboard'))

    return render_template('transfer_money.html', form=form)


@main_blueprint.route('/view_history', methods=['GET', 'POST'])
def view_history():
    if not current_user.is_authenticated:
        flash('You must be logged in to view this page.')
        return redirect(url_for('main.login'))

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sort_order = request.args.get('sort', 'asc')

    # Получаем account_id текущего пользователя
    user_account = BankAccount.query.filter_by(user_id=current_user.id).first()
    if not user_account:
        flash('No bank account found for the current user.')
        return redirect(url_for('main.user_dashboard'))

    query = Transaction.query.filter_by(account_id=user_account.account_id)

    if start_date:
        query = query.filter(Transaction.timestamp >= start_date)
    if end_date:
        query = query.filter(Transaction.timestamp <= end_date)

    if sort_order == 'asc':
        query = query.order_by(Transaction.timestamp.asc())
    else:
        query = query.order_by(Transaction.timestamp.desc())

    transactions = query.all()

    return render_template('view_history.html', transactions=transactions)


@main_blueprint.route('/export_pdf')
def export_pdf():
    if not current_user.is_authenticated:
        flash('You must be logged in to view this page.')
        return redirect(url_for('main.login'))

    # Предполагается, что у пользователя уже есть связанный банковский счет
    account = BankAccount.query.filter_by(user_id=current_user.id).first()
    if not account:
        flash('No bank account found.')
        return redirect(url_for('main.user_dashboard'))

    transactions = Transaction.query.filter_by(account_id=account.account_id).order_by(
        Transaction.timestamp.desc()).all()

    # Создаем PDF в буфере
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.drawString(100, height - 50, "Transaction History:")
    y = height - 100

    for transaction in transactions:
        p.drawString(100, y,
                     f"{transaction.timestamp.strftime('%Y-%m-%d %H:%M')} - {transaction.type} - ${transaction.amount}")
        y -= 20

    p.showPage()
    p.save()

    # Перемещаем указатель в начало буфера
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    buffer.close()
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=transactions.pdf'
    return response



@main_blueprint.route('/manage_users')
def manage_users():
    query = User.query
    filter_term = request.args.get('filter')
    sort_order = request.args.get('sort')
    admin_filter = request.args.get('is_admin')  # Получаем параметр фильтрации по статусу администратора

    if filter_term:
        query = query.filter(User.username.like(f'%{filter_term}%'))

    # Проверяем, есть ли значение у admin_filter, и оно не пустое
    if admin_filter and admin_filter.isdigit():  # Удостоверяемся, что admin_filter содержит числовое значение
        admin_filter_value = bool(int(admin_filter))  # Преобразуем строку в целое число, затем в булево значение
        query = query.filter(User.is_admin == admin_filter_value)

    if sort_order == 'name_asc':
        query = query.order_by(User.username.asc())
    elif sort_order == 'name_desc':
        query = query.order_by(User.username.desc())

    users = query.all()
    return render_template('manage_users.html', users=users)






@main_blueprint.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.home'))


@main_blueprint.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username']
    password = generate_password_hash(request.form['password'])
    new_user = User(username=username, password_hash=password)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('main.manage_users'))


@main_blueprint.route('/delete_user/<int:user_id>', methods=['GET'])
def delete_user(user_id):
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return redirect(url_for('main.manage_users'))


@main_blueprint.route('/view_user/<int:user_id>', methods=['GET'])
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    account = BankAccount.query.filter_by(user_id=user.id).first()
    if account:
        transactions = Transaction.query.filter_by(account_id=account.account_id).order_by(Transaction.timestamp.desc()).all()
    else:
        transactions = []

    return render_template('user_details.html', user=user, transactions=transactions)


@main_blueprint.route('/system_settings')
def system_settings():
    # Здесь может быть код для обработки системных настроек
    return render_template('system_settings.html')


from sqlalchemy import func, extract


@main_blueprint.route('/view_statistics')
def view_statistics():
    total_users = User.query.count()
    total_transactions = Transaction.query.count()
    total_volume = db.session.query(func.sum(Transaction.amount)).scalar() or 0

    transactions_by_type = db.session.query(
        Transaction.type, func.count(Transaction.type)
    ).group_by(Transaction.type).all()

    transactions_by_type = [{'type': type_, 'count': count} for type_, count in transactions_by_type]

    # Получаем данные для динамики транзакций по месяцам
    transaction_dynamics = db.session.query(
        extract('year', Transaction.timestamp).label('year'),
        extract('month', Transaction.timestamp).label('month'),
        func.sum(Transaction.amount).label('total_amount')
    ).group_by('year', 'month').order_by('year', 'month').all()

    # Преобразуем данные в список словарей
    transaction_dynamics = [{'year': year, 'month': month, 'total_amount': total_amount} for year, month, total_amount
                            in transaction_dynamics]

    return render_template('statistics.html', total_users=total_users, total_transactions=total_transactions,
                           total_volume=total_volume, transactions_by_type=transactions_by_type,
                           transaction_dynamics=transaction_dynamics)


@main_blueprint.route('/export_statistics_pdf')
def export_statistics_pdf():
    # Здесь код для сбора статистических данных
    total_users = User.query.count()
    total_transactions = Transaction.query.count()
    transactions_by_type = db.session.query(Transaction.type, db.func.count(Transaction.type)).group_by(
        Transaction.type).all()

    # Создание PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.drawString(72, height - 72, "Statistics Report")
    p.drawString(72, height - 100, f"Total Users: {total_users}")
    p.drawString(72, height - 120, f"Total Transactions: {total_transactions}")

    y = height - 140
    for tran_type, count in transactions_by_type:
        p.drawString(72, y, f"{tran_type}: {count}")
        y -= 20

    p.showPage()
    p.save()

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    buffer.close()
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=statistics_report.pdf'
    return response


@main_blueprint.route('/export_user_pdf/<int:user_id>')
def export_user_pdf(user_id):
    user = User.query.get_or_404(user_id)
    account = BankAccount.query.filter_by(user_id=user.id).first()
    transactions = Transaction.query.filter_by(account_id=account.account_id).order_by(
        Transaction.timestamp.desc()).all()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    p.drawString(72, height - 72, f"Transactions Report for {user.username}")

    y = height - 100
    for transaction in transactions:
        p.drawString(72, y,
                     f"{transaction.timestamp.strftime('%Y-%m-%d %H:%M')} - {transaction.type} - ${transaction.amount}")
        y -= 20

    p.showPage()
    p.save()
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    buffer.close()
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={user.username}_transactions.pdf'
    return response


