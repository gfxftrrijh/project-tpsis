from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from .extensions import db
from .models import User
from werkzeug.security import generate_password_hash
import pymysql
from .views import main_blueprint
from config import Config  # Импорт класса конфигурации

# Создаем экземпляр LoginManager
login_manager = LoginManager()
migrate = Migrate()  # Добавление экземпляра Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)  # Инициализация Migrate с Flask приложением и экземпляром SQLAlchemy
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = 'main.login'

    app.register_blueprint(main_blueprint)

    @app.cli.command("create-admin")
    def create_admin():
        # Параметры подключения к базе данных
        host = 'localhost'  # Адрес сервера MySQL
        user = 'root'  # Ваш MySQL пользователь
        password = '1234'  # Ваш MySQL пароль
        db_name = 'payment_app'  # Имя вашей базы данных

        # Создание хеша пароля
        password_hash = generate_password_hash('1234')

        # Создание подключения к базе данных
        connection = pymysql.connect(host=host, user=user, password=password, db=db_name)
        try:
            with connection.cursor() as cursor:
                # SQL запрос для добавления администратора
                sql = "INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)"
                cursor.execute(sql, ('admin', password_hash, True))

            # Подтверждение транзакции
            connection.commit()
        finally:
            connection.close()

        print("Администратор добавлен.")

    return app
