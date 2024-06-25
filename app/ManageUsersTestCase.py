import unittest
from flask import url_for, request
from flask_testing import TestCase
from pythonProject1 import create_app, db
from pythonProject1.models import User

class ManageUsersTestCase(TestCase):

    def create_app(self):
        app = create_app('testing')
        return app

    def setUp(self):
        db.create_all()
        self.user1 = User(username='user1', email='user1@example.com', is_admin=True)
        self.user2 = User(username='user2', email='user2@example.com', is_admin=False)
        self.user3 = User(username='adminuser', email='admin@example.com', is_admin=True)
        db.session.add(self.user1)
        db.session.add(self.user2)
        db.session.add(self.user3)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_manage_users_no_filters(self):
        response = self.client.get(url_for('main.manage_users'))
        self.assert200(response)
        self.assertTemplateUsed('manage_users.html')
        self.assertIn(b'user1', response.data)
        self.assertIn(b'user2', response.data)
        self.assertIn(b'adminuser', response.data)

    def test_manage_users_filter_by_username(self):
        response = self.client.get(url_for('main.manage_users', filter='user'))
        self.assert200(response)
        self.assertTemplateUsed('manage_users.html')
        self.assertIn(b'user1', response.data)
        self.assertIn(b'user2', response.data)
        self.assertNotIn(b'adminuser', response.data)

    def test_manage_users_filter_by_admin_status(self):
        response = self.client.get(url_for('main.manage_users', is_admin='1'))
        self.assert200(response)
        self.assertTemplateUsed('manage_users.html')
        self.assertIn(b'user1', response.data)
        self.assertNotIn(b'user2', response.data)
        self.assertIn(b'adminuser', response.data)

    def test_manage_users_sort_by_username_asc(self):
        response = self.client.get(url_for('main.manage_users', sort='name_asc'))
        self.assert200(response)
        self.assertTemplateUsed('manage_users.html')
        users = response.context['users']
        self.assertEqual(users[0].username, 'adminuser')
        self.assertEqual(users[1].username, 'user1')
        self.assertEqual(users[2].username, 'user2')

    def test_manage_users_sort_by_username_desc(self):
        response = self.client.get(url_for('main.manage_users', sort='name_desc'))
        self.assert200(response)
        self.assertTemplateUsed('manage_users.html')
        users = response.context['users']
        self.assertEqual(users[0].username, 'user2')
        self.assertEqual(users[1].username, 'user1')
        self.assertEqual(users[2].username, 'adminuser')

if name == 'main':
    unittest.main()