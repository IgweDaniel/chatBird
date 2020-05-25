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
            'username': "John Doe",
            'email': "testEmail@ymail.com",
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
                replies[0].in_reply_to_status.replies.count(), 1)

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

    def test_api_get_followed_statuses_of_a_user(self):
        '''Test API can return a user followed statuses'''
        text = "Hello World"
        user = {"email": "testuser2@email.com", "password": "password",
                'username': 'testuser2', }
        with self.app.app_context():
            u = User(email=user['email'], password_hash=user['password'],
                     username=user['username'], verified=True)
            u.insert()
            s = Tweet(text=text, user=u)
            current_user = User.query.filter_by(
                email=self.test_user['email']).first()
            current_user.follow(u)
            db.session.commit()
        rv = self.client().get(
            '/statuses/home_timeline', headers={'x-access-token': self.auth_token})

        result_in_json = json.loads(
            rv.data.decode('utf-8').replace("'", "\""))
        self.assertEqual(rv.status_code, 200)
        self.assertIn(text, str(result_in_json['data']))
        self.assertIn(user['username'], str(result_in_json['data']))

    def test_api_like_a_status(self):
        tweet_id = 1
        '''Test API can like a status'''
        rv = self.client().post(
            f'/statuses/like/{tweet_id}', headers={'x-access-token': self.auth_token})

        result_in_json = json.loads(
            rv.data.decode('utf-8').replace("'", "\""))
        with self.app.app_context():
            tweet = Tweet.query.filter_by(id=tweet_id).first()
            self.assertEqual(tweet.favorites.count(), 1)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("success", str(result_in_json['data']))

    def test_api_unlike_a_status(self):
        tweet_id = 1
        '''Test API can unlike a status'''
        rv = self.client().post(
            f'/statuses/unlike/{tweet_id}', headers={'x-access-token': self.auth_token})

        result_in_json = json.loads(
            rv.data.decode('utf-8').replace("'", "\""))
        with self.app.app_context():
            tweet = Tweet.query.filter_by(id=tweet_id).first()
            self.assertEqual(tweet.favorites.count(), 0)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("success", str(result_in_json['data']))

    def test_api_can_return_favorite_status(self):
        '''Test API can unlike a status'''
        with self.app.app_context():
            tweet = Tweet.query.filter_by(id=1).first()
            self.client().post(
                f'/statuses/like/{tweet.id}', headers={'x-access-token': self.auth_token})
            rv = self.client().get(
                f'/statuses/favorites', headers={'x-access-token': self.auth_token})

            result_in_json = json.loads(
                rv.data.decode('utf-8').replace("'", "\""))
            self.assertEqual(rv.status_code, 200)
            self.assertIn(tweet.text, str(result_in_json['data']))

    def test_api_can_retweet_a_status(self):
        '''Test API can retweet a Status'''
        status_to_retweet = {'text': "Hahaha retweet this i dare you"}
        user = {
            'username': "Jane Doe",
            'email': "Janey@ymail.com",
            'password': "password"
        }
        with self.app.app_context():
            u = User(email=user['email'], password_hash=user['password'],
                     username=user['username'], verified=True)
            u.insert()
            s = Tweet(text=status_to_retweet['text'], user=u)
            s.insert()

            rv = self.client().post(
                '/statuses/retweet', data=json.dumps({'id': s.id}),
                content_type='application/json', headers={'x-access-token': self.auth_token})
            result_in_json = json.loads(
                rv.data.decode('utf-8').replace("'", "\""))
            self.assertEqual(rv.status_code, 201)
            self.assertIn('success', str(result_in_json['data']))
            self.client().post(
                '/statuses/reply', data=json.dumps({'id': s.id, 'text': 'Hahaha now am gonna also reply'}),
                content_type='application/json', headers={'x-access-token': self.auth_token})

    @classmethod
    def tearDownClass(cls):
        """teardown all initialized variables."""
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def tearDown(self):
        pass


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
