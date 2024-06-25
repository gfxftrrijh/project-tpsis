import unittest
from flask import url_for, flash
from flask_testing import TestCase
from pythonProject1 import create_app, db
from pythonProject1.models import User, BankAccount, Transaction
from pythonProject1.forms import TransferForm
from flask_login import login_user, current_user

class TransferMoneyTestCase(TestCase):

    def create_app(self):
        app = create_app('testing')
        return app

    def setUp(self):
        db.create_all()
        self.user1 = User(username='user1', email='user1@example.com')
        self.user2 = User(username='user2', email='user2@example.com')
        self.user1.set_password('password1')
        self.user2.set_password('password2')
        db.session.add(self.user1)
        db.session.add(self.user2)

        self.account1 = BankAccount(user_id=self.user1.id, balance=1000)
        self.account2 = BankAccount(user_id=self.user2.id, balance=500)
        db.session.add(self.account1)
        db.session.add(self.account2)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login_user1(self):
        with self.client:
            login_user(self.user1)

    def test_transfer_money_success(self):
        self.login_user1()
        form = TransferForm()
        form.recipient_username.data = 'user2'
        form.amount.data = 200

        response = self.client.post(url_for('main.transfer_money'), data=form.data, follow_redirects=True)
        self.assert200(response)
        self.assertIn(b'Transfer successful!', response.data)

        # Check balances after transfer
        sender_account = BankAccount.query.filter_by(user_id=self.user1.id).first()
        recipient_account = BankAccount.query.filter_by(user_id=self.user2.id).first()
        self.assertEqual(sender_account.balance, 800)
        self.assertEqual(recipient_account.balance, 700)

        # Check transaction records
        transactions_sender = Transaction.query.filter_by(account_id=sender_account.account_id).all()
        transactions_recipient = Transaction.query.filter_by(account_id=recipient_account.account_id).all()
        self.assertEqual(len(transactions_sender), 1)
        self.assertEqual(len(transactions_recipient), 1)
        self.assertEqual(transactions_sender[0].amount, -200)
        self.assertEqual(transactions_recipient[0].amount, 200)

    def test_transfer_money_recipient_not_found(self):
        self.login_user1()
        form = TransferForm()
        form.recipient_username.data = 'nonexistentuser'
        form.amount.data = 200

        response = self.client.post(url_for('main.transfer_money'), data=form.data, follow_redirects=True)
        self.assert200(response)
        self.assertIn(b'Recipient not found.', response.data)

        # Check that no transactions were recorded
        transactions = Transaction.query.all()
        self.assertEqual(len(transactions), 0)

    def test_transfer_money_self_transfer_attempt(self):
        self.login_user1()
        form = TransferForm()
        form.recipient_username.data = 'user1'  # Transfer to self
        form.amount.data = 200

        response = self.client.post(url_for('main.transfer_money'), data=form.data, follow_redirects=True)
        self.assert200(response)
        self.assertIn(b'You cannot transfer money to yourself.', response.data)

        # Check that no transactions were recorded
        transactions = Transaction.query.all()
        self.assertEqual(len(transactions), 0)

    def test_transfer_money_insufficient_funds(self):
        self.login_user1()
        form = TransferForm()
        form.recipient_username.data = 'user2'
        form.amount.data = 1200  # More than sender's balance

        response = self.client.post(url_for('main.transfer_money'), data=form.data, follow_redirects=True)
        self.assert200(response)
        self.assertIn(b'Insufficient funds.', response.data)

        # Check that no transactions were recorded
        transactions = Transaction.query.all()
        self.assertEqual(len(transactions), 0)

if name == 'main':
    unittest.main()