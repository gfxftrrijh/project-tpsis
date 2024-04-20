from flask import Flask
from .extensions import db, login_manager
from werkzeug.security import generate_password_hash
import pymysql
from .views import main_blueprint
from .models import User


def create_app():
    app = Flask(__name__)


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
