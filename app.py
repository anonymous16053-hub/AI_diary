from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from database.db import db
import os
from datetime import datetime
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

@app.route("/user/<int:user_id>")
def get_user(user_id):

    user=User.query.get(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }),404
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "theme": user.theme,
        "ai_personality": user.ai_personality,
        "created_at": user.created_at.strftime("%Y-%m-%d")
    })

@app.route("/user/<int:user_id>",methods=["PUT"])
def update_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }),404
    data = request.json

    user.username = data.get("username", user.username)
    user.email = data.get("email", user.email)

    db.session.commit()

    return jsonify({
        "message": "User Profile updated successfully"
    })

@app.route("/preferences/<int:user_id>", methods=["PUT"])
def update_preferences(user_id):

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    data = request.json

    user.theme = data.get(
        "theme",
        user.theme
    )

    user.ai_personality = data.get(
        "ai_personality",
        user.ai_personality
    )

    db.session.commit()

    return jsonify({
        "message": "Preferences updated"
    })

@app.route("/change-password/<int:user_id>", methods=["PUT"])
def change_password(user_id):

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    data = request.json

    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not check_password_hash(
        user.password,
        current_password
    ):
        return jsonify({
            "message": "Current password is incorrect"
        }), 400

    user.password = generate_password_hash(
        new_password
    )

    db.session.commit()

    return jsonify({
        "message": "Password changed successfully"
    })

@app.route("/user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    DiaryEntry.query.filter_by(
        user_id=user_id
    ).delete()

    ChatHistory.query.filter_by(
        user_id=user_id
    ).delete()

    db.session.delete(user)

    db.session.commit()

    return jsonify({
        "message": "Account deleted successfully"
    })

@app.route("/save", methods=["POST"])
def save_entry():

    data = request.json
    entry = data.get("entry")
    user_id = data.get("user_id")
    title = data.get("title")

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
            title=title,
            user_id=user_id,
            entry_text=entry,
            mood=emotion
            )
        db.session.add(entry_record)
        db.session.commit()
        return jsonify({
            "title": title,
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

@app.route("/entry/<int:entry_id>", methods=["GET"])
def get_entry(entry_id):

    entry = DiaryEntry.query.get(entry_id)

    if not entry:
        return jsonify({
            "message": "Entry not found"
        }), 404

    return jsonify({
        "id": entry.id,
        "title": entry.title,
        "text": entry.entry_text,
        "mood": entry.mood,
        "date": entry.created_at.strftime("%Y-%m-%d")
    })

@app.route("/entry/<int:entry_id>", methods=["PUT"])
def update_entry(entry_id):

    entry = DiaryEntry.query.get(entry_id)

    if not entry:
        return jsonify({
            "message": "Entry not found"
        }), 404

    data = request.json

    entry.title = data.get(
        "title",
        entry.title
    )

    entry.entry_text = data.get(
        "text",
        entry.entry_text
    )

    db.session.commit()

    return jsonify({
        "message": "Entry updated"
    })

@app.route("/entry/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id):

    entry = DiaryEntry.query.get(entry_id)

    if not entry:
        return jsonify({
            "message": "Entry not found"
        }), 404

    db.session.delete(entry)

    db.session.commit()

    return jsonify({
        "message": "Entry deleted"
    })


#chat
@app.route("/chat", methods=["POST"])
def chat():

    data = request.json
    user_message = request.json.get("message")
    user_id = data.get("user_id")

    user = User.query.get(user_id)

    personality = (
    user.ai_personality
    if user
    else "friendly"
)

    try:

        # Mood detection
        mood = detect_emotion(user_message)

        previous_chats = (
        ChatHistory.query
        .filter_by(user_id=user_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(5)
        .all()
    )

        conversation_history = ""

        if personality == "friendly":

            personality_prompt = """
            Be warm, friendly and conversational.
            Talk like a supportive friend.
            """

        elif personality == "professional":

            personality_prompt = """
            Be professional, concise and objective.
            Focus on practical advice.
            """

        elif personality == "motivational":

            personality_prompt = """
            Be energetic and motivational.
            Encourage the user and focus on growth.
            """

        elif personality == "therapist":

            personality_prompt = """
            Be empathetic and reflective.
            Help the user explore emotions.
            Do not diagnose conditions.
            """

        else:

            personality_prompt = """
            Be warm and supportive.
            """

        for chat in reversed(previous_chats):
                    conversation_history += f"""
                    User: {chat.user_message}
                    AI: {chat.ai_reply}
        """

        # {personality}

        # prompt
        prompt = f"""

        {personality_prompt}

        Previous Conversation:
        {conversation_history}

        User Mood: {mood}

        User Message: {user_message}

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
            contents=prompt,
            )
        
        reply = response.text

        # Add emotional enhancement
        reply = emotional_response(user_message, reply)

        date = datetime.now().strftime("%Y-%m-%d")
        chat_record = ChatHistory(
    user_id=user_id,
    user_message=user_message,
    ai_reply=reply,
    chat_mood=mood
)

        db.session.add(chat_record)
        db.session.commit()

        return jsonify({
            "reply": reply,
            "mood": mood,
            "preference":personality

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

    entries = DiaryEntry.query.filter_by(user_id=user_id).all()

    mood_counts = Counter()

    timeline = []

    for entry in entries:

        mood_counts[entry.mood] += 1

        timeline.append({
            "date": entry.created_at.strftime("%Y-%m-%d"),
            "mood": entry.mood
        })

    dominant_mood = (
    max(mood_counts, key=mood_counts.get)
    if mood_counts
    else "None"
)
    latest_mood = (
    entries[-1].mood
    if entries
    else "None"
)

    return jsonify({
    "total_entries": len(entries),
    "dominant_mood": dominant_mood,
    "counts": dict(mood_counts),
    "latest_mood": latest_mood,
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
                "id": entry.id,
                "title": entry.title,
                "text": entry.entry_text,
                "mood": entry.mood,
                "date": entry.created_at.strftime("%Y-%m-%d")
                })

        return jsonify(data)

    except Exception as e:

        return jsonify({
            "message": str(e)
        })

@app.route("/chat-history/<int:user_id>")
def get_chat_history(user_id):

    chats = (
        ChatHistory.query
        .filter_by(user_id=user_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )

    chat_list = []

    for chat in chats:

        chat_list.append({
            "user_message": chat.user_message,
            "ai_reply": chat.ai_reply,
            "mood": chat.chat_mood,
            "date": chat.created_at.strftime("%Y-%m-%d %H:%M")
        })

    return jsonify(chat_list)

@app.route("/chat-history/<int:user_id>", methods=["DELETE"])
def delete_chat_history(user_id):

    ChatHistory.query.filter_by(
        user_id=user_id
    ).delete()

    db.session.commit()

    return jsonify({
        "message": "Chat history deleted"
    })

if __name__ == "__main__":
    app.run(debug=True)
