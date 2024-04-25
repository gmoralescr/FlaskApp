from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy.orm import backref
from sqlalchemy import text


from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

# Association table for the many-to-many relationship between users and notes
likes_table = db.Table('likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('note_id', db.Integer, db.ForeignKey('note.id'), primary_key=True),
    db.Column('timestamp', db.DateTime, index=True, default=func.now())
)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=True), default=func.now(), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    image_url = db.Column(db.String(1000000))  # Stores the image file path
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(10000), nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    size = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=True)  # Optional
    material = db.Column(db.String(100), nullable=True)  # Optional
    condition = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Available", index=True)
    # Relationship for likes, using the likes_table as the association table
    likers = db.relationship('User', secondary=likes_table, back_populates="liked_notes")

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    firstName = db.Column(db.String(150))
    # Relationship to Note, indicating which notes a user has
    notes = db.relationship('Note', backref='user')
    # Relationship for liked notes, using the likes_table as the association table
    liked_notes = db.relationship('Note', secondary=likes_table, back_populates="likers")


class ExchangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False, index=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    responder_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    status = db.Column(db.String(50), default='Pending')  # Possible values: Pending, Accepted, Rejected
    exchange_date = db.Column(db.DateTime(timezone=True))  # Timestamp when exchange is accepted

    item = db.relationship('Note', foreign_keys=[item_id], backref=backref('exchange_requests', lazy=True))
    requester = db.relationship('User', foreign_keys=[requester_id], backref=backref('sent_requests', lazy=True))
    responder = db.relationship('User', foreign_keys=[responder_id], backref=backref('received_requests', lazy=True))

