from app import create_app, db
from app.auth import email
from app.models import Post, User

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Post": Post}
