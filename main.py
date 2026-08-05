"""
Главный файл бота.
Инициализирует VK API и обрабатывает входящие сообщения.
"""
import os
from dotenv import load_dotenv
from vk_api import VkApi
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

import db
from commands import route
from utils.helpers import get_name, send

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))
ADMIN_IDS = [229750018]

if not TOKEN or not GROUP_ID:
    raise SystemExit("Создай файл .env и укажи VK_TOKEN и VK_GROUP_ID")

session = VkApi(token=TOKEN)
api = session.get_api()

longpoll = VkBotLongPoll(session, GROUP_ID)


def handle_message(event):
    """Обработать входящее сообщение."""
    user_id = event.obj["message"]["from_id"]
    peer_id = event.obj["message"]["peer_id"]
    text = event.obj["message"].get("text", "").strip()
    
    if not text:
        return
    
    player = db.get_player(user_id, lambda uid: get_name(api, uid))
    player["last_peer_id"] = peer_id
    db.save_player(player)
    
    command = text.lower()
    route(command, user_id, peer_id, text, player, api, ADMIN_IDS)


def main():
    """Главный цикл бота."""
    print("Бот запущен!")
    
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            handle_message(event)


if __name__ == "__main__":
    main()

# WSGI приложение для PythonAnywhere
app = longpoll