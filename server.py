import os
from flask import Flask, request
import game

app = Flask(__name__)
CONFIRMATION = os.getenv("VK_CONFIRMATION", "")
SECRET = os.getenv("VK_SECRET", "")

@app.route("/", methods=["GET"])
def index():
    return "🎮 VK game bot is running"

@app.route("/", methods=["POST"])
def callback():
    data = request.get_json(force=True, silent=True) or {}
    
    if data.get("type") == "confirmation":
        return CONFIRMATION
    
    if SECRET and data.get("secret") != SECRET:
        return "invalid secret", 403
    
    if data.get("type") == "message_new":
        obj = data.get("object", {}) or {}
        message = obj.get("message") or obj  # Compatibility with API versions
        user_id = message.get("from_id")
        peer_id = message.get("peer_id")
        text = message.get("text", "")
        if user_id and peer_id and text:
            try:
                game.handle(user_id, peer_id, text)
            except Exception as e:
                print("Ошибка в обработчике:", e)
    
    return "ok"