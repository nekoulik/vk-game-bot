
"""
Вспомогательные функции для Club Anicoke Bot.
Включает работу с VK API, математические расчёты и парсинг.
"""
import re
import random
import vk_api
from vk_api.utils import get_random_id


# ==========================================
# 1. РАБОТА С VK API И СООБЩЕНИЯМИ
# ==========================================
def get_name(api, user_id):
    """Получить имя пользователя через VK API."""
    try:
        users = api.users.get(user_ids=user_id)
        if users:
            full_name = f"{users[0].get('first_name', '')} {users[0].get('last_name', '')}".strip()
            if full_name:
                return full_name
    except Exception:
        pass
    return f"ID{user_id}"


def get_user_info(vk, user_id):
    """Получение расширенной информации о пользователе (для аватарок и т.д.)"""
    try:
        response = vk.users.get(user_ids=user_id, fields='first_name,last_name,photo_50')
        if response:
            return response[0]
    except Exception:
        pass
    return {'first_name': 'Игрок', 'last_name': '', 'photo_50': ''}


def get_full_name(user_info):
    """Полное имя пользователя из словаря get_user_info"""
    first = user_info.get('first_name', '')
    last = user_info.get('last_name', '')
    return f"{first} {last}".strip()


def send(api, peer_id, text, attachment=None):
    """Универсальная отправка сообщения."""
    try:
        params = {
            'peer_id': peer_id,
            'message': text,
            'random_id': get_random_id()
        }
        if attachment:
            params['attachment'] = attachment
        api.messages.send(**params)
    except Exception as e:
        print(f"⚠️ Ошибка отправки в {peer_id}: {e}")


def parse_user_id_from_mention(text):
    """
    Извлечь ID пользователя из упоминания.
    Поддерживает форматы: [id123|name], @id123, или просто число 123456789
    """
    m = re.search(r'\[id(\d+)', text) or re.search(r'@id(\d+)', text) or re.search(r'(\d{5,10})', text)
    return int(m.group(1)) if m else None


def format_number(num):
    """Форматирование числа с пробелами-разделителями (1 000 000)"""
    if num is None:
        return "0"
    return f"{int(num):,}".replace(',', ' ')


# ==========================================
# 2. ИГРОВАЯ МЕХАНИКА (RPG)
# ==========================================
def add_exp(player, amount=1, clan=None):
    """
    Добавить опыт игроку с учётом кланового бонуса.
    ⚠️ ВАЖНО: Эта функция обновляет словарь player, но НЕ сохраняет в БД.
    После вызова обязательно сделай db.save_player(player) или аналогичный UPDATE.
    """
    # Локальный импорт для избежания циклических зависимостей
    from db.clans import get_clan_bonus, get_clan, add_clan_exp
    
    if clan is None:
        clan = get_clan(player["user_id"])
    
    # Применяем клановый бонус к опыту
    if clan:
        clan_exp_bonus = get_clan_bonus(clan["id"], "exp")
        if clan_exp_bonus > 0:
            amount = int(amount * (1 + clan_exp_bonus))
    
    player["exp"] += amount
    leveled_up = False
    
    # Цикл на случай получения сразу нескольких уровней
    while player["exp"] >= player["level"] * 10:
        player["exp"] -= player["level"] * 10
        player["level"] += 1
        leveled_up = True
        if clan:
            add_clan_exp(clan["id"], 10) # Бонус опыта самому клану
            
    return leveled_up


def get_player_damage(player):
    """Рассчитать итоговый урон игрока с учётом экипировки, питомца и клана."""
    from db.items import get_equipment
    from db.pets import get_pet_bonus
    from db.clans import get_clan, get_clan_bonus
    from config.items import ITEMS
    
    base = random.randint(12, 25)
    
    # Бонус от оружия
    eq = get_equipment(player["user_id"])
    if eq.get("weapon") and eq["weapon"] in ITEMS:
        base += ITEMS[eq["weapon"]]["effect"].get("damage", 0)
    
    # Бонус от питомца
    pet_bonus = get_pet_bonus(player["user_id"], "damage")
    if pet_bonus > 0:
        base = int(base * (1 + pet_bonus))
    
    # Бонус от клана
    clan = get_clan(player["user_id"])
    if clan:
        clan_damage_bonus = get_clan_bonus(clan["id"], "damage")
        if clan_damage_bonus > 0:
            base = int(base * (1 + clan_damage_bonus))
    
    return base


def get_player_defense(player):
    """Рассчитать итоговую защиту игрока."""
    from db.items import get_equipment
    from config.items import ITEMS
    
    defense = 0
    eq = get_equipment(player["user_id"])
    
    # Бонус от брони
    if eq.get("armor") and eq["armor"] in ITEMS:
        defense += ITEMS[eq["armor"]]["effect"].get("defense", 0)
        
    return defense