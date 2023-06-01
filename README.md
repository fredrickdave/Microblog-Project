# Microblog Project

This is a simple microblogging site built with Flask, SQLAlchemy, Bootstrap and Jinja2. It allows users to create an account, write posts, follow other users, and see their posts on a timeline.

## Features

- User authentication and profile management
- Post creation, deletion, and editing
- User following and unfollowing
- Timeline of posts from followed users
- Pagination of posts
- Full-text search of posts
- Email notifications for password reset

## Installation

To run this project locally, you need to have Python 3.6 or higher and pip installed.

1. Clone this repository: `git clone https://github.com/fredrickdave/Microblog-Project.git`
2. Change directory to the project folder: `cd Microblog-Project`
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
5. Install the required dependencies: `pip install -r requirements.txt`
6. Set the environment variables:
    - `FLASK_APP=main.py`
    - `FLASK_ENV=development`
    - `SENDGRID_API_KEY=<your-SENDGRID-API-KEY>`
    - `SECRET_KEY=<a-random-string>`
7. Initialize the database: `flask db upgrade`
8. Run the application: `flask run`
9. Open your browser and go to http://localhost:5000

## Live Demo Link
The app is hosted on a free instance on Render, so please allow a minute or two for the web app to initially load when you open the Live Demo link. 

Link: https://microblog-app-z6vu.onrender.com/