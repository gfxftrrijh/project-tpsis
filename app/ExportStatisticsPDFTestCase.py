import unittest
from flask import url_for
from flask_testing import TestCase
from pythonProject1 import create_app, db
from pythonProject1.models import User, Transaction
from io import BytesIO
from PyPDF2 import PdfFileReader

class ExportStatisticsPDFTestCase(TestCase):

    def create_app(self):
        app = create_app('testing')
        return app

    def setUp(self):
        db.create_all()
        self.user1 = User(username='user1', email='user1@example.com')
        self.user2 = User(username='user2', email='user2@example.com')
        db.session.add(self.user1)
        db.session.add(self.user2)
        db.session.commit()

        self.transaction1 = Transaction(account_id=1, amount=100, type='deposit')
        self.transaction2 = Transaction(account_id=1, amount=-50, type='withdrawal')
        self.transaction3 = Transaction(account_id=2, amount=200, type='deposit')
        db.session.add(self.transaction1)
        db.session.add(self.transaction2)
        db.session.add(self.transaction3)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_export_statistics_pdf(self):
        response = self.client.get(url_for('main.export_statistics_pdf'))
        self.assert200(response)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename=statistics_report.pdf', response.headers['Content-Disposition'])

        pdf = PdfFileReader(BytesIO(response.data))
        self.assertEqual(pdf.getNumPages(), 1)

        # Additional checks to verify PDF content if needed
        content = pdf.getPage(0).extract_text()
        self.assertIn('Statistics Report', content)
        self.assertIn('Total Users: 2', content)
        self.assertIn('Total Transactions: 3', content)
        self.assertIn('deposit: 2', content)
        self.assertIn('withdrawal: 1', content)

if name == 'main':
    unittest.main()