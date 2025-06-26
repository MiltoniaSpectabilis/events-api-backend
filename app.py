#!/usr/bin/env python3
"""
RESTful API for managing events using Flask and MySQL (SQLAlchemy).
"""

from os import getenv
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from datetime import datetime
from database import db
from models.events import Event

load_dotenv()

app = Flask(__name__)

# configure sqlalchemy using the uri from .env
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('SQLALCHEMY_DATABASE_URI')
# disable tracking for performance
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = getenv(
    'SQLALCHEMY_TRACK_MODIFICATIONS'
)

db.init_app(app)


@app.route("/", strict_slashes=False)
def index():
    return "Flask Event Management System API with SQLAlchemy running!"


@app.route("/events", methods=['POST'], strict_slashes=False)
def create_event():
    """Creates event"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON or no data provided"}), 400
        required_fields = ['title', 'description', 'event_date', 'location']
        if not all(field in data for field in required_fields):
            return jsonify({"error": f"Missing required fields: {', '.join(
                f for f in required_fields if f not in data)}"}), 400
        # parse event_date string into a datetime object
        try:
            event_date = datetime.strptime(
                data['event_date'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify(
                {"error": "Invalid event_date format. Use YYYY-MM-DD HH:MM:SS"}
            ), 400

        new_event = Event(
            title=data['title'],
            description=data['description'],
            event_date=event_date,
            location=data['location']

        )

        db.session.add(new_event)
        db.session.commit()

        return jsonify({
            "message": "Event created successfully",
            "event_id": new_event.id,
            "event": new_event.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occured: {e}"}), 500


@app.route("/events", methods=['GET'], strict_slashes=False)
def get_all_events():
    """Gets all events"""
    try:
        events = Event.query.all()
        events_data = [event.to_dict() for event in events]
        return jsonify({"events": events_data}), 200
    except Exception as e:
        return jsonify({"error": f"An error occured: {e}"}), 500


@app.route("/events/<int:event_id>", methods=['GET'], strict_slashes=False)
def get_single_event(event_id):
    """Gets single event"""
    try:
        event = Event.query.get(event_id)
        if event:
            return jsonify({"event": event.to_dict()}), 200
        else:
            return jsonify({"message": "Event not found"}), 404
    except Exception as e:
        return jsonify({"error": f"An error occured: {e}"}), 500


@app.route("/events/<int:event_id>", methods=['PUT'], strict_slashes=False)
def update_event(event_id):
    """Updates event"""
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({"message": "Event not found"}), 404
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON or no data provided"}), 400
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'event_date' in data:
            try:
                event.event_date = datetime.strptime(
                    data['event_date'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return jsonify({"error": "Invalid event_date format. "
                                "Use YYYY-MM-DD HH:MM:SS"}), 400
        if 'location' in data:
            event.location = data['location']

        db.session.commit()

        return jsonify({
            "message": "Event updated successfully",
            "event_id": event.id,
            "updated_event": event.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occured: {e}"}), 500


@app.route("/events/<int:event_id>", methods=['DELETE'], strict_slashes=False)
def delete_event(event_id):
    """Deletes event"""
    try:
        event_to_delete = Event.query.get(event_id)
        if not event_to_delete:
            return jsonify({"message": "event_to_delete"}), 400
        db.session.delete(event_to_delete)
        db.session.commit()
        return jsonify({"message": "Event deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occured: {e}"}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
