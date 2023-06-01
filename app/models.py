from datetime import datetime
from hashlib import md5
from time import time

import jwt
from elasticsearch.exceptions import ConnectionError
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager
from app.search import add_to_index, query_index, remove_from_index


class SearchableMixin:
    @classmethod
    def search(cls, expression, page):
        ids, total = query_index(cls.__tablename__, expression)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = {}
        for i in range(len(ids)):
            when[ids[i]] = i
        return (
            cls.query.filter(cls.id.in_(ids))
            .order_by(db.case(when, value=cls.id))
            .paginate(page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False),
            total,
        )

    @classmethod
    def before_commit(cls, session):
        session._changes = {"add": list(session.new), "update": list(session.dirty), "delete": list(session.deleted)}

    @classmethod
    def after_commit(cls, session):
        try:
            for obj in session._changes["add"]:
                if isinstance(obj, SearchableMixin):
                    add_to_index(obj.__tablename__, obj)
            for obj in session._changes["update"]:
                if isinstance(obj, SearchableMixin):
                    add_to_index(obj.__tablename__, obj)
            for obj in session._changes["delete"]:
                if isinstance(obj, SearchableMixin):
                    remove_from_index(obj.__tablename__, obj)
            session._changes = None
        except ConnectionError:
            print(
                "Failed to establish a connection to Elasticsearch. Please make sure Elasticsearch service is running."
            )

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, "before_commit", SearchableMixin.before_commit)
db.event.listen(db.session, "after_commit", SearchableMixin.after_commit)

followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id")),
)


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    posts = db.relationship("Post", backref="author", lazy="dynamic")
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    def __repr__(self):
        return "<User {}>".format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=retro&s={size}"

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(
            followers.c.follower_id == self.id
        )
        # Add the current user to its own followed user, so user's own posts will be included in followed posts.
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in}, current_app.config["SECRET_KEY"], algorithm="HS256"
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])["reset_password"]
        except:
            return
        return User.query.get(id)


class Post(db.Model, SearchableMixin):
    __tablename__ = "post"
    __searchable__ = ["title", "subtitle", "body"]
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return "<Post {}>".format(self.body)


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
