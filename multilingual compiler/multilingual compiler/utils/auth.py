from functools import wraps
from flask import session, redirect, url_for, flash, jsonify, request
from database.db import get_db_connection

def login_user_session(user):
    """Sets session context for logged-in user."""
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['email'] = user['email']
    session['role'] = user['role']

def logout_user_session():
    """Clears current session."""
    session.clear()

def get_current_user():
    """Returns current user record from database if logged in."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT id, username, email, role, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Decorator to enforce role-based access control."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({"error": "Authentication required"}), 401
                return redirect(url_for('login_page'))
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                if request.path.startswith('/api/'):
                    return jsonify({"error": "Access denied: Unauthorized role"}), 403
                flash("Access denied: You do not have permission to view this page.", "danger")
                return redirect(url_for('dashboard_router'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
