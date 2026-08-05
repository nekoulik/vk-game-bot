"""
Базовые команды: старт, баланс, работа, ставка, дуэль, бонус, топ, профиль.
"""
import random
import time
import datetime

import db
from config.items import ITEMS, ITEM_EMOJI
from config.pets import PETS
from utils.helpers import send, add_exp, get_player_damage, get_player_defense

WORK_COOLDOWN_SECONDS = 60
MIN_BET = 10

HELP_TEXT = (
    "Игровой бот\n\n"
    "Основные: старт, помощь, баланс, работа, ставка 50, дуэль, бонус, топ, профиль\n"
    "Магазин: магазин, инвентарь, купить <id>, экипировать <id>\n"
    "PvP: вызов @id123, принять, отклонить\n"
    "Босс: босс, атака, статус, сдаться\n"
    "Прогресс: квесты, выполнить квесты, достижения\n"
    "Питомцы: питомцы, купить питомца <id>, мои питомцы, активировать <id>\n"
    "Сезоны: сезон, история сезонов\n"
    "Игры: игры, кнб <камень|ножницы|бумага>, угадай <число>, лотерея\n"
    "Напоминания: напоминания, включить <тип>, выключить <тип>\n"
    "Кланы: клан, клан создать <название>, кланы, клан вступить <ID>"
)


def cmd_start(api, peer_id, player):
    """Команда /start или помощь."""
    send(api, peer_id, f"{player['name']}, добро пожаловать!\n\n{HELP_TEXT}")


def cmd_balance(api, peer_id, player):
    """Проверить баланс."""
    send(api, peer_id, f"Баланс: {player['balance']} монет.")
    db.check_achievements_on_action(player["user_id"], player, "rich")
    db.save_player(player)


def cmd_id(api, peer_id, user_id):
    """Узнать свой ID."""
    send(api, peer_id, f"Твой ID: {user_id}")


def cmd_work(api, peer_id, player):
    """Заработать монеты (работа)."""
    now = int(time.time())
    wait = WORK_COOLDOWN_SECONDS - (now - player.get("last_work", 0))
    if wait > 0:
        send(api, peer_id, f"Отдохни ещё {wait} сек.")
        return
    
    earned = random.randint(20, 80)
    
    # Бонус питомца
    pet_coin_bonus = db.get_pet_bonus(player["user_id"], "coins")
    if pet_coin_bonus > 0:
        earned = int(earned * (1 + pet_coin_bonus))
    
    # Бонус клана
    clan = db.get_clan(player["user_id"])
    if clan:
        clan_coins_bonus = db.get_clan_bonus(clan["id"], "coins")
        if clan_coins_bonus > 0:
            earned = int(earned * (1 + clan_coins_bonus))
    
    player["balance"] += earned
    player["last_work"] = now
    
    add_exp(player, 2, clan)
    db.save_player(player)
    db.update_daily_progress(player["user_id"], "coins", earned)
    db.add_season_points(player["user_id"], 2)
    db.check_achievements_on_action(player["user_id"], player, "rich")
    
    pet_msg = f" (с бонусом питомца +{int(pet_coin_bonus*100)}%)" if pet_coin_bonus > 0 else ""
    send(api, peer_id, f"Ты заработал {earned} монет.{pet_msg}")


def cmd_bet(api, peer_id, player, command):
    """Сделать ставку."""
    parts = command.split()
    if len(parts) != 2:
        return
    try:
        amount = int(parts[1])
    except ValueError:
        return
    
    if amount < MIN_BET or amount > player["balance"]:
        send(api, peer_id, "Недостаточно монет или ставка слишком мала.")
        return
    
    player["balance"] -= amount
    if random.random() < 0.45:
        prize = amount * 2
        player["balance"] += prize
        db.update_daily_progress(player["user_id"], "coins", prize)
        msg = f"Выигрыш! +{prize} монет."
    else:
        msg = f"Не повезло. -{amount} монет."
    
    add_exp(player, 1)
    db.save_player(player)
    db.check_achievements_on_action(player["user_id"], player, "rich")
    send(api, peer_id, msg)


def cmd_duel(api, peer_id, player):
    """Дуэль с ботом (PvE)."""
    hp1, hp2, log = 100, 100, []
    for r in range(1, 6):
        d1 = get_player_damage(player)
        d2 = max(0, random.randint(12, 25) - get_player_defense(player))
        hp2 -= d1
        hp1 -= d2
        log.append(f"Раунд {r}: ты {d1}, бот {d2}")
        if hp1 <= 0 or hp2 <= 0:
            break
    
    clan = db.get_clan(player["user_id"])
    
    if hp2 <= 0 and hp1 > 0:
        reward = random.randint(30, 70)
        pet_coin_bonus = db.get_pet_bonus(player["user_id"], "coins")
        if pet_coin_bonus > 0:
            reward = int(reward * (1 + pet_coin_bonus))
        
        if clan:
            clan_coins_bonus = db.get_clan_bonus(clan["id"], "coins")
            if clan_coins_bonus > 0:
                reward = int(reward * (1 + clan_coins_bonus))
        
        player["balance"] += reward
        exp_gain = 3
        pet_exp_bonus = db.get_pet_bonus(player["user_id"], "exp")
        if pet_exp_bonus > 0:
            exp_gain = int(exp_gain * (1 + pet_exp_bonus))
        
        add_exp(player, exp_gain, clan)
        db.save_player(player)
        db.update_daily_progress(player["user_id"], "duels", 1)
        db.add_season_points(player["user_id"], 10)
        
        if clan:
            db.add_clan_exp(clan["id"], 5)
            
        achs = db.check_achievements_on_action(player["user_id"], player, "duel_win")
        ach_msg = "\n Достижение: " + ", ".join(achs) if achs else ""
        send(api, peer_id, f"Победа! +{reward} монет.{ach_msg}")
    else:
        add_exp(player, 1, clan)
        db.save_player(player)
        db.update_daily_progress(player["user_id"], "duels", 1)
        send(api, peer_id, "Поражение или ничья. Попробуй ещё раз.")


def cmd_bonus(api, peer_id, player):
    """Ежедневный бонус."""
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    
    if player.get("last_bonus") == today:
        send(api, peer_id, "Бонус уже получен сегодня.")
        return
        
    if player.get("last_bonus") == yesterday:
        player["bonus_streak"] = player.get("bonus_streak", 0) + 1
    else:
        player["bonus_streak"] = 1
        
    player["last_bonus"] = today
    reward = 50 + min(player["bonus_streak"], 10) * 10
    
    # Бонусы
    pet_daily_bonus = db.get_pet_bonus(player["user_id"], "daily")
    if pet_daily_bonus > 0:
        reward = int(reward * (1 + pet_daily_bonus))
        
    clan = db.get_clan(player["user_id"])
    if clan:
        clan_coins_bonus = db.get_clan_bonus(clan["id"], "coins")
        if clan_coins_bonus > 0:
            reward = int(reward * (1 + clan_coins_bonus))
    
    player["balance"] += reward
    add_exp(player, 1, clan)
    db.save_player(player)
    send(api, peer_id, f"Ежедневный бонус: +{reward} монет!\nСерия: {player['bonus_streak']} дн.")


def cmd_top(api, peer_id):
    """Таблица лидеров."""
    ranked = db.get_top_players(10)
    if not ranked:
        send(api, peer_id, "Пока нет игроков.")
        return
        
    medals = ["1 место", "2 место", "3 место"]
    lines = ["Топ игроков:\n"]
    for i, p in enumerate(ranked, start=1):
        title = f" [{p['title']}]" if p.get("title") else ""
        lines.append(f"{medals[i-1] if i <= 3 else f'{i}.'} {p['name']}{title} — ур. {p['level']}, {p['balance']} монет")
    send(api, peer_id, "\n".join(lines))


def cmd_profile(api, peer_id, player):
    """Профиль игрока."""
    eq = db.get_equipment(player["user_id"])
    cos = f"\nУкрашение: {ITEM_EMOJI.get(eq['cosmetic'], '')} {ITEMS[eq['cosmetic']]['name']}" if eq.get("cosmetic") and eq["cosmetic"] in ITEMS else ""
    
    active_pet_id = db.get_active_pet(player["user_id"])
    pet_info = ""
    if active_pet_id and active_pet_id in PETS:
        pet = PETS[active_pet_id]
        pet_info = f"\nПитомец: {pet['emoji']} {pet['name']} ({pet['desc']})"
        
    title_info = f"\nТитул: {player['title']}" if player.get("title") else ""
    season_info = f"\nСезонные очки: {player.get('season_points', 0)}"
    
    clan = db.get_clan(player["user_id"])
    clan_info = f"\nКлан: {clan['name']} (ур. {clan['level']})" if clan else ""
    
    text = (
        f"Профиль\n\n"
        f"Имя: {player['name']}\n"
        f"Уровень: {player['level']}\n"
        f"Опыт: {player['exp']}\n"
        f"Баланс: {player['balance']}\n"
        f"Серия бонусов: {player.get('bonus_streak', 0)} дн."
        f"{title_info}{season_info}{clan_info}{cos}{pet_info}"
    )
    send(api, peer_id, text)