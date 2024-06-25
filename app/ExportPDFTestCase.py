import unittest
from flask import url_for
from flask_testing import TestCase
from pythonProject1 import create_app, db
from pythonProject1.models import User, BankAccount, Transaction
from flask_login import login_user
import io

class ExportPDFTestCase(TestCase):

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

    def test_export_pdf_not_authenticated(self):
        response = self.client.get(url_for('main.export_pdf'))
        self.assertRedirects(response, url_for('main.login'))

    def test_export_pdf_no_account(self):
        self.login()
        db.session.delete(self.account)
        db.session.commit()
        response = self.client.get(url_for('main.export_pdf'))
        self.assertRedirects(response, url_for('main.user_dashboard'))
        self.assertIn(b'No bank account found.', response.data)

    def test_export_pdf_success(self):
        self.login()
        response = self.client.get(url_for('main.export_pdf'))
        self.assert200(response)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename=transactions.pdf', response.headers['Content-Disposition'])
        # Further checks on PDF content could be added here if needed

if name == 'main':
    unittest.main()