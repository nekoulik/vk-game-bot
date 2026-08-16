"""
Главный файл бота.
Инициализирует VK API и обрабатывает входящие сообщения.
"""
import os
import re
import time
import json
import hashlib
import traceback
from datetime import datetime
from dotenv import load_dotenv
from vk_api import VkApi
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

import db
from commands import route
from utils.helpers import get_name, send
from utils.keyboard import get_main_keyboard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from config.settings import VK_TOKEN, VK_GROUP_ID, ADMIN_IDS

if not VK_TOKEN or not VK_GROUP_ID:
    raise SystemExit("Создай файл .env и укажи VK_TOKEN и VK_GROUP_ID")

session = VkApi(token=VK_TOKEN)
api = session.get_api()

longpoll = VkBotLongPoll(session, VK_GROUP_ID)

# Защита от дубликатов: хэш (user_id + text + peer_id) -> время
processed_messages = {}

# Кэш участников беседы: {peer_id: {user_id: name}}
chat_members_cache = {}


def get_chat_members(peer_id):
    """Получить список участников беседы."""
    try:
        response = api.messages.getConversationMembers(peer_id=peer_id)
        members = {}
        for profile in response.get("profiles", []):
            user_id = profile["id"]
            user_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
            members[user_id] = user_name
        return members
    except Exception as e:
        print(f"Ошибка получения участников беседы: {e}")
        return {}


def check_chat_members_changes(peer_id):
    """Проверить изменения в составе участников беседы."""
    if peer_id not in chat_members_cache:
        chat_members_cache[peer_id] = get_chat_members(peer_id)
        print(f"📋 Кэш участников для {peer_id}: {len(chat_members_cache[peer_id])} человек")
        return
    
    old_members = chat_members_cache[peer_id]
    new_members = get_chat_members(peer_id)
    
    # Нашли новых участников
    for user_id, user_name in new_members.items():
        if user_id not in old_members:
            print(f"➕ Новый участник: {user_name} ({user_id})")
            handle_member_join(peer_id, user_id, user_name)
    
    # Нашли ушедших участников
    for user_id, user_name in old_members.items():
        if user_id not in new_members:
            print(f"➖ Ушёл участник: {user_name} ({user_id})")
            handle_member_leave(peer_id, user_id, user_name)
    
    # Обновляем кэш
    chat_members_cache[peer_id] = new_members


def handle_member_join(peer_id, user_id, user_name):
    """Обработать вход участника."""
    settings = db.get_chat_settings(peer_id)
    
    if settings["is_restricted"]:
        if user_id not in ADMIN_IDS:
            print(f"🚫 Беседа закрыта, выгоняем {user_name}...")
            success = db.kick_user(api, peer_id, user_id)
            if success:
                send(api, peer_id, f"🚫 {user_name} был автоматически выгнан (беседа закрыта)")
            else:
                send(api, peer_id, f"⚠️ Не удалось выгнать {user_name}")
    else:
        if settings["notify_join"]:
            send(api, peer_id, f"👋 {user_name} присоединился к беседе!")
        
        if settings["welcome_message"]:
            welcome = settings["welcome_message"].replace("{name}", user_name)
            send(api, peer_id, welcome)


def handle_member_leave(peer_id, user_id, user_name):
    """Обработать выход участника."""
    settings = db.get_chat_settings(peer_id)
    
    if settings["notify_leave"]:
        send(api, peer_id, f"👋 {user_name} покинул беседу")
    
    if settings["goodbye_message"]:
        goodbye = settings["goodbye_message"].replace("{name}", user_name)
        send(api, peer_id, goodbye)


def clean_text(text):
    """Очистить текст от упоминаний группы, эмодзи и других служебных символов."""
    print(f" ДО очистки: '{text}'")
    
    # Удаляем ВСЕ упоминания в квадратных скобках
    text = re.sub(r'\[[^\]]*club[^\]]*\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[[^\]]*id[^\]]*\]', '', text, flags=re.IGNORECASE)
    
    # Удаляем @club и @id
    text = re.sub(r'@club\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'@id\d+', '', text, flags=re.IGNORECASE)
    
    # === УДАЛЯЕМ ЭМОДЗИ ===
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    text = emoji_pattern.sub(r'', text)
    
    # Удаляем пустые скобки
    text = re.sub(r'\[\]', '', text)
    
    # Удаляем лишние пробелы
    text = ' '.join(text.split())
    
    print(f"🧹 ПОСЛЕ очистки: '{text}'")
    
    return text.strip()


def handle_message(event):
    """Обработать входящее сообщение."""
    try:
        user_id = event.obj["message"]["from_id"]
        peer_id = event.obj["message"]["peer_id"]
        text = event.obj["message"].get("text", "").strip()
        
        # ✅ ОБРАБОТКА PAYLOAD (для кнопок клавиатуры)
        payload = event.obj["message"].get("payload")
        if payload:
            try:
                payload_data = json.loads(payload)
                if "command" in payload_data:
                    text = payload_data["command"]
                    print(f"🔘 Кнопка нажата: {text}")
            except Exception as e:
                print(f"⚠️ Ошибка разбора payload: {e}")
        
        print(f"💬 Сообщение от {user_id} в {peer_id}: {text[:50]}")
        
        if not text:
            return
        
        # === ОЧИСТКА ОТ УПОМИНАНИЙ ===
        text = clean_text(text)
        
        if not text:
            print("⚠️ Текст пуст после очистки")
            return
        
        # Создаём уникальный хэш сообщения
        msg_hash = hashlib.md5(f"{user_id}:{text.lower()}:{peer_id}".encode()).hexdigest()
        now = time.time()
        
        # Если такое же сообщение было меньше 10 секунд назад — пропускаем
        if msg_hash in processed_messages:
            if now - processed_messages[msg_hash] < 10:
                print(f"️ Дубликат пропущен: {text[:30]}")
                return
        
        processed_messages[msg_hash] = now
        
        # Чистим старые записи (старше 120 секунд)
        old_keys = [k for k, v in processed_messages.items() if now - v > 120]
        for k in old_keys:
            del processed_messages[k]
        
        player = db.get_player(user_id, lambda uid: get_name(api, uid))
        player["last_peer_id"] = peer_id
        player["last_activity"] = datetime.now().isoformat()
        db.save_player(player)
        
        # === ПРОВЕРКА МУТА ===
        if player.get("balance") == -2:
            mute_until = player.get("mute_until", 0)
            if mute_until and int(mute_until) > int(time.time()):
                remaining = int((int(mute_until) - int(time.time())) / 60)
                send(api, peer_id, f" Вы в муте! Осталось: {remaining} мин.")
                return
            else:
                player["balance"] = 0
                player["mute_until"] = 0
                db.save_player(player)
                send(api, peer_id, "✅ Ваш мут истёк! Добро пожаловать обратно!")
        
        # === ПРОВЕРКА ОГРАНИЧЕНИЯ БЕСЕДЫ ===
        if peer_id > 2000000000:
            settings = db.get_chat_settings(peer_id)
            if settings["is_restricted"]:
                if user_id not in ADMIN_IDS:
                    print(f"🚫 Беседа закрыта, выгоняем {user_id}...")
                    success = db.kick_user(api, peer_id, user_id)
                    if success:
                        send(api, peer_id, f"🚫 Пользователь был автоматически выгнан (беседа закрыта)")
                    return
            
            # Проверяем изменения в составе участников
            check_chat_members_changes(peer_id)
        
        # === ОБРАБОТКА КОМАНДЫ ===
        command = text.lower()
        print(f"🔀 Команда: '{command}'")
        
        handled = route(command, user_id, peer_id, text, player, api, ADMIN_IDS)
        if handled:
            print(f"✅ Команда обработана")
        else:
            print(f"️ Сообщение проигнорировано (неизвестная команда)")
        
    except Exception as e:
        print(f"❌ Ошибка обработки сообщения: {e}")
        traceback.print_exc()
        try:
            send(api, peer_id, "❌ Произошла ошибка. Попробуй позже.")
        except:
            pass


def main():
    """Главный цикл бота."""
    global longpoll
    
    # === ИНИЦИАЛИЗАЦИЯ БД ===
    db.init_db()  # Создаёт все таблицы (players, boss, items и т.д.)
    db.init_chat_settings_table()  # Таблица настроек беседы
    
    print("="*50)
    print("✅ Бот запущен!")
    print(f"👑 Админы: {ADMIN_IDS}")
    print(f"📱 ID группы: {VK_GROUP_ID}")
    print("="*50)
    print("Нажми Ctrl+C для остановки\n")
    
    try:
        while True:
            for event in longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    handle_message(event)
                    time.sleep(0.3)
                else:
                    print(f"ℹ️ Другое событие: {event.type}")
                    
    except KeyboardInterrupt:
        print("\n" + "="*50)
        print("🛑 Бот остановлен пользователем. До встречи!")
        print("="*50)
    except Exception as e:
        print(f"❌ Ошибка longpoll: {e}")
        traceback.print_exc()
        print("⏳ Перезапуск через 10 секунд...")
        time.sleep(10)
        
        try:
            longpoll = VkBotLongPoll(session, VK_GROUP_ID)
            print("✅ Longpoll пересоздан")
            main()
        except Exception as e2:
            print(f"⚠️ Ошибка пересоздания longpoll: {e2}")


if __name__ == "__main__":
    main()