import unittest
from flask import url_for
from flask_testing import TestCase
from pythonProject1 import create_app, db
from pythonProject1.models import User, Transaction
from sqlalchemy import func
from datetime import datetime

class ViewStatisticsTestCase(TestCase):

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

        self.transaction1 = Transaction(account_id=1, amount=100, type='deposit', timestamp=datetime(2024, 1, 1, 10, 0))
        self.transaction2 = Transaction(account_id=1, amount=-50, type='withdrawal', timestamp=datetime(2024, 1, 2, 10, 0))
        self.transaction3 = Transaction(account_id=2, amount=200, type='deposit', timestamp=datetime(2024, 2, 1, 10, 0))
        db.session.add(self.transaction1)
        db.session.add(self.transaction2)
        db.session.add(self.transaction3)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_view_statistics(self):
        response = self.client.get(url_for('main.view_statistics'))
        self.assert200(response)
        self.assertTemplateUsed('statistics.html')

        total_users = User.query.count()
        total_transactions = Transaction.query.count()
        total_volume = db.session.query(func.sum(Transaction.amount)).scalar() or 0

        transactions_by_type = db.session.query(
            Transaction.type, func.count(Transaction.type)
        ).group_by(Transaction.type).all()

        transaction_dynamics = db.session.query(
            func.extract('year', Transaction.timestamp).label('year'),
            func.extract('month', Transaction.timestamp).label('month'),
            func.sum(Transaction.amount).label('total_amount')
        ).group_by('year', 'month').order_by('year', 'month').all()

        self.assertEqual(response.context['total_users'], total_users)
        self.assertEqual(response.context['total_transactions'], total_transactions)
        self.assertEqual(response.context['total_volume'], total_volume)

        transactions_by_type_context = [{'type': type_, 'count': count} for type_, count in transactions_by_type]
        self.assertEqual(response.context['transactions_by_type'], transactions_by_type_context)

        transaction_dynamics_context = [{'year': year, 'month': month, 'total_amount': total_amount} for year, month, total_amount
                                        in transaction_dynamics]
        self.assertEqual(response.context['transaction_dynamics'], transaction_dynamics_context)

if name == 'main':
    unittest.main()