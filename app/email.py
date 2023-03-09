import sendgrid
from flask import render_template
from sendgrid.helpers.mail import Content, Email, Mail, To

from app import app


def send_email(user):
    sg = sendgrid.SendGridAPIClient(api_key=app.config["SENDGRID_API_KEY"])
    from_email = Email(app.config["ADMINS"])
    to_email = To("fredrick_dave@outlook.com")
    subject = "[Microblog] Reset Your Password"
    # content = Content("text/plain", "and easy to do anywhere, even with Python")
    content = Content("text/html", render_template("reset_password.html", user=user))
    mail = Mail(from_email, to_email, subject, content)

    # Get a JSON-ready representation of the Mail object
    mail_json = mail.get()

    # Send an HTTP POST request to /mail/send
    response = sg.client.mail.send.post(request_body=mail_json)
    print(response.status_code)
    print(response.headers)
