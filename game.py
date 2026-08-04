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

ITEM_EMOJI = {1: "🧪", 2: "⚔️", 3: "⚔️", 4: "🛡️", 5: "🛡️", 6: "👑", 7: "💎", 8: "🧪"}

BOSS_LEVELS = {
    1: {"name": "Гоблин-воин", "hp": 200, "attack": 15, "defense": 5, "reward": 100, "exp": 10},
    2: {"name": "Огр-разбойник", "hp": 400, "attack": 25, "defense": 10, "reward": 200, "exp": 20},
    3: {"name": "Тёмный рыцарь", "hp": 800, "attack": 35, "defense": 15, "reward": 400, "exp": 40},
    4: {"name": "Дракон", "hp": 1500, "attack": 50, "defense": 20, "reward": 800, "exp": 80},
    5: {"name": "Древний демон", "hp": 3000, "attack": 70, "defense": 30, "reward": 1500, "exp": 150},
}

def get_name(user_id):
    try:
        users = api.users.get(user_ids=user_id)
        if users:
            full_name = f"{users[0].get('first_name', '')} {users[0].get('last_name', '')}".strip()
            if full_name: return full_name
    except Exception: pass
    return f"ID{user_id}"

def send(peer_id, text):
    try:
        api.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())
    except Exception as e:
        print(f"Ошибка отправки в {peer_id}: {e}")

def add_exp(player, amount=1):
    player["exp"] += amount
    leveled_up = False
    while player["exp"] >= player["level"] * 10:
        player["exp"] -= player["level"] * 10
        player["level"] += 1
        leveled_up = True
    return leveled_up

HELP_TEXT = (
    "Игровой бот\n\n"
    "Основные: старт, помощь, баланс, работа, ставка 50, дуэль, бонус, топ, профиль\n"
    "Магазин: магазин, инвентарь, купить <id>, экипировать <id>\n"
    "PvP: вызов @id123, принять, отклонить\n"
    "Босс: босс, атака, статус, сдаться\n"
    "Прогресс: квесты, выполнить квесты, достижения"
)

def show_shop(peer_id):
    lines = ["Магазин предметов\n"]
    for item_id, item in ITEMS.items():
        lines.append(f"{item_id}. {ITEM_EMOJI.get(item_id, '📦')} {item['name']} — {item['price']} монет\n   {item['desc']}\n")
    lines.append("Чтобы купить: купить <номер>")
    send(peer_id, "\n".join(lines))

def buy_item(player, peer_id, item_id_str):
    try: item_id = int(item_id_str)
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
    send(peer_id, f"Куплено: {ITEM_EMOJI.get(item_id, '📦')} {item['name']} за {item['price']} монет!")

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
    try: item_id = int(item_id_str)
    except ValueError:
        send(peer_id, "Укажи номер числом")
        return
    inventory = db.get_inventory(player["user_id"])
    if item_id not in inventory or inventory[item_id] <= 0:
        send(peer_id, "У тебя нет этого предмета!")
        return
    if item_id not in ITEMS: return
    item = ITEMS[item_id]
    if item["type"] == "consumable":
        db.remove_from_inventory(player["user_id"], item_id, 1)
        send(peer_id, f"Использовано: {ITEM_EMOJI.get(item_id, '')} {item['name']}\n{item['desc']}")
    elif item["type"] in ["weapon", "armor", "cosmetic"]:
        equipped = db.get_equipment(player["user_id"])
        old = equipped.get(item["type"])
        db.set_equipment(player["user_id"], item["type"], item_id)
        msg = f"Надето: {ITEM_EMOJI.get(item_id, '')} {item['name']}"
        if old and old in ITEMS: msg += f"\n(предыдущее {ITEMS[old]['name']} снято)"
        send(peer_id, msg)

def show_top(peer_id):
    ranked = db.get_top_players(10)
    if not ranked:
        send(peer_id, "Пока нет игроков.")
        return
    medals = ["1 место", "2 место", "3 место"]
    lines = ["Топ игроков:\n"]
    for i, p in enumerate(ranked, start=1):
        lines.append(f"{medals[i-1] if i <= 3 else f'{i}.'} {p['name']} — ур. {p['level']}, {p['balance']} монет")
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
    player["balance"] += reward
    add_exp(player, 1)
    db.save_player(player)
    send(peer_id, f"Ежедневный бонус: +{reward} монет!\nСерия: {player['bonus_streak']} дн.")

def get_player_damage(player):
    base = random.randint(12, 25)
    eq = db.get_equipment(player["user_id"])
    if eq.get("weapon") and eq["weapon"] in ITEMS:
        base += ITEMS[eq["weapon"]]["effect"].get("damage", 0)
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
        hp2 -= d1; hp1 -= d2
        log.append(f"Раунд {r}: ты {d1}, бот {d2}")
        if hp1 <= 0 or hp2 <= 0: break
    
    if hp2 <= 0 and hp1 > 0:
        reward = random.randint(30, 70)
        player["balance"] += reward
        add_exp(player, 3)
        db.save_player(player)
        db.update_daily_progress(player["user_id"], "duels", 1)
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
    if not challenge: return
    db.delete_duel(challenged_id)
    send(challenged_peer_id, "Вы отклонили вызов.")
    send(challenge["challenger_peer_id"], f"{db.get_player(challenged_id, get_name)['name']} отклонил вызов.")

def play_pvp_duel(p1, p2, peer1, peer2):
    hp1, hp2, log = 100, 100, []
    for r in range(1, 8):
        if hp1 <= 0 or hp2 <= 0: break
        d1, d2 = get_player_damage(p1), get_player_damage(p2)
        def1, def2 = get_player_defense(p1), get_player_defense(p2)
        ad1, ad2 = max(3, d1 - def2), max(3, d2 - def1)
        hp2 -= ad1; hp1 -= ad2
        log.append(f"Раунд {r}: {p1['name']} -{ad1}, {p2['name']} -{ad2}")
    
    if hp1 > 0 and hp2 <= 0:
        reward = random.randint(50, 100)
        p1["balance"] += reward
        add_exp(p1, 5); add_exp(p2, 2)
        db.save_player(p1); db.save_player(p2)
        db.update_daily_progress(p1["user_id"], "duels", 1)
        achs = db.check_achievements_on_action(p1["user_id"], p1, "duel_win")
        res = f"🏆 Победил {p1['name']}! +{reward} монет." + ("\n🏆 Достижение: " + ", ".join(achs) if achs else "")
    elif hp2 > 0 and hp1 <= 0:
        reward = random.randint(50, 100)
        p2["balance"] += reward
        add_exp(p2, 5); add_exp(p1, 2)
        db.save_player(p1); db.save_player(p2)
        db.update_daily_progress(p2["user_id"], "duels", 1)
        achs = db.check_achievements_on_action(p2["user_id"], p2, "duel_win")
        res = f"🏆 Победил {p2['name']}! +{reward} монет." + ("\n🏆 Достижение: " + ", ".join(achs) if achs else "")
    else:
        add_exp(p1, 2); add_exp(p2, 2)
        db.save_player(p1); db.save_player(p2)
        res = "Ничья."
    
    msg = f"⚔️ PvP дуэль:\n" + "\n".join(log[-5:]) + f"\n\n{res}"
    send(peer1, msg)
    if peer2 != peer1: send(peer2, msg)

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
    msgs = [f"👹 {boss['name']} повержен!\n\nНаграды:"]
    for p in boss["participants"]:
        share = p["damage"] / total_dmg if total_dmg > 0 else 1 / len(boss["participants"])
        reward = int(BOSS_LEVELS[boss["level"]]["reward"] * share)
        exp = int(BOSS_LEVELS[boss["level"]]["exp"] * share)
        pl = db.get_player(p["player_id"], get_name)
        pl["balance"] += reward
        add_exp(pl, exp)
        db.save_player(pl)
        db.update_daily_progress(p["player_id"], "boss", 1)
        achs = db.check_achievements_on_action(p["player_id"], pl, "boss_kill")
        ach_msg = " 🏆 " + ", ".join(achs) if achs else ""
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
    if not boss or not boss.get("active"): return
    boss["participants"] = [p for p in boss.get("participants", []) if p["player_id"] != user_id]
    db.save_boss(boss)
    send(peer_id, "Ты покинул бой.")


# ==================== ОБРАБОТЧИК ====================
def handle(user_id, peer_id, text):
    player = db.get_player(user_id, get_name)
    player["last_peer_id"] = peer_id
    db.save_player(player)
    player = db.check_and_reset_daily_quests(player)
    command = text.lower().strip()
    if not command: return

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
        player["balance"] += earned
        player["last_work"] = now
        add_exp(player, 2)
        db.save_player(player)
        db.update_daily_progress(user_id, "coins", earned)
        db.check_achievements_on_action(user_id, player, "rich")
        send(peer_id, f"Ты заработал {earned} монет.")
        return
    if command.startswith("ставка "):
        parts = command.split()
        if len(parts) != 2: return
        try: amount = int(parts[1])
        except ValueError: return
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
        send(peer_id, f"Профиль\n\nИмя: {player['name']}\nУровень: {player['level']}\nОпыт: {player['exp']}\nБаланс: {player['balance']}\nСерия бонусов: {player.get('bonus_streak', 0)} дн.{cos}")
        return
    if command in ["магазин", "shop"]:
        show_shop(peer_id)
        return
    if command in ["инвентарь", "inv"]:
        show_inventory(player, peer_id)
        return
    if command.startswith("купить "):
        buy_item(player, peer_id, command.split()[1])
        return
    if command.startswith("экипировать ") or command.startswith("использовать "):
        use_item(player, peer_id, command.split()[1])
        return
    if command.startswith("вызов ") or command.startswith("pvp "):
        opp = parse_user_id_from_mention(text)
        if opp: challenge_player(user_id, opp, peer_id)
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
    
    # === НОВЫЕ КОМАНДЫ: КВЕСТЫ И ДОСТИЖЕНИЯ ===
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

    # Неизвестная команда — молчим
    return