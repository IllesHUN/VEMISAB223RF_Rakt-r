from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """Csak bejelentkezett felhasználó érheti el."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Kérjük, jelentkezz be!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """Csak megadott szerepkörű felhasználó érheti el."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Kérjük, jelentkezz be!', 'warning')
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('Nincs jogosultságod ehhez a művelethez!', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return role_required('admin')(f)


def raktaros_required(f):
    return role_required('raktaros', 'admin')(f)


def fuvarozo_required(f):
    return role_required('fuvarozo', 'admin')(f)


def beszallito_required(f):
    return role_required('beszallito', 'admin')(f)
