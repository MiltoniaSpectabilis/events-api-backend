#!/usr/bin/env python3
""""""
from database import db


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Event {self.id}: {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            # Ensure datetime objects are formatted to string for JSON
            'event_date': self.event_date.strftime('%Y-%m-%d %H:%M:%S')
            if self.event_date else None,
            'location': self.location,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
            if self.created_at else None
        }
