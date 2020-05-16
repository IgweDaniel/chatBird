import unittest
import json
from app import create_app
from app.models import User, db, Token
from unittest.mock import patch
from app.utils import mail, generate_token
from flask_mail import email_dispatched


class UserRouteTestCase(unittest.TestCase):
    """This class represents the User Route test case"""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app('app.config.TestingConfig')
        cls.client = cls.app.test_client
        cls.test_users = [{
            'username': "testuser",
            'email': "testEmail",
            'password': "password"
        }, {
            'username': "testuser2",
            'email': "testEmail2",
            'password': "password2"
        }]
        with cls.app.app_context():
            db.create_all()
            u1 = User(email=cls.test_users[0]['email'], password_hash=cls.test_users[0]['password'],
                      username=cls.test_users[0]['username'], verified=True)
            u1.insert()

    def test_api_can_create_user(self):
        """Test API can create a new User"""
        new_user = {
            'username': "jonnyDepp",
            'email': "johnny@Email",
            'password': "password"
        }
        rv = self.client().post('/user/create', data=json.dumps(new_user),
                                content_type='application/json')

        result_in_json = json.loads(rv.data.decode('utf-8').replace("'", "\""))

        self.assertEqual(rv.status_code, 201)
        self.assertIn('success', str(result_in_json['data']))
        with self.app.app_context():
            user = User.query.filter_by(email=new_user['email']).first()
            self.assertIsNotNone(user)

    def test_api_can_verify_user(self):
        """Test API can verify a new User"""
        new_user = {
            'username': "testy2",
            'email': "testy2@Email",
            'password': "password"
        }
        self.client().post('/user/create', data=json.dumps(new_user),
                           content_type='application/json')

        with self.app.app_context():
            user = User.query.filter_by(email=new_user['email']).first()
            code = Token.query.filter_by(user_id=user.id).first()

        rv = self.client().post('/user/verify', data=json.dumps({'code': code.code, 'email': user.email}),
                                content_type='application/json')

        result_in_json = json.loads(rv.data.decode('utf-8').replace("'", "\""))

        self.assertEqual(rv.status_code, 200)
        self.assertIsNotNone(result_in_json['data'])
        self.assertIn('token', str(result_in_json['data']))

    def test_api_can_authenticate_user(self):
        """Test API can authenticate a User"""
        rv = self.client().post('/user/auth', data=json.dumps(self.test_users[0]),
                                content_type='application/json')

        result_in_json = json.loads(rv.data.decode('utf-8').replace("'", "\""))

        self.assertEqual(rv.status_code, 200)
        self.assertIsNotNone(result_in_json['data'])
        self.assertIn('token', str(result_in_json['data']))

    def test_api_can_return_all_users(self):
        """Test API can return all  Users"""
        rv = self.client().get('/user/index')
        result_in_json = json.loads(rv.data.decode('utf-8').replace("'", "\""))
        self.assertEqual(rv.status_code, 200)
        self.assertIn(self.test_users[0]['email'], str(result_in_json['data']))

    def test_api_can_return_a_user(self):
        """Test API can return a User"""
        with self.app.app_context():
            user = User.query.filter_by(
                email=self.test_users[0]['email']).first()

            rv = self.client().get(f'/user/{user.id}')
            result_in_json = json.loads(
                rv.data.decode('utf-8').replace("'", "\""))
            self.assertEqual(rv.status_code, 200)
            self.assertIn(self.test_users[0]['email'], str(
                result_in_json['data']))

    def test_api_can_reset_user_password(self):
        """Test API can return  reset_ Users"""
        rv1 = self.client().post('/user/forgot_password', data=json.dumps({'email': self.test_users[0]['email']}),
                                 content_type='application/json')

        self.assertEqual(rv1.status_code, 200)
        with self.app.app_context():
            user = User.query.filter_by(
                email=self.test_users[0]['email']).first()
            token = generate_token({'id': user.id})
            rv = self.client().post(f'/user/reset_password/{token}', data=json.dumps({'password': 'mama'}),
                                    content_type='application/json')
            self.assertEqual(rv.status_code, 200)

    def test_api_can_create_friendships(self):
        """Test API can return  reset_ Users"""
        with self.app.app_context():
            u = User(email=self.test_users[1]['email'], password_hash=self.test_users[1]['password'],
                     username=self.test_users[1]['username'], verified=True)
            u.insert()
            rv = self.client().post('/user/auth', data=json.dumps(self.test_users[0]),
                                    content_type='application/json')

            result_in_json = json.loads(
                rv.data.decode('utf-8').replace("'", "\""))

            rv = self.client().post('/user/friendships/create', data=json.dumps({'id': u.id}),
                                    content_type='application/json', headers={'x-access-token': result_in_json['data']['token']})

            result_in_json = json.loads(
                rv.data.decode('utf-8').replace("'", "\""))
            self.assertIn("success", str(result_in_json['data']))
            user = User.query.filter_by(
                email=self.test_users[0]['email']).first()
            self.assertTrue(user.is_following(u))

    def test_api_can_delete_friendships(self):
        """Test API can return  reset_ Users"""
        with self.app.app_context():
            u = User.query.filter_by(email=self.test_users[1]['email']).first()
            rv = self.client().post('/user/auth', data=json.dumps(self.test_users[0]),
                                    content_type='application/json')

            result_in_json = json.loads(
                rv.data.decode('utf-8').replace("'", "\""))

            rv = self.client().post('/user/friendships/delete', data=json.dumps({'id': u.id}),
                                    content_type='application/json', headers={'x-access-token': result_in_json['data']['token']})

            result_in_json = json.loads(
                rv.data.decode('utf-8').replace("'", "\""))
            self.assertIn("success", str(result_in_json['data']))
            user = User.query.filter_by(
                email=self.test_users[0]['email']).first()
            self.assertFalse(user.is_following(u))

    @classmethod
    def tearDownClass(cls):
        """teardown all initialized variables."""
        with cls.app.app_context():
            # drop all tables
            db.session.remove()
            db.drop_all()

    def tearDown(self):
        pass


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
