from datetime import datetime

from flask import current_app, flash, g, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.main import bp
from app.main.forms import CreatePostForm, EditProfileForm, EmptyForm, SearchForm
from app.models import Post, User


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
        g.search_form = SearchForm()


@bp.route("/")
@bp.route("/index")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    return render_template("index.html", title="Home", posts=posts, route="main.index")


@bp.route("/explore")
@login_required
def explore():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    return render_template("index.html", title="Explore", posts=posts, route="main.explore")


@bp.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    form = EmptyForm()
    return render_template(
        "user.html", title=f"Profile: {user.username}", user=user, posts=posts, form=form, route="main.user"
    )


@bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data.lower()
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for("main.user", username=current_user.username))
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
        flash(f"You are now following {username}.")
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
            flash(f"User {username} not found.")
            return redirect(url_for("main.index"))
        if user == current_user:
            flash("You cannot unfollow yourself!")
            return redirect(url_for("main.user", username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f"You've unfollowed {username}.")
        return redirect(url_for("main.user", username=username))
    else:
        return redirect(url_for("main.index"))


@bp.route("/new_post", methods=["GET", "POST"])
@login_required
def new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, subtitle=form.subtitle.data, body=form.body.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post is now live!")
        return redirect(url_for("main.index"))
    return render_template("make_post.html", form=form, title="New Post")


@bp.route("/post/<int:post_id>", methods=["GET", "POST"])
@login_required
def show_post(post_id):
    post = Post.query.get(post_id)
    return render_template("single_post.html", post=post, title=post.title)


@bp.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get(post_id)
    if current_user.id != post.user_id:
        flash("Sorry, you don't have permission to edit this post. Please only edit posts you made.")
        return redirect(url_for("main.index", post_id=post.id))
    form = CreatePostForm(title=post.title, subtitle=post.subtitle, body=post.body)
    if form.validate_on_submit():
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.body = form.body.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for("main.show_post", post_id=post.id))
    return render_template("make_post.html", form=form, is_edit=True, title="Edit Post")


@bp.route("/delete/<int:post_id>")
@login_required
def delete_post(post_id):
    post = Post.query.get(post_id)
    if current_user.id != post.user_id:
        flash("Sorry, you don't have permission to delete this post. Please only edit posts you made.")
        return redirect(url_for("main.index", post_id=post.id))
    db.session.delete(post)
    db.session.commit()
    flash("Post has been deleted.")
    return redirect(url_for("main.index"))


@bp.route("/search")
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for("main.explore"))
    page = request.args.get("page", 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page)
    return render_template("search.html", title="Search", route="main.search", posts=posts, total=total)


@bp.route("/about")
@login_required
def about():
    return render_template("about.html", title="About Microblog")
