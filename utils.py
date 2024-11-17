from flask import session, abort
from functools import wraps

def membership_required(level):
    def decorator(f):
        @wraps(f)
        def wrapped_function(*args, **kwargs):
            user_membership = session.get('membership', 'Gratis')
            if user_membership != level and session.get('user_role') != 1:  # Admin siempre tiene acceso
                abort(403)  # Prohibido
            return f(*args, **kwargs)
        return wrapped_function
    return decorator
