import datetime
import time
from server.trackable import Trackable, create_trackable_from_row
from flask import (
    Blueprint, jsonify, request, session
)

from server.db import get_db

bp = Blueprint('api', __name__, url_prefix='/api')
date_format = '%Y-%m-%d'


def get_user_by_api_key(request):
    db = get_db()
    api_key = request.json.get('api_key')
    user = db.execute("SELECT * FROM user WHERE api_key=?",
                      (api_key,)).fetchone()
    if user is None:
        return None
    return user['id']


@bp.route('/trackable-item', methods=['GET', 'POST'])
def get_tracked_items():
    db = get_db()

    if request.method == 'POST':
        user_id = get_user_by_api_key(request)
        if user_id is None:
            return jsonify({"data": []})
    else:
        user_id = session.get('user_id')

    tracked_items = db.execute(
        "SELECT * FROM tracked_items WHERE owner_id=?", (user_id,)).fetchall()

    results = []
    for t in tracked_items:
        item = create_trackable_from_row(t).to_json()
        results.append(item)

    return jsonify(results)


@bp.route('/trackable-item', methods=['PUT'])
def create_trackable_item():
    db = get_db()
    cursor = db.cursor()
    user_id = get_user_by_api_key(request)

    if not request.is_json:
        return jsonify({"message": "Content type is not supported."}), 415

    data = request.json
    name = data.get('name')
    type = data.get('type')

    cursor.execute(
        "INSERT INTO tracked_items (owner_id, name, type) VALUES (?, ?, ?)",
        (user_id, name, type))
    db.commit()
    return jsonify({"id": cursor.lastrowid})


@bp.route('/trackable-item', methods=['DELETE'])
def delete_trackable_item():
    db = get_db()
    user_id = session.get('user_id')

    data = request.json
    id = data.get('id')

    if not request.is_json:
        return jsonify({"message": "Content type is not supported."}), 415

    deleted_item = db.execute(
        "DELETE FROM tracked_items WHERE id = ? AND owner_id = ?", (id, user_id))
    db.commit()
    return jsonify(deleted_item)


@staticmethod
def validate_date(date, param):
    try:
        if date is not None:
            datetime.datetime.strptime(date, date_format)
    except ValueError:
        return jsonify(
            {"message":
             (f"You provided invalid an invallid date for {param}."
              f"Valid dates follow the format \"YYYY-MM-DD\"")}), 400


@bp.route('/history', methods=['GET', 'POST'])
def get_tracking_history():
    args = request.args
    day = args.get('day')
    start_date = args.get('start_date')
    end_date = args.get('end_date')
    tracked_item = args.get('tracked_item')

    if day and start_date or day and end_date:
        return jsonify({"message": "Query either by day, or start and end dates, not both."}), 400

    errors = []
    day_error = validate_date(day, "day")
    if day_error is not None:
        errors.append(day_error)
    start_date_error = validate_date(start_date, "start_date")
    if start_date_error is not None:
        errors.append(start_date_error)
    end_date_error = validate_date(end_date, "end_date")
    if end_date_error is not None:
        errors.append(end_date_error)
    if len(errors) > 0:
        return jsonify(errors)

    if day is not None:
        day = time.mktime(datetime.datetime.strptime(
            day, date_format).timetuple())
    if start_date is not None:
        start_date = time.mktime(datetime.datetime.strptime(
            start_date, date_format).timetuple())
    if end_date is not None:
        end_date = time.mktime(datetime.datetime.strptime(
            end_date, date_format).timetuple())

    db = get_db()
    if request.method == 'POST':
        user_id = get_user_by_api_key(request)
        if user_id is None:
            return jsonify({"data": []})
    else:
        user_id = session.get('user_id')

    entries = db.execute(
        (f"SELECT * FROM entries WHERE owner_id={user_id} "
         f"{'AND item=' + tracked_item if tracked_item is not None else ''}"
         f"{'AND date=' + str(day) if day is not None else ''}"
         f"{'AND date>' + str(start_date) if start_date is not None else ''}"
         f"{'AND date<' + str(end_date) if end_date is not None else ''}"
         )).fetchall()
    return jsonify(entries)


@bp.route('/history', methods=['DELETE'])
def delete_history():
    args = request.args
    day = args.get('day')
    id = args.get('id')
    tracked_item = args.get('tracked_item')

    db = get_db()
    user_id = session.get('user_id')

    if day is not None:
        day = time.mktime(datetime.datetime.strptime(
            day, date_format).timetuple())

    error = validate_date(day, "day")
    if error is not None:
        return jsonify(error)

    if day is not None:
        entries = db.execute(
            "DELETE FROM entries WHERE owner_id=? AND date=?", (user_id, day,)).fetchall()
        return jsonify(entries)

    if id is not None:
        entries = db.execute(
            "DELETE FROM entries WHERE owner_id=? AND id=?", (user_id, id,)).fetchone()
        return jsonify(entries)

    if tracked_item is not None:
        entries = db.execute(
            "DELETE FROM entries WHERE owner_id=? AND item=?", (user_id, tracked_item,)).fetchone()
        return jsonify(entries)


# Make sure to overwrite existing entry if one exists
@bp.route('/history', methods=['PUT'])
def track_item():
    data = request.json
    item = data.get('item')
    value = data.get('value')
    day = data.get('day')

    day_error = validate_date(day, "day")
    if day_error is not None:
        return jsonify(day_error)

    db = get_db()
    cursor = db.cursor()

    user_id = get_user_by_api_key(request)
    if user_id is None:
        return jsonify({"data": []})

    trackable_row = db.execute(
        "SELECT * FROM tracked_items WHERE id=? AND owner_id=?", (item, user_id,)).fetchone()
    trackable = create_trackable_from_row(trackable_row)

    if not trackable.validate_value(value):
        return jsonify({"message": f"The value you provided ({value}) was invalid for type {trackable.type}"})

    day = time.mktime(datetime.datetime.strptime(
        day, date_format).timetuple())

    existing_entry = db.execute(
        "SELECT * FROM entries WHERE date=?", (day,)).fetchone()
    if existing_entry is not None:
        id_of_existing_entry = existing_entry['id']
        return jsonify(id_of_existing_entry)
        db.execute("DELETE FROM entries WHERE id=?", (id_of_existing_entry))

    cursor.execute("INSERT INTO entries (value, item, date, owner_id) VALUES (?, ?, ?, ?)",
                   (value, trackable.id, day, user_id))

    db.commit()

    return jsonify({"id": cursor.lastrowid})
