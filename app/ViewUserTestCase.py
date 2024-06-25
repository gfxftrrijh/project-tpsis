import unittest
from flask import url_for
from flask_testing import TestCase
from pythonProject1 import create_app, db
from pythonProject1.models import User, BankAccount, Transaction


class ViewUserTestCase(TestCase):

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

        self.transaction1 = Transaction(account_id=self.account.account_id, amount=-100, type='withdrawal',
                                        timestamp='2024-01-01 10:00:00')
        self.transaction2 = Transaction(account_id=self.account.account_id, amount=200, type='deposit',
                                        timestamp='2024-01-02 10:00:00')
        db.session.add(self.transaction1)
        db.session.add(self.transaction2)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_view_user_not_found(self):
        response = self.client.get(url_for('main.view_user', user_id=999))
        self.assert404(response)

    def test_view_user_with_transactions(self):
        response = self.client.get(url_for('main.view_user', user_id=self.user.id))
        self.assert200(response)
        self.assertTemplateUsed('user_details.html')
        self.assertIn(b'testuser', response.data)
        self.assertIn(b'-100', response.data)
        self.assertIn(b'200', response.data)

    def test_view_user_no_account(self):
        user_no_account = User(username='usernoaccount', email='noaccount@example.com')
        user_no_account.set_password('password')
        db.session.add(user_no_account)
        db.session.commit()

        response = self.client.get(url_for('main.view_user', user_id=user_no_account.id))
        self.assert200(response)
        self.assertTemplateUsed('user_details.html')
        self.assertIn(b'usernoaccount', response.data)
        self.assertNotIn(b'-100', response.data)
        self.assertNotIn(b'200', response.data)


if name == 'main':
    unittest.main()