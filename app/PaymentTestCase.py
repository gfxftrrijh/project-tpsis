import unittest
from flask import Flask, url_for
from flask_testing import TestCase
from pythonProject1 import create_app, db
from pythonProject1.models import User, BankAccount, Transaction
from flask_login import login_user


class PaymentTestCase(TestCase):

    def create_app(self):
        app = create_app('testing')
        return app
    100% lines covered

    def setUp(self):
        db.create_all()
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()

        self.account = BankAccount(user_id=self.user.id, balance=1000)
        db.session.add(self.account)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login(self):
        with self.client:
            login_user(self.user)

    def test_make_payment_success(self):
        self.login()
        response = self.client.post(url_for('main.make_payment'), data={'amount': 100})
        self.assertRedirects(response, url_for('main.user_dashboard'))
        self.assertEqual(self.account.balance, 900)
        transaction = Transaction.query.filter_by(account_id=self.account.account_id).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, -100)

    def test_make_payment_insufficient_funds(self):
        self.login()
        response = self.client.post(url_for('main.make_payment'), data={'amount': 2000})
        self.assertIn(b'Insufficient funds!', response.data)
        self.assertEqual(self.account.balance, 1000)

    def test_transfer_money_success(self):
        self.login()
        recipient = User(username='recipient', email='recipient@example.com')
        recipient.set_password('password')
        db.session.add(recipient)
        db.session.commit()

        recipient_account = BankAccount(user_id=recipient.id, balance=500)
        db.session.add(recipient_account)
        db.session.commit()

        response = self.client.post(url_for('main.transfer_money'),
                                    data={'recipient_username': 'recipient', 'amount': 100})
        self.assertRedirects(response, url_for('main.user_dashboard'))
        self.assertEqual(self.account.balance, 900)
        self.assertEqual(recipient_account.balance, 600)

    def test_transfer_money_recipient_not_found(self):
        self.login()
        response = self.client.post(url_for('main.transfer_money'),
                                    data={'recipient_username': 'nonexistent', 'amount': 100})
        self.assertIn(b'Recipient not found.', response.data)
        self.assertEqual(self.account.balance, 1000)

    def test_transfer_money_to_self(self):
        self.login()
        response = self.client.post(url_for('main.transfer_money'),
                                    data={'recipient_username': 'testuser', 'amount': 100})
        self.assertIn(b'You cannot transfer money to yourself.', response.data)
        self.assertEqual(self.account.balance, 1000)

    def test_transfer_money_insufficient_funds(self):
        self.login()
        recipient = User(username='recipient', email='recipient@example.com')
        recipient.set_password('password')
        db.session.add(recipient)
        db.session.commit()

        recipient_account = BankAccount(user_id=recipient.id, balance=500)
        db.session.add(recipient_account)
        db.session.commit()

        response = self.client.post(url_for('main.transfer_money'),
                                    data={'recipient_username': 'recipient', 'amount': 2000})
        self.assertIn(b'Insufficient funds.', response.data)
        self.assertEqual(self.account.balance, 1000)
        self.assertEqual(recipient_account.balance, 500)


if name == 'main':
    unittest.main()