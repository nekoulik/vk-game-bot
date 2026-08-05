"""Вспомогательные функции."""
import re
from vk_api.utils import get_random_id


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


def send(api, peer_id, text):
    """Отправить сообщение."""
    try:
        api.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())
    except Exception as e:
        print(f"Ошибка отправки в {peer_id}: {e}")


def parse_user_id_from_mention(text):
    """Извлечь ID пользователя из упоминания."""
    m = re.search(r'\[id(\d+)', text) or re.search(r'@id(\d+)', text) or re.search(r'(\d{5,10})', text)
    return int(m.group(1)) if m else None


def add_exp(player, amount=1, clan=None):
    """Добавить опыт игроку с учётом кланового бонуса."""
    from db.clans import get_clan_bonus, get_clan
    from db.clans import add_clan_exp
    
    if clan is None:
        clan = get_clan(player["user_id"])
    
    if clan:
        clan_exp_bonus = get_clan_bonus(clan["id"], "exp")
        if clan_exp_bonus > 0:
            amount = int(amount * (1 + clan_exp_bonus))
    
    player["exp"] += amount
    leveled_up = False
    while player["exp"] >= player["level"] * 10:
        player["exp"] -= player["level"] * 10
        player["level"] += 1
        leveled_up = True
        if clan:
            add_clan_exp(clan["id"], 10)
    return leveled_up


def get_player_damage(player):
    """Рассчитать урон игрока с учётом экипировки, питомца и клана."""
    import random
    from db.items import get_equipment
    from db.pets import get_pet_bonus
    from db.clans import get_clan, get_clan_bonus
    from config.items import ITEMS
    
    base = random.randint(12, 25)
    eq = get_equipment(player["user_id"])
    if eq.get("weapon") and eq["weapon"] in ITEMS:
        base += ITEMS[eq["weapon"]]["effect"].get("damage", 0)
    
    pet_bonus = get_pet_bonus(player["user_id"], "damage")
    if pet_bonus > 0:
        base = int(base * (1 + pet_bonus))
    
    clan = get_clan(player["user_id"])
    if clan:
        clan_damage_bonus = get_clan_bonus(clan["id"], "damage")
        if clan_damage_bonus > 0:
            base = int(base * (1 + clan_damage_bonus))
    
    return base


def get_player_defense(player):
    """Рассчитать защиту игрока."""
    from db.items import get_equipment
    from config.items import ITEMS
    
    defense = 0
    eq = get_equipment(player["user_id"])
    if eq.get("armor") and eq["armor"] in ITEMS:
        defense += ITEMS[eq["armor"]]["effect"].get("defense", 0)
    return defense