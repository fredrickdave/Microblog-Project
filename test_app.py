import os

os.environ["DATABASE_URL"] = "sqlite://"

import unittest
from datetime import datetime, timedelta

from app import create_app, db
from app.models import Post, User
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///"


class TestUserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username="susan")
        u.set_password("cat")
        self.assertFalse(u.check_password("dog"))
        self.assertTrue(u.check_password("cat"))

    def test_avatar(self):
        u = User(username="john", email="john@example.com")
        self.assertEqual(
            u.avatar(128), "https://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?d=retro&s=128"
        )

    def test_follow(self):
        u1 = User(username="john", email="john@example.com")
        u1.set_password("cat")
        u2 = User(username="susan", email="susan@example.com")
        u2.set_password("dog")
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, "susan")
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, "john")

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        # Create four users
        u1 = User(username="john", email="john@example.com")
        u1.set_password("cat")
        u2 = User(username="susan", email="susan@example.com")
        u2.set_password("dog")
        u3 = User(username="mary", email="mary@example.com")
        u3.set_password("bird")
        u4 = User(username="david", email="david@example.com")
        u4.set_password("snake")
        db.session.add_all([u1, u2, u3, u4])

        # Create four posts
        now = datetime.utcnow()
        p1 = Post(
            title="Title 1",
            subtitle="Subtitle 1",
            body="post from john",
            author=u1,
            timestamp=now + timedelta(seconds=1),
        )
        p2 = Post(
            title="Title 2",
            subtitle="Subtitle 2",
            body="post from susan",
            author=u2,
            timestamp=now + timedelta(seconds=4),
        )
        p3 = Post(
            title="Title 3",
            subtitle="Subtitle 3",
            body="post from mary",
            author=u3,
            timestamp=now + timedelta(seconds=3),
        )
        p4 = Post(
            title="Title 4",
            subtitle="Subtitle 4",
            body="post from david",
            author=u4,
            timestamp=now + timedelta(seconds=2),
        )
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # Setup the followers
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u3)  # susan follows mary
        u3.follow(u4)  # mary follows david
        db.session.commit()

        # Check the followed posts of each user
        # Note: Returned posts are sorted by latest time stamp
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])


if __name__ == "__main__":
    unittest.main(verbosity=2)
