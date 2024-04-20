from flask_wtf import FlaskForm
from wtforms import DecimalField, StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo
from .models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')


class PaymentForm(FlaskForm):
    amount = DecimalField('Amount', validators=[DataRequired()])
    description = StringField('Описание')  # Необязательное поле
    submit = SubmitField('Make Payment')


class TransferForm(FlaskForm):
    recipient_username = StringField('Recipient Username', validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired()])
    submit = SubmitField('Transfer')

