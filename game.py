import os
import random
import time
import datetime
from collections import Counter

from vk_api import VkApi
from vk_api.utils import get_random_id
from dotenv import load_dotenv
import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))

if not TOKEN or not GROUP_ID:
    raise SystemExit("Создай файл .env и укажи VK_TOKEN и VK_GROUP_ID")

# ==================== АДМИНЫ ====================
ADMIN_IDS = [229750018]

def is_admin(user_id):
    return user_id in ADMIN_IDS

WORK_COOLDOWN_SECONDS = 60
MIN_BET = 10
DUEL_TIMEOUT_SECONDS = 300
BOSS_TIMEOUT_SECONDS = 600

session = VkApi(token=TOKEN)
api = session.get_api()

ITEMS = {
    1: {"name": "Зелье здоровья", "price": 100, "type": "consumable", "desc": "Восстанавливает 30 HP в дуэли", "effect": {"hp": 30}},
    2: {"name": "Ржавый меч", "price": 500, "type": "weapon", "desc": "+10 к урону в дуэлях", "effect": {"damage": 10}},
    3: {"name": "Стальной меч", "price": 1500, "type": "weapon", "desc": "+25 к урону в дуэлях", "effect": {"damage": 25}},
    4: {"name": "Деревянный щит", "price": 400, "type": "armor", "desc": "-10 от получаемого урона", "effect": {"defense": 10}},
    5: {"name": "Железный щит", "price": 1200, "type": "armor", "desc": "-25 от получаемого урона", "effect": {"defense": 25}},
    6: {"name": "Корона", "price": 5000, "type": "cosmetic", "desc": "Для красоты в профиле", "effect": {}},
    7: {"name": "Алмазный меч", "price": 5000, "type": "weapon", "desc": "+50 к урону в дуэлях", "effect": {"damage": 50}},
    8: {"name": "Большое зелье", "price": 250, "type": "consumable", "desc": "Восстанавливает 70 HP в дуэли", "effect": {"hp": 70}},
}

ITEM_EMOJI = {1: "", 2: "⚔️", 3: "⚔️", 4: "🛡️", 5: "️", 6: "", 7: "💎", 8: ""}

BOSS_LEVELS = {
    1: {"name": "Гоблин-воин", "hp": 200, "attack": 15, "defense": 5, "reward": 100, "exp": 10},
    2: {"name": "Огр-разбойник", "hp": 400, "attack": 25, "defense": 10, "reward": 200, "exp": 20},
    3: {"name": "Тёмный рыцарь", "hp": 800, "attack": 35, "defense": 15, "reward": 400, "exp": 40},
    4: {"name": "Дракон", "hp": 1500, "attack": 50, "defense": 20, "reward": 800, "exp": 80},
    5: {"name": "Древний демон", "hp": 3000, "attack": 70, "defense": 30, "reward": 1500, "exp": 150},
}

PETS = db.PETS


def get_name(user_id):
    try:
        users = api.users.get(user_ids=user_id)
        if users:
            full_name = f"{users[0].get('first_name', '')} {users[0].get('last_name', '')}".strip()
            if full_name:
                return full_name
    except Exception:
        pass
    return f"ID{user_id}"


def send(peer_id, text):
    try:
        api.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())
    except Exception as e:
        print(f"Ошибка отправки в {peer_id}: {e}")


def add_exp(player, amount=1):
    player["exp"] += amount
    
    # Клановый бонус к опыту
    clan = db.get_clan(player["user_id"])
    if clan:
        clan_exp_bonus = db.get_clan_bonus(clan["id"], "exp")
        if clan_exp_bonus > 0:
            amount = int(amount * (1 + clan_exp_bonus))
    
    leveled_up = False
    while player["exp"] >= player["level"] * 10:
        player["exp"] -= player["level"] * 10
        player["level"] += 1
        leveled_up = True
        # Добавляем опыт клану при повышении уровня
        if clan:
            db.add_clan_exp(clan["id"], 10)
    return leveled_up


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


def show_shop(peer_id):
    lines = ["Магазин предметов\n"]
    for item_id, item in ITEMS.items():
        lines.append(f"{item_id}. {ITEM_EMOJI.get(item_id, '')} {item['name']} — {item['price']} монет\n   {item['desc']}\n")
    lines.append("Чтобы купить: купить <номер>")
    send(peer_id, "\n".join(lines))


def buy_item(player, peer_id, item_id_str):
    try:
        item_id = int(item_id_str)
    except ValueError:
        send(peer_id, "Укажи номер предмета числом")
        return
    if item_id not in ITEMS:
        send(peer_id, "Такого предмета нет")
        return
    item = ITEMS[item_id]
    if player["balance"] < item["price"]:
        send(peer_id, f"Недостаточно монет! Нужно {item['price']}")
        return
    player["balance"] -= item["price"]
    db.save_player(player)
    db.add_to_inventory(player["user_id"], item_id, 1)
    send(peer_id, f"Куплено: {ITEM_EMOJI.get(item_id, '')} {item['name']} за {item['price']} монет!")


def show_inventory(player, peer_id):
    inventory = db.get_inventory(player["user_id"])
    if not inventory:
        send(peer_id, "Твой инвентарь пуст.")
        return
    lines = ["Твой инвентарь\n"]
    equipped = db.get_equipment(player["user_id"])
    for item_id, count in sorted(inventory.items()):
        if item_id in ITEMS:
            item = ITEMS[item_id]
            eq_mark = " (надето)" if any(eq_id == item_id for eq_id in equipped.values()) else ""
            lines.append(f"{item_id}. {ITEM_EMOJI.get(item_id, '')} {item['name']} x{count}{eq_mark}")
    lines.append("\nНадеть: экипировать <номер>")
    send(peer_id, "\n".join(lines))


def use_item(player, peer_id, item_id_str):
    try:
        item_id = int(item_id_str)
    except ValueError:
        send(peer_id, "Укажи номер числом")
        return
    inventory = db.get_inventory(player["user_id"])
    if item_id not in inventory or inventory[item_id] <= 0:
        send(peer_id, "У тебя нет этого предмета!")
        return
    if item_id not in ITEMS:
        return
    item = ITEMS[item_id]
    if item["type"] == "consumable":
        db.remove_from_inventory(player["user_id"], item_id, 1)
        send(peer_id, f"Использовано: {ITEM_EMOJI.get(item_id, '')} {item['name']}\n{item['desc']}")
    elif item["type"] in ["weapon", "armor", "cosmetic"]:
        equipped = db.get_equipment(player["user_id"])
        old = equipped.get(item["type"])
        db.set_equipment(player["user_id"], item["type"], item_id)
        msg = f"Надето: {ITEM_EMOJI.get(item_id, '')} {item['name']}"
        if old and old in ITEMS:
            msg += f"\n(предыдущее {ITEMS[old]['name']} снято)"
        send(peer_id, msg)


def show_top(peer_id):
    ranked = db.get_top_players(10)
    if not ranked:
        send(peer_id, "Пока нет игроков.")
        return
    medals = ["1 место", "2 место", "3 место"]
    lines = ["Топ игроков:\n"]
    for i, p in enumerate(ranked, start=1):
        title = f" [{p['title']}]" if p.get("title") else ""
        lines.append(f"{medals[i-1] if i <= 3 else f'{i}.'} {p['name']}{title} — ур. {p['level']}, {p['balance']} монет")
    send(peer_id, "\n".join(lines))


def claim_daily_bonus(player, peer_id):
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    if player.get("last_bonus") == today:
        send(peer_id, "Бонус уже получен сегодня.")
        return
    if player.get("last_bonus") == yesterday:
        player["bonus_streak"] = player.get("bonus_streak", 0) + 1
    else:
        player["bonus_streak"] = 1
    player["last_bonus"] = today
    reward = 50 + min(player["bonus_streak"], 10) * 10
    
    # Клановый бонус к монетам
    clan = db.get_clan(player["user_id"])
    if clan:
        clan_coins_bonus = db.get_clan_bonus(clan["id"], "coins")
        if clan_coins_bonus > 0:
            reward = int(reward * (1 + clan_coins_bonus))
    
    pet_daily_bonus = db.get_pet_bonus(player["user_id"], "daily")
    if pet_daily_bonus > 0:
        reward = int(reward * (1 + pet_daily_bonus))
    
    player["balance"] += reward
    add_exp(player, 1)
    db.save_player(player)
    send(peer_id, f"Ежедневный бонус: +{reward} монет!\nСерия: {player['bonus_streak']} дн.")


def get_player_damage(player):
    base = random.randint(12, 25)
    eq = db.get_equipment(player["user_id"])
    if eq.get("weapon") and eq["weapon"] in ITEMS:
        base += ITEMS[eq["weapon"]]["effect"].get("damage", 0)
    
    # Бонус питомца
    pet_bonus = db.get_pet_bonus(player["user_id"], "damage")
    if pet_bonus > 0:
        base = int(base * (1 + pet_bonus))
    
    # Клановый бонус к урону
    clan = db.get_clan(player["user_id"])
    if clan:
        clan_damage_bonus = db.get_clan_bonus(clan["id"], "damage")
        if clan_damage_bonus > 0:
            base = int(base * (1 + clan_damage_bonus))
    
    return base


def get_player_defense(player):
    defense = 0
    eq = db.get_equipment(player["user_id"])
    if eq.get("armor") and eq["armor"] in ITEMS:
        defense += ITEMS[eq["armor"]]["effect"].get("defense", 0)
    return defense


def play_duel_vs_bot(player, peer_id):
    hp1, hp2, log = 100, 100, []
    for r in range(1, 6):
        d1, d2 = get_player_damage(player), max(0, random.randint(12, 25) - get_player_defense(player))
        hp2 -= d1
        hp1 -= d2
        log.append(f"Раунд {r}: ты {d1}, бот {d2}")
        if hp1 <= 0 or hp2 <= 0:
            break
    
    if hp2 <= 0 and hp1 > 0:
        reward = random.randint(30, 70)
        pet_coin_bonus = db.get_pet_bonus(player["user_id"], "coins")
        if pet_coin_bonus > 0:
            reward = int(reward * (1 + pet_coin_bonus))
        
        # Клановый бонус к монетам
        clan = db.get_clan(player["user_id"])
        if clan:
            clan_coins_bonus = db.get_clan_bonus(clan["id"], "coins")
            if clan_coins_bonus > 0:
                reward = int(reward * (1 + clan_coins_bonus))
        
        player["balance"] += reward
        exp_gain = 3
        pet_exp_bonus = db.get_pet_bonus(player["user_id"], "exp")
        if pet_exp_bonus > 0:
            exp_gain = int(exp_gain * (1 + pet_exp_bonus))
        
        add_exp(player, exp_gain)
        db.save_player(player)
        db.update_daily_progress(player["user_id"], "duels", 1)
        db.add_season_points(player["user_id"], 10)
        
        # Добавляем опыт клану
        if clan:
            db.add_clan_exp(clan["id"], 5)
        
        achs = db.check_achievements_on_action(player["user_id"], player, "duel_win")
        ach_msg = "\n🏆 Достижение: " + ", ".join(achs) if achs else ""
        send(peer_id, f"Победа! +{reward} монет.{ach_msg}")
    else:
        add_exp(player, 1)
        db.save_player(player)
        db.update_daily_progress(player["user_id"], "duels", 1)
        send(peer_id, "Поражение или ничья. Попробуй ещё раз.")


def parse_user_id_from_mention(text):
    import re
    m = re.search(r'\[id(\d+)', text) or re.search(r'@id(\d+)', text) or re.search(r'(\d{5,10})', text)
    return int(m.group(1)) if m else None


def challenge_player(challenger_id, challenged_id, challenger_peer_id):
    if challenged_id == challenger_id:
        send(challenger_peer_id, "Нельзя вызвать самого себя!")
        return
    challenged = db.get_player(challenged_id, get_name)
    if not challenged:
        send(challenger_peer_id, "Этот игрок ещё не начинал игру.")
        return
    existing = db.get_duel(challenged_id)
    if existing and time.time() - existing["timestamp"] < DUEL_TIMEOUT_SECONDS:
        send(challenger_peer_id, "Этот игрок уже получил вызов.")
        return
    db.save_duel(challenged_id, challenger_id, challenger_peer_id, time.time())
    challenger = db.get_player(challenger_id, get_name)
    send(challenger_peer_id, f"Вы вызвали {challenged['name']} на дуэль!")
    if challenged.get("last_peer_id"):
        send(challenged["last_peer_id"], f"⚔️ {challenger['name']} вызывает вас!\nНапишите: принять")


def accept_duel(challenged_id, challenged_peer_id):
    challenge = db.get_duel(challenged_id)
    if not challenge:
        send(challenged_peer_id, "Нет активных вызовов.")
        return
    if time.time() - challenge["timestamp"] >= DUEL_TIMEOUT_SECONDS:
        db.delete_duel(challenged_id)
        send(challenged_peer_id, "Вызов истёк.")
        return
    db.delete_duel(challenged_id)
    send(challenged_peer_id, "Вы приняли вызов!")
    send(challenge["challenger_peer_id"], "Соперник принял вызов!")
    p1 = db.get_player(challenge["challenger_id"], get_name)
    p2 = db.get_player(challenged_id, get_name)
    play_pvp_duel(p1, p2, challenge["challenger_peer_id"], challenged_peer_id)


def decline_duel(challenged_id, challenged_peer_id):
    challenge = db.get_duel(challenged_id)
    if not challenge:
        return
    db.delete_duel(challenged_id)
    send(challenged_peer_id, "Вы отклонили вызов.")
    send(challenge["challenger_peer_id"], f"{db.get_player(challenged_id, get_name)['name']} отклонил вызов.")


def play_pvp_duel(p1, p2, peer1, peer2):
    hp1, hp2, log = 100, 100, []
    for r in range(1, 8):
        if hp1 <= 0 or hp2 <= 0:
            break
        d1, d2 = get_player_damage(p1), get_player_damage(p2)
        def1, def2 = get_player_defense(p1), get_player_defense(p2)
        ad1, ad2 = max(3, d1 - def2), max(3, d2 - def1)
        hp2 -= ad1
        hp1 -= ad2
        log.append(f"Раунд {r}: {p1['name']} -{ad1}, {p2['name']} -{ad2}")
    
    if hp1 > 0 and hp2 <= 0:
        reward = random.randint(50, 100)
        pet_coin_bonus = db.get_pet_bonus(p1["user_id"], "coins")
        if pet_coin_bonus > 0:
            reward = int(reward * (1 + pet_coin_bonus))
        
        # Клановый бонус
        clan = db.get_clan(p1["user_id"])
        if clan:
            clan_coins_bonus = db.get_clan_bonus(clan["id"], "coins")
            if clan_coins_bonus > 0:
                reward = int(reward * (1 + clan_coins_bonus))
        
        p1["balance"] += reward
        add_exp(p1, 5)
        add_exp(p2, 2)
        db.save_player(p1)
        db.save_player(p2)
        db.update_daily_progress(p1["user_id"], "duels", 1)
        db.add_season_points(p1["user_id"], 15)
        
        # Опыт клану
        if clan:
            db.add_clan_exp(clan["id"], 10)
        
        achs = db.check_achievements_on_action(p1["user_id"], p1, "duel_win")
        res = f"🏆 Победил {p1['name']}! +{reward} монет." + ("\n🏆 Достижение: " + ", ".join(achs) if achs else "")
    elif hp2 > 0 and hp1 <= 0:
        reward = random.randint(50, 100)
        pet_coin_bonus = db.get_pet_bonus(p2["user_id"], "coins")
        if pet_coin_bonus > 0:
            reward = int(reward * (1 + pet_coin_bonus))
        
        clan = db.get_clan(p2["user_id"])
        if clan:
            clan_coins_bonus = db.get_clan_bonus(clan["id"], "coins")
            if clan_coins_bonus > 0:
                reward = int(reward * (1 + clan_coins_bonus))
        
        p2["balance"] += reward
        add_exp(p2, 5)
        add_exp(p1, 2)
        db.save_player(p1)
        db.save_player(p2)
        db.update_daily_progress(p2["user_id"], "duels", 1)
        db.add_season_points(p2["user_id"], 15)
        
        if clan:
            db.add_clan_exp(clan["id"], 10)
        
        achs = db.check_achievements_on_action(p2["user_id"], p2, "duel_win")
        res = f"🏆 Победил {p2['name']}! +{reward} монет." + ("\n🏆 Достижение: " + ", ".join(achs) if achs else "")
    else:
        add_exp(p1, 2)
        add_exp(p2, 2)
        db.save_player(p1)
        db.save_player(p2)
        res = "Ничья."
    
    msg = f"⚔️ PvP дуэль:\n" + "\n".join(log[-5:]) + f"\n\n{res}"
    send(peer1, msg)
    if peer2 != peer1:
        send(peer2, msg)


def start_boss_fight(user_id, peer_id):
    boss = db.get_boss()
    if boss and boss.get("active"):
        if boss.get("start_time") and (time.time() - boss["start_time"]) > BOSS_TIMEOUT_SECONDS:
            db.clear_boss()
            return create_new_boss(user_id, peer_id)
        if any(p["player_id"] == user_id for p in boss.get("participants", [])):
            send(peer_id, "Ты уже участвуешь! Пиши 'атака'.")
            return
        player = db.get_player(user_id, get_name)
        boss["participants"].append({"player_id": user_id, "name": player["name"], "damage": 0, "peer_id": peer_id})
        db.save_boss(boss)
        send(peer_id, f"Ты присоединился к бою с {boss['name']}!\nHP: {boss['current_hp']}/{boss['max_hp']}")
        return
    create_new_boss(user_id, peer_id)


def create_new_boss(user_id, peer_id):
    player = db.get_player(user_id, get_name)
    lvl = 1 if player.get("level", 1) <= 2 else 2 if player.get("level", 1) <= 5 else 3 if player.get("level", 1) <= 10 else 4 if player.get("level", 1) <= 15 else 5
    boss = BOSS_LEVELS[lvl]
    data = {"active": True, "level": lvl, "name": boss["name"], "max_hp": boss["hp"], "current_hp": boss["hp"],
            "attack": boss["attack"], "defense": boss["defense"], "start_time": time.time(),
            "participants": [{"player_id": user_id, "name": player["name"], "damage": 0, "peer_id": peer_id}]}
    db.save_boss(data)
    send(peer_id, f"👹 {boss['name']} (ур. {lvl}) появился!\nHP: {boss['hp']}\nПиши 'атака'!")
    
    # Уведомить всех игроков о появлении босса
    try:
        all_players = db.get_all_peer_ids()
        for p in all_players:
            if p["user_id"] == user_id:
                continue
            if db.should_notify(p["user_id"], "boss", cooldown_hours=2):
                try:
                    send(p["last_peer_id"], 
                         f"👹 Появился новый босс: {boss['name']} (ур. {lvl})!\n"
                         f"HP: {boss['hp']}\n"
                         f"Напиши: босс")
                    db.update_last_notification(p["user_id"], "boss")
                except Exception:
                    pass
    except Exception as e:
        print(f"Ошибка рассылки о боссе: {e}")


def attack_boss(user_id, peer_id):
    boss = db.get_boss()
    if not boss or not boss.get("active"):
        send(peer_id, "Нет активного боя. Напиши 'босс'.")
        return
    if boss.get("start_time") and (time.time() - boss["start_time"]) > BOSS_TIMEOUT_SECONDS:
        db.clear_boss()
        send(peer_id, "Бой истёк.")
        return
    p = next((x for x in boss.get("participants", []) if x["player_id"] == user_id), None)
    if not p:
        send(peer_id, "Ты не участвуешь! Напиши 'босс'.")
        return
    player = db.get_player(user_id, get_name)
    dmg = max(1, get_player_damage(player) - boss.get("defense", 0))
    boss["current_hp"] -= dmg
    p["damage"] += dmg
    boss_dmg = max(1, boss.get("attack", 10) - get_player_defense(player))
    db.save_boss(boss)
    send(peer_id, f"Ты нанёс {dmg} урона {boss['name']}!\nHP: {max(0, boss['current_hp'])}/{boss['max_hp']}\nБосс атакует на {boss_dmg}.")
    if boss["current_hp"] <= 0:
        defeat_boss(boss)


def defeat_boss(boss):
    total_dmg = sum(p["damage"] for p in boss["participants"])
    msgs = [f" {boss['name']} повержен!\n\nНаграды:"]
    for p in boss["participants"]:
        share = p["damage"] / total_dmg if total_dmg > 0 else 1 / len(boss["participants"])
        reward = int(BOSS_LEVELS[boss["level"]]["reward"] * share)
        exp = int(BOSS_LEVELS[boss["level"]]["exp"] * share)
        
        pet_coin_bonus = db.get_pet_bonus(p["player_id"], "coins")
        if pet_coin_bonus > 0:
            reward = int(reward * (1 + pet_coin_bonus))
        pet_exp_bonus = db.get_pet_bonus(p["player_id"], "exp")
        if pet_exp_bonus > 0:
            exp = int(exp * (1 + pet_exp_bonus))
        
        # Клановый бонус
        clan = db.get_clan(p["player_id"])
        if clan:
            clan_coins_bonus = db.get_clan_bonus(clan["id"], "coins")
            if clan_coins_bonus > 0:
                reward = int(reward * (1 + clan_coins_bonus))
            clan_exp_bonus = db.get_clan_bonus(clan["id"], "exp")
            if clan_exp_bonus > 0:
                exp = int(exp * (1 + clan_exp_bonus))
        
        pl = db.get_player(p["player_id"], get_name)
        pl["balance"] += reward
        add_exp(pl, exp)
        db.save_player(pl)
        db.update_daily_progress(p["player_id"], "boss", 1)
        db.add_season_points(p["player_id"], 20)
        
        # Опыт клану
        if clan:
            db.add_clan_exp(clan["id"], 15)
        
        achs = db.check_achievements_on_action(p["player_id"], pl, "boss_kill")
        ach_msg = "  " + ", ".join(achs) if achs else ""
        msgs.append(f"{p['name']}: +{reward}💰, +{exp}⭐ (урон: {p['damage']}){ach_msg}")
    boss["active"] = False
    db.save_boss(boss)
    for p in boss["participants"]:
        send(p["peer_id"], "\n".join(msgs))


def show_boss_status(user_id, peer_id):
    boss = db.get_boss()
    if not boss or not boss.get("active"):
        send(peer_id, "Нет активного боя.")
        return
    lines = [f"👹 {boss['name']} (ур. {boss['level']})", f"HP: {boss['current_hp']}/{boss['max_hp']}", f"Участников: {len(boss.get('participants', []))}"]
    for p in boss.get("participants", []):
        if p["player_id"] == user_id:
            lines.append(f"Твой урон: {p['damage']}")
    send(peer_id, "\n".join(lines))


def leave_boss_fight(user_id, peer_id):
    boss = db.get_boss()
    if not boss or not boss.get("active"):
        return
    boss["participants"] = [p for p in boss.get("participants", []) if p["player_id"] != user_id]
    db.save_boss(boss)
    send(peer_id, "Ты покинул бой.")


# ==================== УВЕДОМЛЕНИЯ ====================
def check_and_send_notifications(user_id, peer_id, player):
    """Проверить и отправить уведомления игроку."""
    notifications = []
    
    # Проверка ежедневного бонуса
    today = datetime.date.today().isoformat()
    if player.get("last_bonus") != today:
        if db.should_notify(user_id, "daily_bonus", cooldown_hours=12):
            notifications.append(
                "💰 Не забудь забрать ежедневный бонус!\n"
                "Напиши: бонус"
            )
            db.update_last_notification(user_id, "daily_bonus")
    
    # Проверка квестов
    player = db.check_and_reset_daily_quests(player)
    quests_status = db.get_daily_quests_status(player)
    if "⏳" in quests_status and player.get("daily_quest_claimed", 0) == 0:
        if db.should_notify(user_id, "quests", cooldown_hours=6):
            notifications.append(
                "📜 У тебя есть невыполненные квесты!\n"
                "Напиши: квесты"
            )
            db.update_last_notification(user_id, "quests")
    
    if notifications:
        send(peer_id, "🔔 Напоминания:\n\n" + "\n\n".join(notifications))


# ==================== ОБРАБОТЧИК ====================
def handle(user_id, peer_id, text):
    player = db.get_player(user_id, get_name)
    
    # Проверка бана
    if db.is_player_banned(user_id) and not is_admin(user_id):
        send(peer_id, " Вы забанены!")
        return
    
    player["last_peer_id"] = peer_id
    player = db.check_and_reset_season(player)
    db.save_player(player)
    player = db.check_and_reset_daily_quests(player)
    
    # Уведомления для обычных игроков
    if not is_admin(user_id):
        check_and_send_notifications(user_id, peer_id, player)
    
    command = text.lower().strip()
    if not command:
        return

    if command in ["старт", "start", "/start", "помощь", "help"]:
        send(peer_id, f"{player['name']}, добро пожаловать!\n\n{HELP_TEXT}")
        return
    if command in ["баланс", "balance"]:
        send(peer_id, f"Баланс: {player['balance']} монет.")
        db.check_achievements_on_action(user_id, player, "rich")
        return
    if command in ["id", "айди"]:
        send(peer_id, f"Твой ID: {user_id}")
        return
    if command in ["работа", "work"]:
        now = int(time.time())
        wait = WORK_COOLDOWN_SECONDS - (now - player.get("last_work", 0))
        if wait > 0:
            send(peer_id, f"Отдохни ещё {wait} сек.")
            return
        earned = random.randint(20, 80)
        
        pet_coin_bonus = db.get_pet_bonus(user_id, "coins")
        if pet_coin_bonus > 0:
            earned = int(earned * (1 + pet_coin_bonus))
        
        # Клановый бонус к монетам
        clan = db.get_clan(user_id)
        if clan:
            clan_coins_bonus = db.get_clan_bonus(clan["id"], "coins")
            if clan_coins_bonus > 0:
                earned = int(earned * (1 + clan_coins_bonus))
        
        player["balance"] += earned
        player["last_work"] = now
        add_exp(player, 2)
        db.save_player(player)
        db.update_daily_progress(user_id, "coins", earned)
        db.add_season_points(user_id, 2)
        db.check_achievements_on_action(user_id, player, "rich")
        pet_msg = f" (с бонусом питомца +{int(pet_coin_bonus*100)}%)" if pet_coin_bonus > 0 else ""
        send(peer_id, f"Ты заработал {earned} монет.{pet_msg}")
        return
    if command.startswith("ставка "):
        parts = command.split()
        if len(parts) != 2:
            return
        try:
            amount = int(parts[1])
        except ValueError:
            return
        if amount < MIN_BET or amount > player["balance"]:
            send(peer_id, "Недостаточно монет или ставка слишком мала.")
            return
        player["balance"] -= amount
        if random.random() < 0.45:
            prize = amount * 2
            player["balance"] += prize
            db.update_daily_progress(user_id, "coins", prize)
            msg = f"Выигрыш! +{prize} монет."
        else:
            msg = f"Не повезло. -{amount} монет."
        add_exp(player, 1)
        db.save_player(player)
        db.check_achievements_on_action(user_id, player, "rich")
        send(peer_id, msg)
        return
    if command in ["дуэль", "duel"]:
        play_duel_vs_bot(player, peer_id)
        return
    if command in ["бонус", "bonus"]:
        claim_daily_bonus(player, peer_id)
        return
    if command in ["топ", "top"]:
        show_top(peer_id)
        return
    if command in ["профиль", "profile"]:
        eq = db.get_equipment(player["user_id"])
        cos = f"\nУкрашение: {ITEM_EMOJI.get(eq['cosmetic'], '')} {ITEMS[eq['cosmetic']]['name']}" if eq.get("cosmetic") and eq["cosmetic"] in ITEMS else ""
        active_pet_id = db.get_active_pet(user_id)
        pet_info = ""
        if active_pet_id and active_pet_id in PETS:
            pet = PETS[active_pet_id]
            pet_info = f"\nПитомец: {pet['emoji']} {pet['name']} ({pet['desc']})"
        title_info = ""
        if player.get("title"):
            title_info = f"\nТитул: {player['title']}"
        season_info = f"\nСезонные очки: {player.get('season_points', 0)}"
        
        # Информация о клане
        clan = db.get_clan(user_id)
        clan_info = ""
        if clan:
            clan_info = f"\nКлан: {clan['name']} (ур. {clan['level']})"
        
        send(peer_id, f"Профиль\n\nИмя: {player['name']}\nУровень: {player['level']}\nОпыт: {player['exp']}\nБаланс: {player['balance']}\nСерия бонусов: {player.get('bonus_streak', 0)} дн.{title_info}{season_info}{clan_info}{cos}{pet_info}")
        return
    if command in ["магазин", "shop"]:
        show_shop(peer_id)
        return
    if command in ["инвентарь", "inv"]:
        show_inventory(player, peer_id)
        return
    
    if command.startswith("купить питомца ") or command.startswith("buy pet "):
        parts = command.split()
        if len(parts) < 3:
            send(peer_id, "Формат: купить питомца <id>")
            return
        try:
            pet_id = int(parts[2])
        except ValueError:
            send(peer_id, "ID должен быть числом")
            return
        
        if pet_id not in PETS:
            send(peer_id, "Такого питомца нет!")
            return
        
        pet = PETS[pet_id]
        if player["balance"] < pet["price"]:
            send(peer_id, f"Недостаточно монет! Нужно {pet['price']}")
            return
        
        owned = db.get_player_pets(user_id)
        if any(p["pet_id"] == pet_id for p in owned):
            send(peer_id, f"У тебя уже есть {pet['emoji']} {pet['name']}!")
            return
        
        player["balance"] -= pet["price"]
        db.save_player(player)
        db.buy_pet(user_id, pet_id)
        send(peer_id, f"🎉 Ты купил {pet['emoji']} {pet['name']}!\n{pet['desc']}\n\nАктивируй: активировать {pet_id}")
        return
    
    if command.startswith("купить ") or command.startswith("buy "):
        parts = command.split()
        if len(parts) < 2:
            send(peer_id, "Формат: купить <номер>")
            return
        buy_item(player, peer_id, parts[1])
        return
    
    if command.startswith("экипировать ") or command.startswith("использовать "):
        parts = command.split()
        if len(parts) < 2:
            send(peer_id, "Формат: экипировать <номер>")
            return
        use_item(player, peer_id, parts[1])
        return
    if command.startswith("вызов ") or command.startswith("pvp "):
        opp = parse_user_id_from_mention(text)
        if opp:
            challenge_player(user_id, opp, peer_id)
        return
    if command in ["принять", "accept"]:
        accept_duel(user_id, peer_id)
        return
    if command in ["отклонить", "decline"]:
        decline_duel(user_id, peer_id)
        return
    if command in ["босс", "boss"]:
        start_boss_fight(user_id, peer_id)
        return
    if command in ["атака", "attack", "удар"]:
        attack_boss(user_id, peer_id)
        return
    if command in ["статус", "status"]:
        show_boss_status(user_id, peer_id)
        return
    if command in ["сдаться", "leave"]:
        leave_boss_fight(user_id, peer_id)
        return
    
    if command in ["квесты", "задания", "quests"]:
        send(peer_id, db.get_daily_quests_status(player))
        return
    if command in ["выполнить квесты", "claim quests"]:
        success, msg = db.claim_daily_quests(player)
        send(peer_id, msg)
        return
    if command in ["достижения", "achievements"]:
        send(peer_id, db.get_achievements_list(user_id))
        return
    
    if command in ["питомцы", "pets", "магазин питомцев"]:
        lines = ["🐾 Магазин питомцев:\n"]
        player_pets = db.get_player_pets(user_id)
        owned_pet_ids = [p["pet_id"] for p in player_pets]
        
        for pet_id, pet in PETS.items():
            if pet_id in owned_pet_ids:
                active_mark = " ✅ (активен)" if any(p["pet_id"] == pet_id and p["is_active"] for p in player_pets) else " (куплен)"
                lines.append(f"{pet['emoji']} {pet['name']} — {pet['price']} монет{active_mark}\n   {pet['desc']}")
            else:
                lines.append(f"{pet['emoji']} {pet['name']} — {pet['price']} монет\n   {pet['desc']}")
        
        lines.append("\nКупить: купить питомца <id>")
        lines.append("Активировать: активировать <id>")
        send(peer_id, "\n".join(lines))
        return
    
    if command in ["мои питомцы", "my pets"]:
        owned = db.get_player_pets(user_id)
        if not owned:
            send(peer_id, "У тебя пока нет питомцев. Загляни в магазин: питомцы")
            return
        
        lines = ["🐾 Твои питомцы:\n"]
        for p in owned:
            pet = PETS.get(p["pet_id"])
            if pet:
                active_mark = " ✅ АКТИВЕН" if p["is_active"] else ""
                lines.append(f"{pet['emoji']} {pet['name']}{active_mark}\n   {pet['desc']}")
        
        send(peer_id, "\n".join(lines))
        return
    
    if command.startswith("активировать ") or command.startswith("activate "):
        parts = command.split()
        if len(parts) < 2:
            send(peer_id, "Формат: активировать <id>")
            return
        try:
            pet_id = int(parts[1])
        except ValueError:
            send(peer_id, "ID должен быть числом")
            return
        
        owned = db.get_player_pets(user_id)
        if not any(p["pet_id"] == pet_id for p in owned):
            send(peer_id, "У тебя нет этого питомца!")
            return
        
        db.activate_pet(user_id, pet_id)
        pet = PETS[pet_id]
        send(peer_id, f"✅ {pet['emoji']} {pet['name']} активирован!\n{pet['desc']}")
        return
    
    if command in ["сезон", "season", "сезонный рейтинг"]:
        current = db.get_current_season_number()
        leaderboard = db.get_season_leaderboard(10)
        
        if not leaderboard:
            send(peer_id, f"Сезон {current} только начался. Пока нет участников.\n\nНачисляй сезонные очки:\n• Дуэль: +10\n• PvP победа: +15\n• Босс: +20\n• Работа: +2")
            return
        
        lines = [f"🏆 Сезонный рейтинг (сезон {current}):\n"]
        medals = ["", "🥈", ""]
        for i, p in enumerate(leaderboard, start=1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            lines.append(f"{medal} {p['name']} — {p['season_points']} очков")
        
        lines.append(f"\nТвои очки: {player.get('season_points', 0)}")
        lines.append("\nНаграды топ-3:\n🥇 1000 монет + титул 'Чемпион'\n🥈 500 монет + 'Вице-чемпион'\n🥉 250 монет + 'Бронзовый'")
        send(peer_id, "\n".join(lines))
        return
    
    if command in ["история сезонов", "seasons history"]:
        history = db.get_season_history()
        if not history:
            send(peer_id, "История сезонов пуста.")
            return
        
        lines = ["📜 История сезонов:\n"]
        current_season_num = None
        for h in history:
            if h["season_number"] != current_season_num:
                current_season_num = h["season_number"]
                lines.append(f"\n🏆 Сезон {current_season_num}:")
            
            pl = db.get_player(h["user_id"], get_name)
            medal = ["🥇", "", "🥉"][h["position"]-1] if h["position"] <= 3 else f"{h['position']}."
            lines.append(f"  {medal} {pl['name']} — {h['season_points']} очков (+{h['reward_coins']}💰, '{h['title']}')")
        
        send(peer_id, "\n".join(lines))
        return
    
    if command in ["игры", "мини-игры", "games"]:
        send(peer_id, "🎮 Мини-игры:\n\n"
                     "🪨 Камень-ножницы-бумага:\n"
                     "  кнб <камень|ножницы|бумага>\n"
                     "  Приз за победу: +10 монет\n\n"
                     "🎲 Угадай число:\n"
                     "  угадай <число от 1 до 10>\n"
                     "  Приз: 50 монет\n\n"
                     "🎫 Лотерея (100 монет):\n"
                     "  лотерея\n"
                     "  Шанс 30%, приз 200-500 монет")
        return
    
    if command in ["кнб", "камень ножницы бумага", "rps"]:
        send(peer_id, "🪨 Камень-ножницы-бумага!\n\nНапиши: кнб <камень|ножницы|бумага>")
        return
    
    if command.startswith("кнб ") or command.startswith("rps "):
        parts = command.split()
        if len(parts) < 2:
            send(peer_id, "Формат: кнб <камень|ножницы|бумага>")
            return
        
        player_choice = parts[1].lower()
        if player_choice not in ["камень", "ножницы", "бумага"]:
            send(peer_id, "Выбери: камень, ножницы или бумага")
            return
        
        bot_choice = random.choice(["камень", "ножницы", "бумага"])
        
        if player_choice == bot_choice:
            result = "🤝 Ничья!"
            db.add_season_points(user_id, 1)
        elif (
            (player_choice == "камень" and bot_choice == "ножницы") or
            (player_choice == "ножницы" and bot_choice == "бумага") or
            (player_choice == "бумага" and bot_choice == "камень")
        ):
            result = "🏆 Ты победил! +10 монет"
            player["balance"] += 10
            db.add_season_points(user_id, 2)
        else:
            result = "😔 Бот победил! Попробуй ещё раз"
        
        db.save_player(player)
        send(peer_id, f"🪨 Камень-ножницы-бумага:\n\nТы: {player_choice}\nБот: {bot_choice}\n\n{result}")
        return
    
    if command in ["угадай", "угадай число", "guess"]:
        send(peer_id, "🎲 Угадай число от 1 до 10!\n\nНапиши: угадай <число>")
        return
    
    if command.startswith("угадай ") or command.startswith("guess "):
        parts = command.split()
        if len(parts) < 2:
            send(peer_id, "Формат: угадай <число от 1 до 10>")
            return
        
        try:
            guess = int(parts[1])
        except ValueError:
            send(peer_id, "Число должно быть от 1 до 10")
            return
        
        if guess < 1 or guess > 10:
            send(peer_id, "Число должно быть от 1 до 10")
            return
        
        secret = random.randint(1, 10)
        
        if guess == secret:
            reward = 50
            player["balance"] += reward
            db.save_player(player)
            db.add_season_points(user_id, 5)
            send(peer_id, f"🎉 Угадал! Загаданное число: {secret}\nНаграда: +{reward} монет!")
        else:
            send(peer_id, f"😔 Не угадал! Загаданное число: {secret}\nТвоё число: {guess}\nПопробуй ещё раз: угадай <число>")
        return
    
    if command in ["лотерея", "lottery"]:
        last_lottery = player.get("last_lottery", "")
        today = datetime.date.today().isoformat()
        
        if last_lottery == today:
            send(peer_id, "🎫 Ты уже покупал лотерейный билет сегодня!\nПриходи завтра.")
            return
        
        ticket_price = 100
        if player["balance"] < ticket_price:
            send(peer_id, f"🎫 Билет стоит {ticket_price} монет.\nУ тебя недостаточно монет.")
            return
        
        player["balance"] -= ticket_price
        player["last_lottery"] = today
        
        if random.random() < 0.3:
            prize = random.randint(200, 500)
            player["balance"] += prize
            db.save_player(player)
            send(peer_id, f"🎉 ПОБЕДА В ЛОТЕРЕЕ!\n\nТы выиграл {prize} монет!\nЧистая прибыль: {prize - ticket_price} монет")
        else:
            db.save_player(player)
            send(peer_id, f"😔 Не повезло в лотерее...\n\nПопробуй завтра!")
        return
    
    # === УПРАВЛЕНИЕ УВЕДОМЛЕНИЯМИ ===
    if command in ["напоминания", "notifications", "уведомления"]:
        settings = db.get_notification_settings(user_id)
        if not settings:
            send(peer_id, "❌ Не удалось получить настройки.")
            return
        
        lines = ["🔔 Настройки уведомлений:\n"]
        for notif_type, name in db.NOTIFICATION_TYPES.items():
            status = "✅ ВКЛ" if settings.get(notif_type, False) else "❌ ВЫКЛ"
            lines.append(f"{status} {name}")
        
        lines.append("\nУправление:")
        lines.append("  включить <тип> — включить уведомление")
        lines.append("  выключить <тип> — выключить уведомление")
        lines.append("\nТипы: bonus, quests, boss, inactivity")
        send(peer_id, "\n".join(lines))
        return
    
    if command.startswith("включить "):
        parts = command.split()
        if len(parts) < 2:
            send(peer_id, "Формат: включить <тип>")
            return
        
        notif_type = parts[1].lower()
        if notif_type not in db.NOTIFICATION_TYPES:
            send(peer_id, f"Неизвестный тип. Доступные: {', '.join(db.NOTIFICATION_TYPES.keys())}")
            return
        
        db.set_notification_setting(user_id, notif_type, True)
        send(peer_id, f"✅ Уведомление '{db.NOTIFICATION_TYPES[notif_type]}' включено!")
        return
    
    if command.startswith("выключить "):
        parts = command.split()
        if len(parts) < 2:
            send(peer_id, "Формат: выключить <тип>")
            return
        
        notif_type = parts[1].lower()
        if notif_type not in db.NOTIFICATION_TYPES:
            send(peer_id, f"Неизвестный тип. Доступные: {', '.join(db.NOTIFICATION_TYPES.keys())}")
            return
        
        db.set_notification_setting(user_id, notif_type, False)
        send(peer_id, f"❌ Уведомление '{db.NOTIFICATION_TYPES[notif_type]}' выключено!")
        return
    
    # === КЛАНЫ ===
    if command in ["клан", "clan"]:
        clan = db.get_clan(user_id)
        if not clan:
            send(peer_id, "🏰 Ты не состоишь в клане.\n\n"
                         "Создать: клан создать <название> (5000 монет)\n"
                         "Вступить: клан вступить <ID клана>\n"
                         "Список кланов: кланы")
            return
        
        members = db.get_clan_members(clan["id"])
        member_count = len(members)
        
        send(peer_id, f"🏰 {clan['name']}\n\n"
                     f"👑 Лидер: {clan['leader_name']}\n"
                     f"⭐ Уровень: {clan['level']}\n"
                     f"📊 Опыт: {clan['exp']}/{clan['level'] * 100}\n"
                     f"💰 Казна: {clan['coins']} монет\n"
                     f"👥 Участников: {member_count}\n"
                     f"⚔️ Победы: {clan['wins']} | Поражения: {clan['losses']}\n\n"
                     f"Твоя роль: {clan['role']}\n\n"
                     f"Команды:\n"
                     f"  клан info — информация\n"
                     f"  клан участники — список участников\n"
                     f"  клан пригласить <id> — пригласить игрока\n"
                     f"  клан кикнуть <id> — кикнуть участника\n"
                     f"  клан выйти — выйти из клана\n"
                     f"  клан распустить — распустить клан (лидер)\n"
                     f"  кланы — все кланы")
        return
    
    if command.startswith("клан создать ") or command.startswith("clan create "):
        clan = db.get_clan(user_id)
        if clan:
            send(peer_id, "Ты уже состоишь в клане!")
            return
        
        if player["balance"] < 5000:
            send(peer_id, "Недостаточно монет! Создание клана стоит 5000 монет.")
            return
        
        name = text.split(" ", 2)[-1].strip()
        if len(name) < 3 or len(name) > 30:
            send(peer_id, "Название клана должно быть от 3 до 30 символов.")
            return
        
        clan_id = db.create_clan(name, user_id)
        if not clan_id:
            send(peer_id, "Клан с таким названием уже существует!")
            return
        
        player["balance"] -= 5000
        db.save_player(player)
        send(peer_id, f"🎉 Клан '{name}' создан!\n"
                     f"ID клана: {clan_id}\n"
                     f"Стоимость: 5000 монет")
        return
    
    if command in ["кланы", "clans"]:
        clans = db.get_all_clans()
        if not clans:
            send(peer_id, "Пока нет кланов. Будь первым!")
            return
        
        lines = ["🏰 Все кланы:\n"]
        for i, c in enumerate(clans[:10], start=1):
            lines.append(f"{i}. {c['name']} (ур. {c['level']}) — {c['member_count']} уч., лидер: {c['leader_name']}")
        
        send(peer_id, "\n".join(lines))
        return
    
    if command.startswith("клан вступить ") or command.startswith("clan join "):
        clan = db.get_clan(user_id)
        if clan:
            send(peer_id, "Ты уже состоишь в клане!")
            return
        
        try:
            clan_id = int(command.split()[-1])
        except (ValueError, IndexError):
            send(peer_id, "Формат: клан вступить <ID клана>")
            return
        
        target_clan = db.get_clan_by_id(clan_id)
        if not target_clan:
            send(peer_id, "Клан не найден!")
            return
        
        if db.invite_to_clan(clan_id, user_id, user_id):
            send(peer_id, f"✅ Ты вступил в клан '{target_clan['name']}'!")
            
            # Уведомить лидера
            leader = db.get_player(target_clan["leader_id"], get_name)
            if leader.get("last_peer_id"):
                send(leader["last_peer_id"], 
                     f"🎉 {player['name']} вступил в клан '{target_clan['name']}'!")
        else:
            send(peer_id, "Не удалось вступить в клан.")
        return
    
    if command in ["клан выйти", "clan leave"]:
        clan = db.get_clan(user_id)
        if not clan:
            send(peer_id, "Ты не состоишь в клане!")
            return
        
        if clan["role"] == "leader":
            send(peer_id, "Лидер не может выйти из клана. Распусти клан: клан распустить")
            return
        
        if db.leave_clan(user_id):
            send(peer_id, f"✅ Ты вышел из клана '{clan['name']}'.")
        else:
            send(peer_id, "Не удалось выйти из клана.")
        return
    
    if command.startswith("клан пригласить ") or command.startswith("clan invite "):
        clan = db.get_clan(user_id)
        if not clan:
            send(peer_id, "Ты не состоишь в клане!")
            return
        
        if clan["role"] not in ["leader", "officer"]:
            send(peer_id, "Только лидер и офицеры могут приглашать!")
            return
        
        try:
            target_id = int(command.split()[-1])
        except (ValueError, IndexError):
            send(peer_id, "Формат: клан пригласить <ID игрока>")
            return
        
        if target_id == user_id:
            send(peer_id, "Нельзя пригласить самого себя!")
            return
        
        if db.invite_to_clan(clan["id"], target_id, user_id):
            target = db.get_player(target_id, get_name)
            send(peer_id, f"✅ {target['name']} приглашён в клан!")
            
            # Уведомить игрока
            if target.get("last_peer_id"):
                send(target["last_peer_id"],
                     f" Тебя пригласили в клан '{clan['name']}'!\n"
                     f"Напиши: клан вступить {clan['id']}")
        else:
            send(peer_id, "Игрок уже состоит в клане.")
        return
    
    if command.startswith("клан кикнуть ") or command.startswith("clan kick "):
        clan = db.get_clan(user_id)
        if not clan:
            send(peer_id, "Ты не состоишь в клане!")
            return
        
        if clan["role"] not in ["leader", "officer"]:
            send(peer_id, "Только лидер и офицеры могут кикать!")
            return
        
        try:
            target_id = int(command.split()[-1])
        except (ValueError, IndexError):
            send(peer_id, "Формат: клан кикнуть <ID игрока>")
            return
        
        if db.kick_from_clan(clan["id"], target_id, user_id):
            target = db.get_player(target_id, get_name)
            send(peer_id, f"✅ {target['name']} кикнут из клана!")
            
            # Уведомить игрока
            if target.get("last_peer_id"):
                send(target["last_peer_id"],
                     f"😔 Вас кикнули из клана '{clan['name']}'.")
        else:
            send(peer_id, "Не удалось кикнуть игрока.")
        return
    
    if command in ["клан распустить", "clan disband"]:
        clan = db.get_clan(user_id)
        if not clan:
            send(peer_id, "Ты не состоишь в клане!")
            return
        
        if clan["role"] != "leader":
            send(peer_id, "Только лидер может распустить клан!")
            return
        
        if db.disband_clan(clan["id"], user_id):
            send(peer_id, f"🗑️ Клан '{clan['name']}' распущен!")
        else:
            send(peer_id, "Не удалось распустить клан.")
        return
    
    if command in ["клан участники", "clan members"]:
        clan = db.get_clan(user_id)
        if not clan:
            send(peer_id, "Ты не состоишь в клане!")
            return
        
        members = db.get_clan_members(clan["id"])
        lines = [f"👥 Участники клана '{clan['name']}':\n"]
        
        role_emoji = {"leader": "👑", "officer": "⭐", "member": "•"}
        for m in members:
            emoji = role_emoji.get(m["role"], "•")
            lines.append(f"{emoji} {m['name']} (ур. {m['level']}, {m['balance']}💰)")
        
        send(peer_id, "\n".join(lines))
        return

    # === АДМИН-КОМАНДЫ ===
    if not is_admin(user_id):
        return
    
    if command in ["админ", "admin"]:
        send(peer_id, " Админ-панель:\n\n"
                     "📊 Статистика:\n"
                     "  статистика\n\n"
                     "👥 Игроки:\n"
                     "  игроки\n"
                     "  выдать <id> <сумма>\n"
                     "  бан <id>\n"
                     "  разбан <id>\n\n"
                     "🏆 Сезоны:\n"
                     "  сбросить сезон\n\n"
                     " Босс:\n"
                     "  сбросить босса\n\n"
                     "📢 Рассылка:\n"
                     "  рассылка <текст>")
        return
    
    if command in ["статистика", "stats"]:
        stats = db.get_stats()
        send(peer_id, f"📊 Статистика бота:\n\n"
                     f"👥 Всего игроков: {stats['total_players']}\n"
                     f"💰 Всего монет: {stats['total_coins']}\n"
                     f"⭐ Средний уровень: {stats['avg_level']}\n"
                     f"⚔️ Всего дуэлей выиграно: {stats['total_duels']}\n"
                     f"👹 Всего боссов убито: {stats['total_boss_kills']}")
        return
    
    if command in ["игроки", "players"]:
        all_players = db.get_all_players()
        if not all_players:
            send(peer_id, "Нет игроков.")
            return
        
        lines = [f"👥 Игроки ({len(all_players)}):\n"]
        for i, p in enumerate(all_players[:20], start=1):
            banned = " 🚫" if p["balance"] == -1 else ""
            lines.append(f"{i}. {p['name']}{banned} — ур. {p['level']}, {p['balance']}💰, {p['season_points']}🏆")
        
        if len(all_players) > 20:
            lines.append(f"\n... и ещё {len(all_players) - 20}")
        
        send(peer_id, "\n".join(lines))
        return
    
    if command.startswith("выдать "):
        parts = command.split()
        if len(parts) < 3:
            send(peer_id, "Формат: выдать <id> <сумма>")
            return
        
        try:
            target_id = int(parts[1])
            amount = int(parts[2])
        except ValueError:
            send(peer_id, "ID и сумма должны быть числами")
            return
        
        if amount <= 0:
            send(peer_id, "Сумма должна быть положительной")
            return
        
        if db.add_coins_to_player(target_id, amount):
            target = db.get_player(target_id, get_name)
            send(peer_id, f"✅ Выдано {amount} монет игроку {target['name']}")
            if target.get("last_peer_id"):
                send(target["last_peer_id"], f"🎁 Админ выдал вам {amount} монет!")
        else:
            send(peer_id, "Игрок не найден")
        return
    
    if command.startswith("бан "):
        parts = command.split()
        if len(parts) < 2:
            send(peer_id, "Формат: бан <id>")
            return
        
        try:
            target_id = int(parts[1])
        except ValueError:
            send(peer_id, "ID должен быть числом")
            return
        
        if db.ban_player(target_id):
            target = db.get_player(target_id, get_name)
            send(peer_id, f"🚫 {target['name']} забанен!")
            if target.get("last_peer_id"):
                send(target["last_peer_id"], "🚫 Вы были забанены администратором!")
        else:
            send(peer_id, "Игрок не найден")
        return
    
    if command.startswith("разбан "):
        parts = command.split()
        if len(parts) < 2:
            send(peer_id, "Формат: разбан <id>")
            return
        
        try:
            target_id = int(parts[1])
        except ValueError:
            send(peer_id, "ID должен быть числом")
            return
        
        if db.unban_player(target_id):
            target = db.get_player(target_id, get_name)
            send(peer_id, f"✅ {target['name']} разбанен!")
            if target.get("last_peer_id"):
                send(target["last_peer_id"], "✅ Вас разбанили! Добро пожаловать обратно!")
        else:
            send(peer_id, "Игрок не найден или не забанен")
        return
    
    if command in ["сбросить сезон", "reset season"]:
        count = db.force_reset_season()
        send(peer_id, f"✅ Сезон сброшен! Награды выданы {count} игрокам.")
        return
    
    if command in ["сбросить босса", "reset boss"]:
        db.clear_boss()
        send(peer_id, "✅ Босс сброшен!")
        return
    
    if command.startswith("рассылка "):
        message = text[len("рассылка "):].strip()
        if not message:
            send(peer_id, "Формат: рассылка <текст сообщения>")
            return
        
        all_players = db.get_all_peer_ids()
        sent_count = 0
        for p in all_players:
            try:
                send(p["last_peer_id"], f"📢 Важное сообщение от админа:\n\n{message}")
                sent_count += 1
            except Exception as e:
                print(f"Не удалось отправить {p['user_id']}: {e}")
        
        send(peer_id, f"✅ Рассылка отправлена {sent_count} игрокам!")
        return

    # Неизвестная команда — молчим
    return