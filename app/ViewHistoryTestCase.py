import unittest
from flask import Flask, url_for
from flask_testing import TestCase
from pythonProject1 import create_app, db
from pythonProject1.models import User, BankAccount, Transaction
from flask_login import login_user, current_user

class ViewHistoryTestCase(TestCase):

    def create_app(self):
        app = create_app('testing')
        return app

    def setUp(self):
        db.create_all()
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()

        self.account = BankAccount(user_id=self.user.id, balance=1000)
        db.session.add(self.account)
        db.session.commit()

        # Adding some transactions
        self.transaction1 = Transaction(account_id=self.account.account_id, amount=-100, type='withdrawal', timestamp='2024-01-01 10:00:00')
        self.transaction2 = Transaction(account_id=self.account.account_id, amount=200, type='deposit', timestamp='2024-01-02 10:00:00')
        db.session.add(self.transaction1)
        db.session.add(self.transaction2)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login(self):
        with self.client:
            login_user(self.user)

    def test_view_history_not_authenticated(self):
        response = self.client.get(url_for('main.view_history'))
        self.assertRedirects(response, url_for('main.login'))

    def test_view_history_no_account(self):
        self.login()
        # Remove account to test the scenario
        db.session.delete(self.account)
        db.session.commit()
        response = self.client.get(url_for('main.view_history'))
        self.assertRedirects(response, url_for('main.user_dashboard'))
        self.assertIn(b'No bank account found for the current user.', response.data)

    def test_view_history_sorted_ascending(self):
        self.login()
        response = self.client.get(url_for('main.view_history', sort='asc'))
        self.assert200(response)
        transactions = response.context['transactions']
        self.assertEqual(transactions[0].timestamp, '2024-01-01 10:00:00')
        self.assertEqual(transactions[1].timestamp, '2024-01-02 10:00:00')

    def test_view_history_sorted_descending(self):
        self.login()
        response = self.client.get(url_for('main.view_history', sort='desc'))
        self.assert200(response)
        transactions = response.context['transactions']
        self.assertEqual(transactions[0].timestamp, '2024-01-02 10:00:00')
        self.assertEqual(transactions[1].timestamp, '2024-01-01 10:00:00')

    def test_view_history_start_date(self):
        self.login()
        response = self.client.get(url_for('main.view_history', start_date='2024-01-02'))
        self.assert200(response)
        transactions = response.context['transactions']
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].timestamp, '2024-01-02 10:00:00')

    def test_view_history_end_date(self):
        self.login()
        response = self.client.get(url_for('main.view_history', end_date='2024-01-01'))
        self.assert200(response)
        transactions = response.context['transactions']
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].timestamp, '2024-01-01 10:00:00')

if name == 'main':
    unittest.main()