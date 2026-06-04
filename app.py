from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from database.db import db
import os
from datetime import datetime
from textblob import TextBlob
from collections import Counter
from google import genai
from dotenv import load_dotenv

from models.models import User, DiaryEntry, ChatHistory




app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

load_dotenv()
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)
@app.route("/test")
def test():
    return "Flask Working"

@app.route("/")
def home():
    return render_template("index.html")


# new_1 register
@app.route("/register", methods=["POST"])
def register():

    data = request.json

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    try:

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            return jsonify({
                "message": "Username already exists"
            })

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({
            "message": "Registered successfully"
        })

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "message": str(e)
        })
    
    
# new_1 login 
@app.route("/login", methods=["POST"])
def login():

    data = request.json

    username = data.get("username")
    password = data.get("password")

    try:

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            return jsonify({
                "message": "Login success",
                "user_id": user.id
            })

        return jsonify({
            "message": "Invalid credentials"
        })

    except Exception as e:

        return jsonify({
            "message": str(e)
        })
def detect_emotion(text):

    prompt = f"""
    You are an emotion classifier.

    Analyze the diary entry and return ONLY ONE emotion
    from the following list:

    Happy
    Sad
    Angry
    Anxious
    Stressed
    Excited
    Lonely
    Grateful
    Confused
    Neutral

    Return only the emotion word.

    Diary Entry:
    {text}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    print("GEMINI RESPONSE:", response.text)

    return response.text.strip()

@app.route("/save", methods=["POST"])
def save_entry():

    data = request.json
    entry = data.get("entry")
    user_id = data.get("user_id")

    try:
        #mood Detection

        emotion = detect_emotion(entry)

        # polarity = analysis.sentiment.polarity

        # if polarity > 0.3:
        #     mood = "Positive 😊"

        # elif polarity < -0.3:
        #     mood = "Negative 😔"

        # else:
        #     mood = "Neutral 😐"

        entry_record = DiaryEntry(
            user_id=user_id,
            entry_text=entry,
            mood=emotion
            )
        db.session.add(entry_record)
        db.session.commit()
        return jsonify({
            "message": "Saved successfully!",
            "mood": emotion
        })

    except Exception as e:

        return jsonify({
            "message": str(e)
        })
    


def emotional_response(user_message, reply):
    text = user_message.lower()

    if "sad" in text or "helpless" in text:
        return reply + "\n\n💛 I'm sorry you're feeling this way. Want to talk about what's bothering you?"

    elif "stress" in text or "overwhelmed" in text:
        return reply + "\n\n🧘 Try taking a short break or deep breathing—it really helps."

    elif "happy" in text or "good" in text:
        return reply + "\n\n😊 That’s great to hear! Keep enjoying the moment."

    return reply

#chat
@app.route("/chat", methods=["POST"])
def chat():

    data = request.json
    user_message = request.json.get("message")
    user_id = data.get("user_id")


    try:

        # Mood detection
        analysis = TextBlob(user_message)

        if analysis.sentiment.polarity > 0:
            mood = "Positive 😊"
        elif analysis.sentiment.polarity < 0:
            mood = "Negative 😔"
        else:
            mood = "Neutral 😐"

        previous_chats = (
        ChatHistory.query
        .filter_by(user_id=user_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(5)
        .all()
        )
        conversation_history = ""

        for chat in reversed(previous_chats):
            conversation_history += f"""
            User: {chat.user_message}
            AI: {chat.ai_reply}
"""


        # prompt
        prompt = f"""
        You are an intelligent emotional AI diary assistant.
        

        Your personality:
        - Friendly
        - Human-like
        - Emotionally supportive
        - Smart and conversational
        - Helpful instead of repetitive

        Rules:
        - Never repeatedly ask unnecessary follow-up questions.
        - If user asks for suggestions, directly provide them.
        - If user asks for songs, movies, quotes, activities, etc., give actual recommendations.
        - Keep responses natural and concise.
        - Use emojis occasionally.
        - Sound like a close supportive friend.
        - Avoid repeating phrases like:
        "I'd love to help"
        "Could you tell me more"
        repeatedly.
        - When user asks for songs, provide YouTube links if possible.
        Detect emotions naturally and respond empathetically.

        Previous Conversation:
        {conversation_history}
    
        User Mood:{mood}

        User Message:{user_message}


        """

        custom_reply = custom_music_response(user_message)
        if custom_reply:
            return jsonify({
        "reply": custom_reply,
        "mood": mood
    })
        # Gemini response
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
            )
        
        reply = response.text

        # Add emotional enhancement
        reply = emotional_response(user_message, reply)

        date = datetime.now().strftime("%Y-%m-%d")
        chat_record = ChatHistory(
        user_id=user_id,
        user_message=user_message,
        ai_reply=reply
        )

        db.session.add(chat_record)
        db.session.commit()

        return jsonify({
            "reply": reply,
            "mood": mood
        })

    except Exception as e:
        print("ERROR:", e)

        return jsonify({
            "reply": str(e),
            "mood": "Error"
        })

    
def custom_music_response(message):

    text = message.lower()

    if "arijit" in text:
        return """
🎵 Popular Arijit Singh Songs:

1. Kesariya
https://youtu.be/BddP6PYo2gs

2. Shayad
https://youtu.be/MJyKN-8UncM

3. Hawayein
https://youtu.be/zgltAHSekZY

4. Ilahi
https://youtu.be/fdubeMFwuGs

Enjoy your music 😊
"""

    return None    
    
# @app.route("/analytics")
# def analytics():

#     mood_counts = {
#         "Positive 😊": 0,
#         "Negative 😔": 0,
#         "Neutral 😐": 0
#     }

#     entries = DiaryEntry.query.all()

#     timeline = []

#     for entry in entries:

#         if entry.mood in mood_counts:
#             mood_counts[entry.mood] += 1

#         timeline.append({
#             "date": entry.created_at.strftime("%Y-%m-%d"),
#             "mood": entry.mood
#         })

#     return jsonify({
#         "counts": mood_counts,
#         "timeline": timeline
#     })

@app.route("/analytics/<int:user_id>")
def analytics(user_id):

    # entries = DiaryEntry.query.all()
    DiaryEntry.query.filter_by(user_id=user_id)

    mood_counts = Counter()

    timeline = []

    for entry in entries:

        mood_counts[entry.mood] += 1

        timeline.append({
            "date": entry.created_at.strftime("%Y-%m-%d"),
            "mood": entry.mood
        })

    return jsonify({
        "counts": dict(mood_counts),
        "timeline": timeline
    })


@app.route("/history/<int:user_id>")
def history(user_id):

    try:
        entries = (
            DiaryEntry.query
            .filter_by(user_id=user_id)
            .order_by(DiaryEntry.created_at.desc())
            .all()
)

        data = []
        for entry in entries:
            data.append({
                "text": entry.entry_text,
                "mood": entry.mood,
                "date": entry.created_at.strftime("%Y-%m-%d")
                })

        return jsonify(data)

    except Exception as e:

        return jsonify({
            "message": str(e)
        })

if __name__ == "__main__":
    app.run(debug=True)
