from database.db import db
from datetime import datetime


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True)

    password = db.Column(db.String(255), nullable=False)

    theme = db.Column(db.String(20), default="dark")

    ai_personality = db.Column(db.String(50), default="friendly")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
class DiaryEntry(db.Model):
    __tablename__ = "diary_entries"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(20))

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    entry_text = db.Column(db.Text)

    mood = db.Column(db.String(50))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    user_message = db.Column(db.Text)

    ai_reply = db.Column(db.Text)

    chat_mood = db.Column(
    db.String(50)
)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )