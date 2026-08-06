"""
Главный файл бота.
Инициализирует VK API и обрабатывает входящие сообщения.
"""
import os
import time
import traceback
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
    try:
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
        
    except Exception as e:
        print(f"❌ Ошибка обработки сообщения: {e}")
        traceback.print_exc()
        try:
            send(api, peer_id, "❌ Произошла ошибка. Попробуй позже.")
        except:
            pass


def main():
    """Главный цикл бота."""
    global longpoll  # ← ВАЖНО! Объявляем как глобальную
    
    print("✅ Бот запущен!")
    
    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    handle_message(event)
                    time.sleep(0.3)  # Задержка между сообщениями
                    
        except Exception as e:
            print(f"❌ Ошибка longpoll: {e}")
            traceback.print_exc()
            print(" Перезапуск через 10 секунд...")
            time.sleep(10)
            
            # Пересоздаём longpoll
            try:
                longpoll = VkBotLongPoll(session, GROUP_ID)
                print("✅ Longpoll пересоздан")
            except Exception as e2:
                print(f" Ошибка пересоздания longpoll: {e2}")


if __name__ == "__main__":
    main()