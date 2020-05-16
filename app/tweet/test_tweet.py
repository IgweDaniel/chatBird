import unittest
import json
from app import create_app
from app.models import User, db, Tweet
from unittest.mock import patch


class TweetRouteTestCase(unittest.TestCase):
    '''This class represents the Tweet Route test case'''

    @classmethod
    def setUpClass(cls):
        cls.app = create_app('app.config.TestingConfig')
        cls.client = cls.app.test_client
        cls.test_user = {
            'username': "testuser",
            'email': "testEmail",
            'password': "password"
        }
        cls.test_status = {
            'text': "Hi I am new Here",
        }

        with cls.app.app_context():
            db.create_all()
            u1 = User(email=cls.test_user['email'], password_hash=cls.test_user['password'],
                      username=cls.test_user['username'], verified=True)
            u1.insert()
        rv = cls.client().post('/user/auth', data=json.dumps(cls.test_user),
                               content_type='application/json')

        result_in_json = json.loads(rv.data.decode('utf-8').replace("'", "\""))
        cls.auth_token = result_in_json['data']['token']

    def test_api_can_create_a_status(self):
        '''Test API can create a Status'''
        rv = self.client().post(
            '/statuses/', data=json.dumps(self.test_status),
            content_type='application/json', headers={'x-access-token': self.auth_token})
        result_in_json = json.loads(rv.data.decode('utf-8').replace("'", "\""))
        self.assertEqual(rv.status_code, 201)
        self.assertIn('success', str(result_in_json['data']))
        with self.app.app_context():
            statuses = Tweet.query.all()
            self.assertEqual(len(statuses), 1)

    def test_api_can_reply_a_status(self):
        '''Test API can reply a Status'''
        with self.app.app_context():
            status = Tweet.query.all()[0]
        rv = self.client().post(
            '/statuses/reply', data=json.dumps({'id': status.id, 'text': 'Welcome, i hope you enjoy chatBird as much as i do chirp on'}),
            content_type='application/json', headers={'x-access-token': self.auth_token})
        result_in_json = json.loads(rv.data.decode('utf-8').replace("'", "\""))
        self.assertEqual(rv.status_code, 201)
        self.assertIn('success', str(result_in_json['data']))
        with self.app.app_context():
            replies = Tweet.query.filter_by(id=status.id).first().replies.all()
            self.assertEqual(len(replies), 1)
            self.assertEqual(
                replies[0].in_reply_to_status.text, self.test_status['text'])
            self.assertEqual(
                replies[0].in_reply_to_status.reply_count, 1)

    def test_api_get_a_status(self):
        '''Test API can return a single Status'''
        with self.app.app_context():
            status = Tweet.query.all()[0]
        rv = self.client().get(
            f'/statuses/{status.id}')
        result_in_json = json.loads(rv.data.decode('utf-8').replace("'", "\""))
        self.assertEqual(rv.status_code, 200)
        self.assertIn(status.text, str(result_in_json['data']))
        self.assertIn(f'{status.id}', str(result_in_json['data']))

    def test_api_get_status_replies(self):
        '''Test API can return a replies for a single Status'''
        text = 'it seems we are both test users hopefully we can get along pretty well...love ChatBird'
        with self.app.app_context():
            status = Tweet.query.all()[0]
            self.client().post(
                '/statuses/reply', data=json.dumps({'id': status.id, 'text': text}),
                content_type='application/json', headers={'x-access-token': self.auth_token})

            rv = self.client().get(
                f'/statuses/{status.id}/replies')
            result_in_json = json.loads(
                rv.data.decode('utf-8').replace("'", "\""))
            self.assertEqual(rv.status_code, 200)
            self.assertIn(text, str(result_in_json['data']))

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
