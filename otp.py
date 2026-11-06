import secrets
import string


def genotp():
    """Return a cryptographically random 6-digit OTP."""
    return "".join(secrets.choice(string.digits) for _ in range(6))
