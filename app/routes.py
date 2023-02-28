from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.urls import url_parse

from app import app, db
from app.forms import EditProfileForm, LoginForm, RegistrationForm
from app.models import Post, User


@app.before_request
def before_request():
    if current_user.is_authenticated:
        # Only update user's last seen time if it's been over 10 seconds since its last update.
        # This also avoids database lock error due to multiple database commits when static assets are loaded
        # which are independent requests.
        time_difference = (datetime.utcnow() - current_user.last_seen).total_seconds()
        print("time_difference:", time_difference)
        if time_difference > 10:
            print("Time adjusted!")
            current_user.last_seen = datetime.utcnow()
            db.session.commit()


@app.route("/")
@app.route("/index")
@login_required
def index():
    posts = Post.query.all()
    return render_template("index.html", title="Home", posts=posts)


@app.route("/single-post")
def get_post():
    return render_template("single-post.html", title="Single Post")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("You're already logged in.")
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password. Please try again.")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        flash(f"Login requested for user {form.username.data}, remember_me={form.remember_me.data}")
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(next_page)

    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        flash("You're already logged in.")
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data.lower(), email=form.email.data.lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user! Enter your username and password to login.")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash("Successfully Logged out.")
    return redirect(url_for("index"))


@app.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    # print(user)
    posts = [
        {
            "author": user,
            "body": (
                "Test post #1 Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test"
                " post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test"
                " post #1"
            ),
        },
        {
            "author": user,
            "body": (
                "Test post #1 Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test"
                " post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test"
                " post #1"
            ),
        },
        {
            "author": user,
            "body": (
                "Test post #1 Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test"
                " post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test"
                " post #1"
            ),
        },
        {
            "author": user,
            "body": (
                "Test post #1 Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test"
                " post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test"
                " post #1"
            ),
        },
        {
            "author": user,
            "body": (
                "Test post #1 Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test"
                " post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test post #1Test"
                " post #1"
            ),
        },
        {"author": user, "body": "Test post #2"},
    ]
    return render_template("user.html", user=user, posts=posts)


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data.lower()
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for("edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title="Edit Profile", form=form)
