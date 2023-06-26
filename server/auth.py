import secrets
from flask import (
    Blueprint, g, jsonify, request, session
)
from werkzeug.security import check_password_hash, generate_password_hash

from server.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['POST'])
def register():
    if not request.is_json:
        return jsonify({"message": "Content type is not supported."}), 415

    data = request.json
    username = data.get('username')
    password = data.get('password')
    db = get_db()

    if not username:
        return jsonify({"message": "A username is required"}), 403
    elif not password:
        return jsonify({"message": "A password is required."}), 503

    try:
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        db.commit()
        return jsonify({"message": f"User {username} is now registered."})
    except db.IntegrityError:
        return jsonify({"message": f"User {username} is already registered."}), 500


@bp.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"message": "Content type is not supported."}), 415

    data = request.json
    username = data.get('username')
    password = data.get('password')
    key = data.get('api_key')
    db = get_db()

    if key is not None:
        user = db.execute(
            "SELECT * FROM user WHERE api_key = ?", (key,)).fetchone()
    else:
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            return jsonify({"message": "Invalid credentials"}), 401
        elif not check_password_hash(user['password'], password):
            return jsonify({"message": "Invalid credentials"}), 401

    session.clear()
    session['user_id'] = user['id']
    return jsonify({"message": f"User {username} is now logged in."})


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    user_id = session.get('user_id')

    db = get_db()
    user = db.execute(
        'SELECT * FROM user WHERE id = ?', (user_id,)
    ).fetchone()
    username = user.username

    session.clear()
    return jsonify({"message": f"User {username} is now logged out."})


@bp.route('generate-key', methods=['POST'])
def generate_key():
    if not request.is_json:
        return jsonify({"message": "Content type is not supported."}), 415

    data = request.json
    username = data.get('username')
    password = data.get('password')
    db = get_db()

    user = db.execute(
       'SELECT * FROM user WHERE username = ?', (username,)
       ).fetchone()

    if user is None:
        return jsonify({"message": "Invalid credentials"}), 401
    elif not check_password_hash(user['password'], password):
        return jsonify({"message": "Invalid credentials"}), 401

    api_key = secrets.token_urlsafe(16)
    db.execute("UPDATE user SET api_key = ? WHERE id = ?", (api_key, user['id']))
    db.commit()

    return jsonify({
        "key": api_key
    })
