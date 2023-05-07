from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import app, db
from app.main.forms import CreatePostForm, EditProfileForm, EmptyForm
from app.models import Post, User
from app.main import bp

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        # Only update user's last seen time if it's been over 10 seconds since its last update.
        # This also avoids database lock error due to multiple database commits when static assets are loaded
        # which are independent requests.
        time_difference = (datetime.utcnow() - current_user.last_seen).total_seconds()
        if time_difference > 10:
            current_user.last_seen = datetime.utcnow()
            db.session.commit()


@bp.route("/")
@bp.route("/index")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    posts = current_user.followed_posts().paginate(page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    return render_template("index.html", title="Home", posts=posts, route="main.index")


@bp.route("/explore")
@login_required
def explore():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False
    )
    return render_template("index.html", title="Explore", posts=posts, route="main.explore")


@bp.route("/single-post")
def get_post():
    return render_template("single-post.html", title="Single Post")


@bp.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False
    )
    form = EmptyForm()
    return render_template("user.html", user=user, posts=posts, form=form, route="main.user")


@bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data.lower()
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for("main.edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title="Edit Profile", form=form)


@bp.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {} not found.".format(username))
            return redirect(url_for("main.index"))
        if user == current_user:
            flash("You cannot follow yourself!")
            return redirect(url_for("user", username=username))
        current_user.follow(user)
        db.session.commit()
        flash("You are following {}!".format(username))
        return redirect(url_for("main.user", username=username))
    else:
        return redirect(url_for("main.index"))


@bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {} not found.".format(username))
            return redirect(url_for("main.index"))
        if user == current_user:
            flash("You cannot unfollow yourself!")
            return redirect(url_for("main.user", username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash("You are not following {}.".format(username))
        return redirect(url_for("main.user", username=username))
    else:
        return redirect(url_for("main.index"))


@bp.route("/new_post", methods=["GET", "POST"])
def new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, subtitle=form.subtitle.data, body=form.body.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post is now live!")
        return redirect(url_for("main.index"))
    return render_template("make_post.html", form=form)
