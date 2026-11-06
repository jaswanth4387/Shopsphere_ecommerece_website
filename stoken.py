from flask import current_app
from itsdangerous import URLSafeTimedSerializer

SALT = "shopsphere-password-reset"


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def endata(data):
    """Sign `data` into a URL-safe token."""
    return _serializer().dumps(data, salt=SALT)


def dndata(token, max_age=900):
    """Return the data inside `token`; raises if it is invalid or older than max_age seconds."""
    return _serializer().loads(token, salt=SALT, max_age=max_age)
