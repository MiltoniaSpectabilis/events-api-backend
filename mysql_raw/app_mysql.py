#!/usr/bin/env python3
"""
RESTful API for managing events using Flask and MySQL (Raw).
"""

from os import getenv
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['MYSQL_HOST'] = getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = getenv('MYSQL_DB')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


@app.route("/", strict_slashes=False)
def index():
    """Tests database connection"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT DATABASE();")
        result = cursor.fetchone()
        cursor.close()
        return f"Database connection successful! Test query result: {result}"
    except Exception as e:
        return f"Database connection failed: {e}"


@app.route("/events", methods=['POST'], strict_slashes=False)
def create_event():
    """Creates event"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON or no data provided"}), 400
        if not all(
            key in data for key in [
                'title',
                'description',
                'event_date',
                'location'
            ]
        ):
            return jsonify(
                {"error": "Missing required event fields (title, "
                    "description, event_date, location)"}
            ), 400

        title = data.get('title')
        description = data.get('description')
        event_date = data.get('event_date')
        location = data.get('location')

        cursor = mysql.connection.cursor()

        insert_query = """
        INSERT INTO events (title, description, event_date, location)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(
            insert_query, (title, description, event_date, location)
        )
        mysql.connection.commit()
        new_event_id = cursor.lastrowid
        cursor.close()

        return jsonify({
            "message": "Event created successfully",
            "event_id": new_event_id,
            "event": {
                "title": title,
                "description": description,
                "event_date": event_date,
                "location": location
            }
        }), 201
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"error": f"An error occured: {e}"}), 500


@app.route("/events", methods=['GET'], strict_slashes=False)
def get_all_events():
    """Gets all events"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM events")
        events = cursor.fetchall()
        cursor.close()
        return jsonify({"events": events}), 200
    except Exception as e:
        return jsonify({"error": f"An error occured: {e}"}), 500


@app.route("/events/<int:event_id>", methods=['GET'], strict_slashes=False)
def get_single_event(event_id):
    """Gets single event"""
    try:
        cursor = mysql.connection.cursor()
        select_query = "SELECT * FROM events WHERE id = %s"
        # I should not forget to add ',' after 'event_id'
        # so it is treated as a tuple
        cursor.execute(select_query, (event_id,))
        event = cursor.fetchone()
        cursor.close()
        if not event:
            return jsonify({"message": "Event not found"}), 404
        else:
            return jsonify({"event": event}), 200
    except Exception as e:
        return jsonify({"error": f"An error occured: {e}"}), 500


@app.route("/events/<int:event_id>", methods=['PUT'], strict_slashes=False)
def update_event(event_id):
    """Updates event"""
    try:
        # check if event exists
        cursor = mysql.connection.cursor()
        select_query = "SELECT * FROM events WHERE id = %s"
        cursor.execute(select_query, (event_id,))
        event_to_update = cursor.fetchone()
        if not event_to_update:
            cursor.close()
            return jsonify({"message": "Event not found"}), 404
        # check if data is valid
        data = request.get_json()
        if not data:
            cursor.close()
            return jsonify({"error": "Invalid JSON or data not provided"}), 400
        title = data.get('title', event_to_update['title'])
        description = data.get('description', event_to_update['description'])
        event_date = data.get('event_date', event_to_update['event_date']
                              .strftime('%Y-%m-%d %H:%M:%S'))
        location = data.get('location', event_to_update['location'])
        update_query = """
        UPDATE events
        SET title = %s, description = %s, event_date = %s, location = %s
        WHERE id = %s;
        """
        cursor.execute(
            update_query, (title, description, event_date, location, event_id)
        )
        cursor.connection.commit()
        # check for affected rows
        if cursor.rowcount == 0:
            return jsonify({
                "message": (
                    "No changes made to event or event not "
                    "found after initial check"
                )
            }), 200
        cursor.close()
        return jsonify({
            "message": "Event updated successfully",
            "event_id": event_id,
            "updated_event": {
                "title": title,
                "description": description,
                "event_date": event_date,
                "location": location
            }
        }), 200
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"error": f"An error occured: {e}"}), 500


@app.route("/events/<int:event_id>", methods=['DELETE'], strict_slashes=False)
def delete_event(event_id):
    """Deletes event"""
    try:
        # we should always check if the event exists first
        cursor = mysql.connection.cursor()
        # using alias here to make it easier to fetch value from key.
        # it's better/more efficient to use EXISTS here
        # since our goal is just to check whether or not an event (row) exists
        select_query = """
            SELECT EXISTS (SELECT 1 FROM events WHERE id = %s)
            AS event_to_delete
            """
        cursor.execute(select_query, (event_id,))
        result_dict = cursor.fetchone()
        event_to_delete = result_dict.get('event_to_delete')
        if not event_to_delete:
            cursor.close()
            return jsonify({"message": "Event not found"}), 404
        # now for the deletion process
        delete_query = "DELETE FROM events WHERE id = %s"
        cursor.execute(delete_query, (event_id,))
        cursor.connection.commit()
        cursor.close()
        return jsonify({"message": "Event deleted successfully"}), 200
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"error": f"An error occured: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
